#!/bin/bash

# Fetch the directory listing
url="https://ftp.pdl.cmu.edu/pub/datasets/twemcacheWorkload/cacheDatasets/twitter/"
html=$(curl -s "$url")

# Extract file names (skip parent directory and directories)
files=$(echo "$html" | grep -oP '(?<=href=")[^"/]+(?=")' | grep -vE '^\.\.?$')

# For each file, get its size using curl -I (HEAD request)
tmpfile=$(mktemp)
for f in $files; do
    size_bytes=$(curl -sI "${url}${f}" | awk '/Content-Length/ {print $2}' | tr -d '\r')
    if [[ -n "$size_bytes" ]]; then
        size_gb=$(awk "BEGIN {printf \"%.3f\", $size_bytes/1024/1024/1024}")
        echo -e "$size_gb\t$f"
    fi
done > "$tmpfile"

# Sort by size (numeric, ascending) and print
sort -n "$tmpfile" | column -t

# Clean up
rm "$tmpfile"