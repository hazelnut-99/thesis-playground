#!/bin/bash

# Loop through synth_1.csv to synth_5.csv
for i in {1..5}; do
    dataname="synth_${i}.csv"
    python3 /users/Hongshu/libCacheSim/scripts/traceAnalysis/size_heatmap.py "${dataname}.sizeWindow_w300"
done