#!/bin/bash

# Script to merge CSV trace files and extract specific fields
# Usage: ./process_csv_meta_traces.sh <input_directory> <output_file>

# Check if correct number of arguments provided
if [ $# -ne 2 ]; then
    echo "Usage: $0 <input_directory> <output_file>"
    echo "Example: $0 /nfs/hongshu/traces/08_07_2024-Intel merged_traces.csv"
    exit 1
fi

INPUT_DIR="$1"
OUTPUT_FILE="$2"
TEMP_FILE="/tmp/temp_merged_traces.csv"
KEY_MAP_FILE="/tmp/key_mapping.txt"

# Check if input directory exists
if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: Directory $INPUT_DIR does not exist"
    exit 1
fi

echo "Processing CSV files in directory: $INPUT_DIR"
echo "Output file: $OUTPUT_FILE"

# Remove temporary files if they exist
rm -f "$TEMP_FILE" "$KEY_MAP_FILE"

# Find all CSV files and process them
csv_files=$(find "$INPUT_DIR" -name "*.csv" -type f | sort)

if [ -z "$csv_files" ]; then
    echo "Error: No CSV files found in $INPUT_DIR"
    exit 1
fi

echo "Found CSV files:"
echo "$csv_files"

# Process each CSV file
echo "First pass: Creating key mapping..."
key_counter=1

# First pass: collect all unique keys and create mapping
for csv_file in $csv_files; do
    echo "Scanning keys in: $csv_file"
    # Extract unique keys from column 2, skip header
    tail -n +2 "$csv_file" | cut -d',' -f2 | sort -u | while read -r key; do
        if [ ! -z "$key" ]; then
            echo "$key"
        fi
    done
done | sort -u | nl -nln | sed 's/\t/,/' > "$KEY_MAP_FILE"

echo "Key mapping created with $(wc -l < "$KEY_MAP_FILE") unique keys"

echo "Loading key mapping into memory..."
# Load key mapping into associative array
declare -A key_to_id
while IFS=',' read -r id key; do
    key_to_id["$key"]="$id"
done < "$KEY_MAP_FILE"

echo "Second pass: Processing files with key mapping..."

# Process each CSV file using the key mapping
for csv_file in $csv_files; do
    echo "Processing: $csv_file"
    
    # Skip header and process each line
    tail -n +2 "$csv_file" | while IFS=',' read -r op_time key key_size op op_count size cache_hits ttl usecase sub_usecase; do
        # Look up the integer ID for this key from associative array
        key_id="${key_to_id[$key]}"
        if [ ! -z "$key_id" ]; then
            echo "$op_time,$key_id,$size"
        fi
    done >> "$TEMP_FILE"
done

echo "Sorting merged data by op_time..."

# Sort by op_time (first column, numeric sort) and add header
{
    echo "clock_time,obj_id,obj_size"
    sort -t',' -k1,1n "$TEMP_FILE"
} > "$OUTPUT_FILE"

# Clean up temporary files
rm -f "$TEMP_FILE" "$KEY_MAP_FILE"

# Display statistics
total_lines=$(wc -l < "$OUTPUT_FILE")
data_lines=$((total_lines - 1))
unique_keys=$(tail -n +2 "$OUTPUT_FILE" | cut -d',' -f2 | sort -u | wc -l)

echo "Processing complete!"
echo "Output file: $OUTPUT_FILE"
echo "Total records: $data_lines"
echo "Unique keys mapped: $unique_keys"
echo "First few lines:"
head -n 6 "$OUTPUT_FILE"