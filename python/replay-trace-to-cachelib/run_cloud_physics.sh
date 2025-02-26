#!/bin/bash

set -e
# Base URL for downloading datasets
base_url="https://ftp.pdl.cmu.edu/pub/datasets/twemcacheWorkload/cacheDatasets/cloudphysics"

# Path to the reader executable
reader_executable="/users/Hongshu/thesis-playground/C++/cacheTraceReader/executable/reader"

# Loop through w01 to w106
for i in $(seq 1 106); do
    dataset=$(printf "w%02d.oracleGeneral.bin.zst" $i)
    csv_file=$(printf "w%02d.csv" $i)

    # Step 1: Download dataset
    wget -q "${base_url}/${dataset}"
    if [ ! -f "${dataset}" ]; then
        echo "Failed to download ${dataset}"
        exit 1
    fi

    # Step 2: Convert dataset to CSV format
    ${reader_executable} ${dataset} ${csv_file}
    if [ ! -f "${csv_file}" ]; then
        echo "Failed to create ${csv_file}"
        exit 1
    fi  

    # Step 3: Count the number of lines in the CSV file (minus 1 for the header)
    record_count=$(($(wc -l < ${csv_file}) - 1))

    # Step 4: Run the Python script with the updated JSON configuration
    export TRACE_FILE=$(realpath ${csv_file})
    export RECORD_COUNT=${record_count}
    python3 /users/Hongshu/thesis-playground/python/replay-trace-to-cachelib/run.py

    # Step 5: Delete the dataset and CSV file
    rm ${dataset} ${csv_file}
done