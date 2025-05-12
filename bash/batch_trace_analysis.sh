#!/bin/bash

# Base URLs and directories
base_url="https://ftp.pdl.cmu.edu/pub/datasets/twemcacheWorkload/cacheDatasets/twitter/sample"
trace_dir="/users/Hongshu/traces"
outcome_dir="/users/Hongshu/thesis-playground/bash/outcome"
parse_script="/users/Hongshu/thesis-playground/bash/parse_trace_analysis.sh"
analyzer="/users/Hongshu/libCacheSim/_build/bin/traceAnalyzer"
heatmap_script="/users/Hongshu/libCacheSim/scripts/traceAnalysis/size_heatmap.py"

process_cluster() {
    i=$1
    cluster="cluster$i"
    filename="${cluster}.oracleGeneral.sample10.zst"
    filepath="${trace_dir}/${filename}"
    analysis_txt="${trace_dir}/analysis/${filename}_analysis.txt"
    analysis_json="${trace_dir}/analysis/${filename}_analysis.json"

    echo "Processing $filename"

    # Download trace
    wget -q "${base_url}/${filename}" -P "${trace_dir}"

    # Run traceAnalyzer
    cd "${outcome_dir}" || exit
    "${analyzer}" "${filepath}" oracleGeneralBin --common >> "${analysis_txt}"

    # Parse analysis
    /bin/bash "${parse_script}" "${analysis_txt}" "${analysis_json}"

    # Generate heatmap
    cd /users/Hongshu/thesis-playground/bash/ || exit
    python3 "${heatmap_script}" "outcome/${filename}.sizeWindow_w300_req"

    # Remove downloaded trace file
    rm -f "${filepath}"
}

export -f process_cluster
export base_url trace_dir outcome_dir parse_script analyzer heatmap_script

# Run with 2 jobs in parallel
parallel -j 2 process_cluster ::: {7..54}
