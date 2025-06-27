#!/bin/bash

# Function to parse metrics from a text file (new format)
parse_metrics() {
    local file=$1
    local json_file=$2

    local num_requests=$(grep "^number of requests:" "$file" | awk -F': ' '{print $2}' | xargs)
    local min_req_size=$(grep "^min req size:" "$file" | awk -F': ' '{print $2}' | xargs)
    local max_req_size=$(grep "^max req size:" "$file" | awk -F': ' '{print $2}' | xargs)
    local qps=$(grep "^qps:" "$file" | awk -F': ' '{print $2}' | xargs)
    local num_objects=$(grep "^number of objects:" "$file" | awk -F': ' '{print $2}' | xargs)
    local num_req_gib=$(grep "^number of req GiB:" "$file" | awk -F': ' '{print $2}' | xargs)
    local num_obj_gib=$(grep "^number of obj GiB:" "$file" | awk -F': ' '{print $2}' | xargs)
    local comp_miss_ratio_line=$(grep "^compulsory miss ratio (req/byte):" "$file" | awk -F': ' '{print $2}' | xargs)
    local comp_miss_ratio_req=$(echo "$comp_miss_ratio_line" | awk -F'/' '{print $1}' | xargs)
    local comp_miss_ratio_byte=$(echo "$comp_miss_ratio_line" | awk -F'/' '{print $2}' | xargs)
    local time_span=$(grep "^time span:" "$file" | awk -F'[:(]' '{print $2}' | xargs)
    local freq_mean=$(grep "^frequency mean:" "$file" | awk -F': ' '{print $2}' | xargs)

    # Create JSON object
    local json=$(cat <<EOF
{
    "number_of_requests": $num_requests,
    "min_req_size": $min_req_size,
    "max_req_size": $max_req_size,
    "qps": $qps,
    "number_of_objects": $num_objects,
    "number_of_req_GiB": $num_req_gib,
    "number_of_obj_GiB": $num_obj_gib,
    "compulsory_miss_ratio_req": $comp_miss_ratio_req,
    "compulsory_miss_ratio_byte": $comp_miss_ratio_byte,
    "time_span": $time_span,
    "frequency_mean": $freq_mean
}
EOF
)

    # Write JSON to file
    echo "$json" > "$json_file"
}

# Main script
if [ $# -lt 2 ]; then
    echo "Usage: $0 <input_text_file> <output_json_file>"
    exit 1
fi

input_file=$1
output_file=$2

parse_metrics "$input_file" "$output_file"