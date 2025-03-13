#!/bin/bash

# Directory containing the trace files
trace_dir="/users/Hongshu/traces"
analysis_dir="/users/Hongshu/traces/analysis"

# Create the analysis directory if it doesn't exist
mkdir -p "$analysis_dir"

# Loop through all files with names starting with synth_ under the trace directory
for csv_file in "$trace_dir"/synth_periodic*.csv; do
    # Extract the base name of the file (without the directory and extension)
    base_name=$(basename "$csv_file" .csv)
    analysis_txt="$analysis_dir/${base_name}_analysis.txt"
    analysis_json="$analysis_dir/${base_name}_analysis.json"

    # Generate analysis
    /users/Hongshu/libCacheSim/_build/bin/traceAnalyzer "$csv_file" csv --common --trace-type-params=time-col=1,obj-id-col=2,obj-size-col=3,obj-id-is-num=1,delimiter=, >> "$analysis_txt"

    # Parse analysis
    /bin/bash /users/Hongshu/thesis-playground/bash/parse_trace_analysis.sh "$analysis_txt" "$analysis_json"
done

echo "Analysis completed for all synth_*.csv files."