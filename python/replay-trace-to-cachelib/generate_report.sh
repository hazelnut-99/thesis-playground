#!/bin/bash

# Output CSV file
output_csv="outcome/report.csv"

# Write the header to the CSV file
echo "cacheSizeMB,rebalanceStrategy,allocator,numCacheGet,numCacheGetMisses,allocSuccessRate,rebalanceNumRebalancedSlabs,getPerSec,setPerSec" > $output_csv

# Iterate over each subdirectory in the outcome directory
for dir in outcome/*/; do
    # Check if the directory contains config.json and std.out files
    if [[ -f "$dir/config.json" && -f "$dir/std.out" ]]; then
        # Extract values from config.json
        cacheSizeMB=$(jq -r '.cache_config.cacheSizeMB' "$dir/config.json")
        rebalanceStrategy=$(jq -r '.cache_config.rebalanceStrategy' "$dir/config.json")
        allocator=$(jq -r '.cache_config.allocator' "$dir/config.json")

        # Extract values from std.out
        numCacheGet=$(grep -m 1 "Num Cache Gets  :" "$dir/std.out" | awk -F': ' '{print $2}' | tr -d ',')
        numCacheGetMisses=$(grep -m 1 "Num Cache Gets Misses  :" "$dir/std.out" | awk -F': ' '{print $2}' | tr -d ',')
        allocSuccessRate=$(grep -m 1 "Alloc Attempts" "$dir/std.out" | awk -F'Success: ' '{print $2}' | tr -d '%' | tr -d ' ')
        rebalanceNumRebalancedSlabs=$(grep -m 1 "Rebalance Num Rebalanced Slabs" "$dir/std.out" | awk -F': ' '{print $2}' | tr -d ' ')
        getPerSec=$(grep -m 1 "get       :" "$dir/std.out" | awk -F': ' '{print $2}' | awk '{print $1}' | tr -d ',' | tr -d '/s')
        setPerSec=$(grep -m 1 "set       :" "$dir/std.out" | awk -F': ' '{print $2}' | awk '{print $1}' | tr -d ',' | tr -d '/s')

        # Write the values to the CSV file
        echo "$cacheSizeMB,$rebalanceStrategy,$allocator,$numCacheGet,$numCacheGetMisses,$allocSuccessRate,$rebalanceNumRebalancedSlabs,$getPerSec,$setPerSec" >> $output_csv
    fi
done

echo "Report generated: $output_csv"