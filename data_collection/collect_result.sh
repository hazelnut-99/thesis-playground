#!/bin/bash

# Define the base directory
base_dir="work_dir_3/outcome"

# Output CSV file
output_csv="$base_dir/report_raw.csv"

# Write the header to the CSV file
echo -e "directory,_numCacheGet,_numCacheGetMisses,_allocFailures,_allocSuccessRate,_numRebalancedSlabs,_getPerSec,_poolUsedFrac,_ramEvictions,_rebalanceNumRuns,_rebalanceAvgTimeMs" > $output_csv

# Function to process each directory
process_dir() {
    dir=$1
    if [[ -f "$dir/config.json" && -f "$dir/exp_config.json" && -f "$dir/std.out" ]]; then
        # Extract directory name
        directory=$(basename "$dir")

        # Extract values from std.out
        numCacheGet=$(grep -m 1 "Num Cache Gets  :" "$dir/std.out" | awk -F': ' '{print $2}' | tr -d ',')
        numCacheGetMisses=$(grep -m 1 "Num Cache Gets Misses  :" "$dir/std.out" | awk -F': ' '{print $2}' | tr -d ',')
        allocSuccessRate=$(grep -m 1 "Alloc Attempts" "$dir/std.out" | awk -F'Success: ' '{print $2}' | tr -d '%' | tr -d ' ' | tr -d ',')
        allocFailures=$(grep -m 1 "Allocation Failures  :" "$dir/std.out" | awk -F': ' '{print $2}' | tr -d ' ' | tr -d ',')
        rebalanceNumRebalancedSlabs=$(grep -m 1 "Rebalance Num Rebalanced Slabs" "$dir/std.out" | awk -F': ' '{print $2}' | tr -d ' ' | tr -d ',')
        getPerSec=$(grep -m 1 "get       :" "$dir/std.out" | awk -F': ' '{print $2}' | awk '{print $1}' | tr -d ',' | tr -d '/s')
        poolUsedFrac=$(grep -m 1 "Fraction of pool 0 used :" "$dir/std.out" | awk -F': ' '{print $2}' | tr -d ' ' | tr -d ',')
        ramEvictions=$(grep -m 1 "RAM Evictions :" "$dir/std.out" | awk -F': ' '{print $2}' | tr -d ' ' | tr -d ',')
        rebalanceNumRuns=$(grep -m 1 "Rebalance Num Runs  :" "$dir/std.out" | awk -F': ' '{print $2}' | tr -d ' ' | tr -d ',')
        rebalanceAvgTimeMs=$(grep -m 1 "Rebalance Avg Rebalance TimeMs  :" "$dir/std.out" | awk -F': ' '{print $2}' | tr -d ' ' | tr -d ',')


        # Write the values to the CSV file
        echo -e "$directory,$numCacheGet,$numCacheGetMisses,$allocFailures,$allocSuccessRate,$rebalanceNumRebalancedSlabs,$getPerSec,$poolUsedFrac,$ramEvictions,$rebalanceNumRuns,$rebalanceAvgTimeMs" >> $output_csv
    fi
}

export -f process_dir
export output_csv

# Use GNU Parallel to process directories in parallel
find "$base_dir"/*/ -maxdepth 0 -type d | parallel process_dir

echo "Report generated: $output_csv"