#!/bin/bash

# Function to convert JSON to CSV
json_to_csv() {
    local json_file=$1
    local trace_name=$2
    local csv_file=$3

    # Extract JSON fields and convert to CSV format
    jq -r --arg trace_name "$trace_name" '
        [
            $trace_name,
            .number_of_requests,
            .number_of_objects,
            .number_of_req_GiB,
            .number_of_obj_GiB,
            .compulsory_miss_ratio_req,
            .compulsory_miss_ratio_byte,
            .frequency_mean,
            .time_span,
            .zipf_slope,
            .zipf_intercept,
            .zipf_r2
        ] | @csv' "$json_file" >> "$csv_file"
}

# Main script
if [ $# -lt 2 ]; then
    echo "Usage: $0 <output_csv_file> <json_files_directory>"
    exit 1
fi

output_csv=$1
json_dir=$2

# Write CSV header
echo "trace_name,number_of_requests,number_of_objects,number_of_req_GiB,number_of_obj_GiB,compulsory_miss_ratio_req,compulsory_miss_ratio_byte,frequency_mean,time_span,zipf_slope,zipf_intercept,zipf_r2" > "$output_csv"

# Process each JSON file in the directory
for json_file in "$json_dir"/synth*.json; do
    trace_name=$(basename "$json_file" .json)
    json_to_csv "$json_file" "$trace_name" "$output_csv"
done


echo "CSV file generated: $output_csv"