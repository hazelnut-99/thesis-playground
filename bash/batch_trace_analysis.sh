#!/bin/bash

# Base URLs and directories
base_url="https://ftp.pdl.cmu.edu/pub/datasets/twemcacheWorkload/cacheDatasets/twitter/"
trace_dir="/mydata/hongshu/traces"
outcome_dir="/mydata/hongshu/thesis-playground/bash/outcome"
parse_script="/mydata/hongshu/thesis-playground/bash/parse_trace_analysis.sh"
analyzer="/mydata/hongshu/libCacheSim/_build/bin/traceAnalyzer"
heatmap_script="/mydata/hongshu/libCacheSim/scripts/traceAnalysis/size_heatmap.py"
minmax_executable="/mydata/hongshu/thesis-playground/C++/cacheTraceReader/executable/reader"

process_cluster() {
    i=$1
    cluster="cluster$i"
    filename="${cluster}.oracleGeneral.zst"
    filepath="${trace_dir}/${filename}"
    analysis_txt="${trace_dir}/analysis/${filename}_analysis.txt"
    analysis_json="${trace_dir}/analysis/${filename}_analysis.json"

    echo "Processing $filename"

    # Download trace
    wget -q "${base_url}/${filename}" -P "${trace_dir}"

    # Check file size (in bytes) and skip processing if larger than 25GB
    if [[ -f "$filepath" ]]; then
        file_size=$(stat --format="%s" "$filepath")
        if (( file_size > 20 * 1024 * 1024 * 1024 )); then
            echo "File $filename is larger than 25GB. Skipping processing and deleting the file."
            rm -f "$filepath"
            return
        fi
    fi

    # Run traceAnalyzer
    cd "${outcome_dir}" || exit
    "${analyzer}" "${filepath}" oracleGeneralBin --common > "${analysis_txt}"

    # Parse analysis to JSON
    /bin/bash "${parse_script}" "${analysis_txt}" "${analysis_json}"

    # Extract Min/Max object size
    minmax_output=$("${minmax_executable}" "${filepath}" print_min_max_size)

    min_obj_size=$(echo "$minmax_output" | grep "Min Object Size:" | awk '{print $4}')
    max_obj_size=$(echo "$minmax_output" | grep "Max Object Size:" | awk '{print $4}')

    # Add min/max sizes to JSON file
    if [[ -n "$min_obj_size" && -n "$max_obj_size" ]]; then
        tmp_json=$(mktemp)
        jq --arg min "$min_obj_size" --arg max "$max_obj_size" \
           '. + {min_obj_size: ($min | tonumber), max_obj_size: ($max | tonumber)}' \
           "$analysis_json" > "$tmp_json" && mv "$tmp_json" "$analysis_json"
    fi

    # Generate heatmap
    cd /mydata/hongshu/thesis-playground/bash/ || exit
    python3 "${heatmap_script}" "outcome/${filename}.sizeWindow_w300_req"

    # Remove downloaded trace file
    rm -f "${filepath}"
}

export -f process_cluster
export base_url trace_dir outcome_dir parse_script analyzer heatmap_script minmax_executable

# Run with 2 jobs in parallel
parallel -j 4 process_cluster ::: {39..54}