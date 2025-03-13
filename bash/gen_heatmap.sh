#!/bin/bash

trace_dir="/users/Hongshu/traces"
for csv_file in "$trace_dir"/synth_peri*.csv; do
    base_name=$(basename "$csv_file" .csv)
    python3 /users/Hongshu/libCacheSim/scripts/traceAnalysis/size_heatmap.py "outcome/${base_name}.csv.sizeWindow_w300"
done



