#!/bin/bash

input_csv="output.csv"
output_csv="output_with_wss.csv"

# Read the input CSV file and add the new column
# add key size and cachelib metadata overhead
awk -F',' 'BEGIN {OFS=","} 
NR==1 {print $0, "wss"} 
NR>1 {wss = ($4 * 1024) + ($3 * 52) / (1024 * 1024); print $0, wss}' "$input_csv" > "$output_csv"

echo "Updated CSV file generated: $output_csv"