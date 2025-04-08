import csv
import os
import bisect
import numpy as np
import pandas as pd
import bisect
from collections import defaultdict


def compute_reuse_distances(reference_sequence):
    """
    Computes reuse distances for each element in the sequence and returns a histogram.
    
    Args:
        reference_sequence (list): Sequence of data accesses (e.g., ['A', 'B', 'A']).
    
    Returns:
        tuple: (list of reuse distances, histogram as a dict).
    """
    last_access_time = {}  # Hash table (H): maps elements to last access time
    access_times_tree = []  # Binary search tree (T): maintains sorted access times
    hist = defaultdict(int) # Histogram of reuse distances

    for current_time, element in enumerate(reference_sequence):
        reuse_distance = -1  # Default: no prior access (∞)
        
        if element in last_access_time:
            last_time = last_access_time[element]
            # Find the number of accesses after `last_time` (reuse distance)
            idx = bisect.bisect_right(access_times_tree, last_time)
            reuse_distance = len(access_times_tree) - idx
            # Remove the old access time from the tree
            del access_times_tree[bisect.bisect_left(access_times_tree, last_time)]

        hist[reuse_distance] += 1
        
        # Update tree and hash table
        bisect.insort(access_times_tree, current_time)
        last_access_time[element] = current_time
    
    return dict(hist)

def calculate_miss_ratios(input_files, output_dir, output_file="miss_ratios.csv"):
    """
    Calculate miss ratios for all subtrace files in a directory under different memory sizes.

    Args:
        directory (str): Path to the directory containing subtrace files.
        output_file (str): Name of the output CSV file to store miss ratios (default: "miss_ratios.csv").
    """
    # Define memory size range (4MB to 4GB in steps of 4MB)
    memory_sizes = np.arange(4 * 1024 * 1024, 4 * 1024 * 1024 * 1025, 4 * 1024 * 1024)  # 4MB to 4GB

    # Prepare the output CSV file
    output_path = os.path.join(output_dir, output_file)
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['subtrace_name', 'cache_size', 'slab_cnt', 'miss_count', 'miss_ratio', 'miss_ratio_delta'])  # Header row

        # Scan the directory for subtrace files
        for trace_name, info in input_files.items():
            object_ids = pd.read_csv(info['path'], usecols=['object_id'])['object_id'].tolist()
            object_size = info['object_size']

            reuse_distance_histogram = compute_reuse_distances(object_ids)
            total_records = sum(reuse_distance_histogram.values())

            last_miss_ratio = 1

            for memory_size in memory_sizes:
                slab_cnt = memory_size // (4 * 1024 * 1024)  # Number of 4MB slabs
                max_objects = memory_size // object_size  # Maximum objects that can fit in the cache

                # Calculate miss count by filtering the histogram
                miss_count = sum(count for reuse_distance, count in reuse_distance_histogram.items() if (reuse_distance >= max_objects or reuse_distance == -1))
                miss_ratio = miss_count / total_records
                miss_ratio_delta = last_miss_ratio - miss_ratio

                # Write the result to the output CSV
                writer.writerow([trace_name, memory_size, slab_cnt, miss_count, miss_ratio, miss_ratio_delta])

                # Update the last miss ratio
                last_miss_ratio = miss_ratio


if __name__ == "__main__":
    input_files = {
        'alpha=1;size=512': {'object_size': 512, 'path': '/users/Hongshu/traces/synth_zipf_100_512.csv'},
        'alpha=1;size=1024': {'object_size': 1024, 'path': '/users/Hongshu/traces/synth_zipf_100_1024.csv'},
        'alpha=0.5;size=512': {'object_size': 512, 'path': '/users/Hongshu/traces/synth_zipf_050_512.csv'},
        'alpha=0.5;size=1024': {'object_size': 1024, 'path': '/users/Hongshu/traces/synth_zipf_050_1024.csv'},
    }
    output_dir = '/proj/latencymodel-PG0/hongshu/traces/subtraces/single_size_zipfs'
    os.makedirs(output_dir, exist_ok=True)
    
    calculate_miss_ratios(input_files, output_dir)
