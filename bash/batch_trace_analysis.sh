#!/bin/bash

# Fixed base URL
base_url="https://ftp.pdl.cmu.edu/pub/datasets/twemcacheWorkload/cacheDatasets/"
subdirs=("tencentPhoto" "metaCDN" "wiki")  # Add more as needed

trace_dir="/nfs/hongshu/traces"
outcome_dir="/nfs/hongshu/thesis-playground/bash/outcome_new"
parse_script="/nfs/hongshu/thesis-playground/bash/parse_trace_analysis.sh"
analyzer="/nfs/hongshu/libCacheSim/_build/bin/traceAnalyzer"
heatmap_script="/nfs/hongshu/libCacheSim/scripts/traceAnalysis/size_heatmap.py"
minmax_executable="/nfs/hongshu/thesis-playground/C++/cacheTraceReader/executable/reader"

process_trace() {
    ulimit -v $((248 * 1024 * 1024))
    filename="$1"
    subdir="$2"
    filepath="${trace_dir}/${filename}"
    analysis_txt="${trace_dir}/analysis_txt/${filename}_analysis.txt"
    analysis_json="${trace_dir}/analysis_json/${filename}_analysis.json"

    echo "Processing $filename in $subdir"

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
export base_url trace_dir outcome_dir parse_script analyzer heatmap_script minmax_executable

# for subdir in "${subdirs[@]}"; do
#     echo "Processing subdir: $subdir"
#     file_list=$(curl -s "${base_url}${subdir}/" | grep -oP '(?<=href=")[^"]+\.oracleGeneral(\.bin)?\.zst(?=")' | sort | uniq)
#     echo "$file_list" | parallel -j 1 process_trace {} "$subdir"
# done

for subdir in "${subdirs[@]}"; do
    echo "Processing subdir: $subdir"
    file_list=$(curl -s "${base_url}${subdir}/" | grep -oP '(?<=href=")[^"]+\.oracleGeneral(\.bin)?\.zst(?=")' | sort | uniq)
    while read -r filename; do
        [[ -z "$filename" ]] && continue
        process_trace "$filename" "$subdir"
    done <<< "$file_list"
done