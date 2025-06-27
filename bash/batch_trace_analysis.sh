#!/bin/bash

# Fixed base URL and configurable subdir
base_url="https://ftp.pdl.cmu.edu/pub/datasets/twemcacheWorkload/cacheDatasets/"
subdir="metaKV"  # Change this to e.g. metaKV, cloudphysics, etc.

trace_dir="/mydata/hongshu/traces"
outcome_dir="/mydata/hongshu/thesis-playground/bash/outcome_new"
parse_script="/mydata/hongshu/thesis-playground/bash/parse_trace_analysis.sh"
analyzer="/mydata/hongshu/libCacheSim/_build/bin/traceAnalyzer"
heatmap_script="/mydata/hongshu/libCacheSim/scripts/traceAnalysis/size_heatmap.py"
minmax_executable="/mydata/hongshu/thesis-playground/C++/cacheTraceReader/executable/reader"

# Get file list from remote subdir (assumes server provides HTML listing)
file_list=$(curl -s "${base_url}${subdir}/" | grep -oP '(?<=href=")[^"]+\.oracleGeneral(\.bin)?\.zst(?=")' | sort | uniq)
echo "$file_list"

process_trace() {
    ulimit -v $((248 * 1024 * 1024))
    filename="$1"
    filepath="${trace_dir}/${filename}"
    analysis_txt="${trace_dir}/analysis_txt/${filename}_analysis.txt"
    analysis_json="${trace_dir}/analysis_json/${filename}_analysis.json"

    echo "Processing $filename"

    if [[ -f "$analysis_json" ]]; then
        echo "Analysis JSON $analysis_json already exists, skipping."
        return
    fi

    cleanup() {
        rm -f "${filepath}"
    }
    trap cleanup EXIT

    if [[ -f "${filepath}" ]]; then
        echo "Trace file ${filepath} already exists, skipping download."
    else
        if ! wget -q "${base_url}${subdir}/${filename}" -P "${trace_dir}"; then
            echo "Error downloading ${filename}" >&2
            return 1
        fi
    fi

    cd "${outcome_dir}" || { echo "Failed to cd to ${outcome_dir}"; return 1; }
    if ! "${analyzer}" "${filepath}" oracleGeneralBin --simple > "${analysis_txt}"; then
        echo "traceAnalyzer failed for ${filename}" >&2
        return 1
    fi

    if ! /bin/bash "${parse_script}" "${analysis_txt}" "${analysis_json}"; then
        echo "parse_script failed for ${analysis_txt}" >&2
        return 1
    fi
}

export -f process_trace
export base_url subdir trace_dir outcome_dir parse_script analyzer heatmap_script minmax_executable

# Process all found files in parallel (adjust -j as needed)
echo "$file_list" | parallel -j 1 process_trace