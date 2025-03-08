#!/bin/bash

# Function to parse metrics from a text file
parse_metrics() {
    local file=$1
    local json_file=$2

    # Extract metrics using grep and awk
    local num_requests=$(grep "number of requests:" "$file" | awk -F'[:,]' '{print $2}' | xargs)
    local num_objects=$(grep "number of requests:" "$file" | awk -F'[:,]' '{print $4}' | xargs)
    local num_req_gib=$(grep "number of req GiB:" "$file" | awk -F'[:,]' '{print $2}' | xargs)
    local num_obj_gib=$(grep "number of req GiB:" "$file" | awk -F'[:,]' '{print $4}' | xargs)
    local comp_miss_ratio_req=$(grep "compulsory miss ratio (req/byte):" "$file" | awk -F'[:,/]' '{print $3}' | xargs)
    local comp_miss_ratio_byte=$(grep "compulsory miss ratio (req/byte):" "$file" | awk -F'[:,/]' '{print $4}' | xargs)
    local freq_mean=$(grep "frequency mean:" "$file" | awk -F': ' '{print $2}' | xargs)
    local time_span=$(grep "time span:" "$file" | awk -F'[()]' '{print $1}' | awk -F': ' '{print $2}' | xargs)
    local zipf_slope=$(grep "popularity: Zipf linear fitting slope=" "$file" | awk -F'[=,]' '{print $2}' | xargs)
    local zipf_intercept=$(grep "popularity: Zipf linear fitting slope=" "$file" | awk -F'[=,]' '{print $4}' | xargs)
    local zipf_r2=$(grep "popularity: Zipf linear fitting slope=" "$file" | awk -F'R2=' '{print $2}' | xargs)

    # Create JSON object
    local json=$(cat <<EOF
{
    "number_of_requests": $num_requests,
    "number_of_objects": $num_objects,
    "number_of_req_GiB": $num_req_gib,
    "number_of_obj_GiB": $num_obj_gib,
    "compulsory_miss_ratio_req": $comp_miss_ratio_req,
    "compulsory_miss_ratio_byte": $comp_miss_ratio_byte,
    "frequency_mean": $freq_mean,
    "time_span": $time_span,
    "zipf_slope": $zipf_slope,
    "zipf_intercept": $zipf_intercept,
    "zipf_r2": $zipf_r2
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