#!/bin/bash

# Loop through synth_1.csv to synth_5.csv
for i in {1..5}; do
    csv_file="/users/Hongshu/traces/synth_${i}.csv"
    analysis_txt="/users/Hongshu/traces/analysis/synth_${i}_analysis.txt"
    analysis_json="/users/Hongshu/traces/analysis/synth_${i}_analysis.json"

    # Generate analysis
    /users/Hongshu/libCacheSim/_build/bin/traceAnalyzer "$csv_file" csv --common --trace-type-params=time-col=1,obj-id-col=2,obj-size-col=3,obj-id-is-num=1,delimiter=, >> "$analysis_txt"

    # Parse analysis
    /bin/bash parse_trace_analysis.sh "$analysis_txt" "$analysis_json"
done