#!/bin/bash

# Directories and script paths
trace_dir="/mydata/hongshu/traces"
outcome_dir="/mydata/hongshu/thesis-playground/bash/outcome"
parse_script="/mydata/hongshu/thesis-playground/bash/parse_trace_analysis.sh"
analyzer="/mydata/hongshu/libCacheSim/_build/bin/traceAnalyzer"
heatmap_script="/mydata/hongshu/libCacheSim/scripts/traceAnalysis/size_heatmap.py"

traces=(
    "synth_dynamic_403.csv"
)

process_trace() {
process_trace() {
    filename="$1"
    filepath="${trace_dir}/${filename}"
    filename_no_ext="${filename%.*}"
    analysis_txt="${trace_dir}/analysis/${filename_no_ext}_analysis.txt"
    analysis_json="${trace_dir}/analysis/${filename_no_ext}_analysis.json"

    echo "Processing $filename"

    # Run traceAnalyzer
    cd "${outcome_dir}" || exit
    "${analyzer}" "${filepath}" csv --common --trace-type-params=time-col=1,obj-id-col=2,obj-size-col=3,obj-id-is-num=1,delimiter=, >> "${analysis_txt}"

    # Parse analysis
    /bin/bash "${parse_script}" "${analysis_txt}" "${analysis_json}"

    # Generate heatmap
    cd /mydata/hongshu/thesis-playground/bash/ || exit
    python3 "${heatmap_script}" "outcome/${filename}.sizeWindow_w300_req"
}

export -f process_trace
export trace_dir outcome_dir parse_script analyzer heatmap_script

# Run in parallel
parallel -j 2 process_trace ::: "${traces[@]}"
