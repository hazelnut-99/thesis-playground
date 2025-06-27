#!/bin/bash

# Directories and script paths
trace_dir="/mydata/hongshu/traces"
outcome_dir="/mydata/hongshu/thesis-playground/bash/outcome"
parse_script="/mydata/hongshu/thesis-playground/bash/parse_trace_analysis.sh"
analyzer="/mydata/hongshu/libCacheSim/_build/bin/traceAnalyzer"
heatmap_script="/mydata/hongshu/libCacheSim/scripts/traceAnalysis/size_heatmap.py"
minmax_executable="/mydata/hongshu/thesis-playground/C++/cacheTraceReader/executable/reader"

traces=(
    "tencent_photo1.oracleGeneral.zst"
    "wiki_2016u.oracleGeneral.zst"
)

process_trace() {
    filename="$1"
    filepath="${trace_dir}/${filename}"
    filename_no_ext="${filename%.*}"
    analysis_txt="${trace_dir}/analysis/${filename_no_ext}_analysis.txt"
    analysis_json="${trace_dir}/analysis/${filename_no_ext}_analysis.json"

    echo "Processing $filename"

    # Run traceAnalyzer
    cd "${outcome_dir}" || exit
    "${analyzer}" "${filepath}" oracleGeneralBin --common >> "${analysis_txt}"

    # Parse analysis
    /bin/bash "${parse_script}" "${analysis_txt}" "${analysis_json}"

    # Extract Min/Max object size
    minmax_output=$("${minmax_executable}" "${filepath}" print_min_max_size)

    min_obj_size=$(echo "$minmax_output" | grep "Min Object Size:" | awk '{print $4}')
    max_obj_size=$(echo "$minmax_output" | grep "Max Object Size:" | awk '{print $4}')
    num_small_records=$(echo "$minmax_output" | grep "Number of small records:" | awk '{print $5}')
    total_records=$(echo "$minmax_output" | grep "Total number of records:" | awk '{print $5}')
    avg_qps=$(echo "$minmax_output" | grep "Average QPS:" | awk '{print $3}')

    # Add all stats to JSON file
    if [[ -n "$min_obj_size" && -n "$max_obj_size" && -n "$num_small_records" && -n "$total_records" && -n "$avg_qps" ]]; then
        tmp_json=$(mktemp)
        jq --arg min "$min_obj_size" \
        --arg max "$max_obj_size" \
        --arg small "$num_small_records" \
        --arg total "$total_records" \
        --arg avgqps "$avg_qps" \
        '. + {
            min_obj_size: ($min | tonumber),
            max_obj_size: ($max | tonumber),
            num_small_records: ($small | tonumber),
            total_records: ($total | tonumber),
            avg_qps: ($avgqps | tonumber)
            }' \
        "$analysis_json" > "$tmp_json" && mv "$tmp_json" "$analysis_json"
    fi

    # Generate heatmap
    cd /mydata/hongshu/thesis-playground/bash/ || exit
    python3 "${heatmap_script}" "outcome/${filename}.sizeWindow_w300_req"
}

export -f process_trace
export trace_dir outcome_dir parse_script analyzer heatmap_script minmax_executable

# Run in parallel
parallel -j 3 process_trace ::: "${traces[@]}"