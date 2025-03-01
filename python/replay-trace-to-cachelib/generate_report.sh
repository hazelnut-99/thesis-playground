#!/bin/bash

# Output CSV file
output_csv="outcome_w06/report.csv"

# Write the header to the CSV file
echo "directory,cacheSizeMB,rebalanceStrategy,poolRebalanceIntervalSec,poolRebalancerFreeAllocThreshold,disablepoolRebalancer,allocFactor,allocator,rebalanceDiffRatio,ltaMinTailAgeDifference,rebalanceMinSlabs,ltaNumSlabsFreeMem,ltaSlabProjectionLength,test_group,hpsMinDiff,hpsNumSlabsFreeMem,hpsMinLruTailAge,hpsMaxLruTailAge,mhMovingAverageParam,mhMaxFreeMemSlabs,fmNumFreeSlabs,fmMaxUnAllocatedSlabs,numCacheGet,numCacheGetMisses,allocSuccessRate,rebalanceNumRebalancedSlabs,getPerSec" > $output_csv

# Function to process each directory
process_dir() {
    dir=$1
    if [[ -f "$dir/config.json" && -f "$dir/std.out" ]]; then
        # Extract directory name
        directory=$(basename "$dir")

        # Extract values from config.json
        cacheSizeMB=$(jq -r '.cache_config.cacheSizeMB // empty' "$dir/config.json")
        rebalanceStrategy=$(jq -r '.cache_config.rebalanceStrategy // empty' "$dir/config.json")
        poolRebalanceIntervalSec=$(jq -r '.cache_config.poolRebalanceIntervalSec // empty' "$dir/config.json")
        poolRebalancerFreeAllocThreshold=$(jq -r '.cache_config.poolRebalancerFreeAllocThreshold // empty' "$dir/config.json")
        disablepoolRebalancer=$(jq -r '.cache_config.disablepoolRebalancer // empty' "$dir/config.json")
        allocFactor=$(jq -r '.cache_config.allocFactor // empty' "$dir/config.json")
        allocator=$(jq -r '.cache_config.allocator // empty' "$dir/config.json")
        rebalanceDiffRatio=$(jq -r '.cache_config.rebalanceDiffRatio // empty' "$dir/config.json")
        ltaMinTailAgeDifference=$(jq -r '.cache_config.ltaMinTailAgeDifference // empty' "$dir/config.json")
        rebalanceMinSlabs=$(jq -r '.cache_config.rebalanceMinSlabs // empty' "$dir/config.json")
        ltaNumSlabsFreeMem=$(jq -r '.cache_config.ltaNumSlabsFreeMem // empty' "$dir/config.json")
        ltaSlabProjectionLength=$(jq -r '.cache_config.ltaSlabProjectionLength // empty' "$dir/config.json")
        test_group=$(jq -r '.cache_config.test_group // empty' "$dir/config.json")
        hpsMinDiff=$(jq -r '.cache_config.hpsMinDiff // empty' "$dir/config.json")
        hpsNumSlabsFreeMem=$(jq -r '.cache_config.hpsNumSlabsFreeMem // empty' "$dir/config.json")
        hpsMinLruTailAge=$(jq -r '.cache_config.hpsMinLruTailAge // empty' "$dir/config.json")
        hpsMaxLruTailAge=$(jq -r '.cache_config.hpsMaxLruTailAge // empty' "$dir/config.json")
        mhMovingAverageParam=$(jq -r '.cache_config.mhMovingAverageParam // empty' "$dir/config.json")
        mhMaxFreeMemSlabs=$(jq -r '.cache_config.mhMaxFreeMemSlabs // empty' "$dir/config.json")
        fmNumFreeSlabs=$(jq -r '.cache_config.fmNumFreeSlabs // empty' "$dir/config.json")
        fmMaxUnAllocatedSlabs=$(jq -r '.cache_config.fmMaxUnAllocatedSlabs // empty' "$dir/config.json")

        # Extract values from std.out
        numCacheGet=$(grep -m 1 "Num Cache Gets  :" "$dir/std.out" | awk -F': ' '{print $2}' | tr -d ',')
        numCacheGetMisses=$(grep -m 1 "Num Cache Gets Misses  :" "$dir/std.out" | awk -F': ' '{print $2}' | tr -d ',')
        allocSuccessRate=$(grep -m 1 "Alloc Attempts" "$dir/std.out" | awk -F'Success: ' '{print $2}' | tr -d '%' | tr -d ' ' | tr -d ',')
        rebalanceNumRebalancedSlabs=$(grep -m 1 "Rebalance Num Rebalanced Slabs" "$dir/std.out" | awk -F': ' '{print $2}' | tr -d ' ' | tr -d ',')
        getPerSec=$(grep -m 1 "get       :" "$dir/std.out" | awk -F': ' '{print $2}' | awk '{print $1}' | tr -d ',' | tr -d '/s')

        # Write the values to the CSV file
        echo "$directory,$cacheSizeMB,$rebalanceStrategy,$poolRebalanceIntervalSec,$poolRebalancerFreeAllocThreshold,$disablepoolRebalancer,$allocFactor,$allocator,$rebalanceDiffRatio,$ltaMinTailAgeDifference,$rebalanceMinSlabs,$ltaNumSlabsFreeMem,$ltaSlabProjectionLength,$test_group,$hpsMinDiff,$hpsNumSlabsFreeMem,$hpsMinLruTailAge,$hpsMaxLruTailAge,$mhMovingAverageParam,$mhMaxFreeMemSlabs,$fmNumFreeSlabs,$fmMaxUnAllocatedSlabs,$numCacheGet,$numCacheGetMisses,$allocSuccessRate,$rebalanceNumRebalancedSlabs,$getPerSec" >> $output_csv
    fi
}

export -f process_dir
export output_csv

# Use GNU Parallel to process directories in parallel
find outcome_w06/*/ -maxdepth 0 -type d | parallel process_dir

echo "Report generated: $output_csv"