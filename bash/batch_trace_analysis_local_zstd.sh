#!/bin/bash

# Local trace files configuration
# Add your local trace files here (full paths)
trace_files=(
    "/nfs/hongshu/traces/memcache_2024_intel.csv.oracleGeneral.zst"
    # Add more trace files as needed
)

trace_dir="/nfs/hongshu/traces"
outcome_dir="/nfs/hongshu/thesis-playground/bash/outcome_new"
parse_script="/nfs/hongshu/thesis-playground/bash/parse_trace_analysis.sh"
analyzer="/nfs/hongshu/libCacheSim/_build/bin/traceAnalyzer"
heatmap_script="/nfs/hongshu/libCacheSim/scripts/traceAnalysis/size_heatmap.py"
minmax_executable="/nfs/hongshu/thesis-playground/C++/cacheTraceReader/executable/reader"

process_trace() {
    ulimit -v $((248 * 1024 * 1024))
    filepath="$1"
    filename=$(basename "$filepath")
    analysis_txt="${trace_dir}/analysis_txt/${filename}_analysis.txt"
    analysis_json="${trace_dir}/analysis_json/${filename}_analysis.json"

    echo "Processing $filename"

    # Check if the trace file exists
    if [[ ! -f "$filepath" ]]; then
        echo "Error: Trace file $filepath does not exist" >&2
        return 1
    fi

    if [[ -f "$analysis_json" ]]; then
        echo "Analysis JSON $analysis_json already exists, skipping."
        return
    fi

    # Create analysis directories if they don't exist
    mkdir -p "${trace_dir}/analysis_txt"
    mkdir -p "${trace_dir}/analysis_json"

    cd "${outcome_dir}" || { echo "Failed to cd to ${outcome_dir}"; return 1; }
    if ! "${analyzer}" "${filepath}" oracleGeneralBin --simple > "${analysis_txt}"; then
        echo "traceAnalyzer failed for ${filename}" >&2
        return 1
    fi

    if ! /bin/bash "${parse_script}" "${analysis_txt}" "${analysis_json}"; then
        echo "parse_script failed for ${analysis_txt}" >&2
        return 1
    fi

    echo "Successfully processed $filename"
}

export -f process_trace
export trace_dir outcome_dir parse_script analyzer heatmap_script minmax_executable

# Process each local trace file
echo "Processing ${#trace_files[@]} local trace files..."

for filepath in "${trace_files[@]}"; do
    [[ -z "$filepath" ]] && continue
    process_trace "$filepath"
done

echo "All trace files processed!"