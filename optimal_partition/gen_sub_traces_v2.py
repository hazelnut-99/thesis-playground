import csv
import os
import bisect
import json
import numpy as np
from collections import Counter
from multiprocessing import Pool
from scipy.stats import linregress
import pandas as pd
import bisect
from collections import defaultdict
from calc_optimal import calc_optimal_allocation
from zstandard import ZstdDecompressor


def get_aligned_size(size, alignment):
    return (size + alignment - 1) // alignment * alignment


def generate_alloc_sizes(factor, max_size, min_size, alignment=8):
    if max_size > 4 * 1024 * 1024:
        raise ValueError(f"maximum alloc size {max_size} is more than the slab size {1024 * 1024}")

    if factor <= 1.0:
        raise ValueError(f"invalid factor {factor}")

    alloc_sizes = set()
    size = min_size

    while size < max_size:
        n_per_slab = 4 * 1024 * 1024 // size  # Assuming Slab::kSize is 1MB
        if n_per_slab <= 1:
            break
        alloc_sizes.add(size)
        prev_size = size
        size = get_aligned_size(int(size * factor), alignment)
        if prev_size == size:
            raise ValueError(f"invalid incFactor {factor}")

    alloc_sizes.add(get_aligned_size(max_size, alignment))
    return alloc_sizes


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


def generate_one_subtrace(binary_file_path, name, output_dir, alloc_sizes, alloc_size):
    """
    Generate a subtrace file for a specific allocation size from a Zstandard-compressed binary file.

    Args:
        binary_file_path (str): Path to the input binary file.
        output_dir (str): Directory where the subtrace file will be written.
        alloc_size (int): Allocation size for the subtrace.
        alloc_sizes (list): List of all allocation sizes (sorted).

    Returns:
        str: Path to the generated subtrace file.
    """
    # Create the output file path
    output_file_path = os.path.join(output_dir, f"{name}_subtrace_{alloc_size}.csv")

    object_ids = []

    # Open the binary file and decompress it
    with open(binary_file_path, 'rb') as binary_file:
        decompressor = ZstdDecompressor()
        with decompressor.stream_reader(binary_file) as reader:
            while True:
                # Read a single record (24 bytes per record)
                record = reader.read(24)
                if len(record) < 24:
                    break  # End of file

                # Parse the binary record
                clock_time = int.from_bytes(record[0:4], byteorder='little', signed=False)
                obj_id = int.from_bytes(record[4:12], byteorder='little', signed=False)
                obj_size = int.from_bytes(record[12:16], byteorder='little', signed=False)
                next_access_vtime = int.from_bytes(record[16:24], byteorder='little', signed=True)

                # Adjust object size with metadata overhead
                obj_size = max(24, obj_size)
                obj_size += (32 + len(str(obj_id)))

                # Find the smallest allocation size that can fit the object
                index = bisect.bisect_left(alloc_sizes, obj_size)
                if index < len(alloc_sizes) and alloc_size == alloc_sizes[index]:
                    object_ids.append(obj_id)

    return output_file_path, object_ids



def subtrace_statistics_helper(object_ids):
    # Total number of records in the subtrace
    record_count = len(object_ids)

    # Count distinct object IDs
    distinct_object_count = len(set(object_ids))

    # Perform Zipf linear fitting
    if distinct_object_count > 0:
        # Use NumPy to calculate frequencies
        object_ids_array = np.array(object_ids)
        _, frequencies = np.unique(object_ids_array, return_counts=True)

        # Sort frequencies in descending order
        frequencies = np.sort(frequencies)[::-1]

        # Generate ranks
        ranks = np.arange(1, len(frequencies) + 1)

        # Perform linear regression on log-log scale
        log_ranks = np.log(ranks)
        log_frequencies = np.log(frequencies)
        slope, intercept, r_value, p_value, stderr = linregress(log_ranks, log_frequencies)
        zipf_r2 = r_value**2
    else:
        # If no distinct objects, set Zipf fitting values to None
        slope, intercept, zipf_r2, p_value = None, None, None, None
    
    return record_count, distinct_object_count, slope, intercept, zipf_r2, p_value



def process_binary_and_generate_subtraces(binary_file_path, output_dir, factor, max_size, min_size, name, alignment=8, alloc_sizes=None):
    """
    Process a CSV file, generate subtrace files for each allocation size, calculate statistics and miss ratios, and clean up subtrace files.

    Args:
        csv_file_path (str): Path to the input CSV file.
        output_dir (str): Directory where the subtrace files will be written.
        factor (float): Factor for generating allocation sizes.
        max_size (int): Maximum allocation size.
        min_size (int): Minimum allocation size.
        alignment (int): Alignment for allocation sizes (default is 8).
        alloc_sizes (list): Predefined allocation sizes (optional).
    """
    # Generate allocation sizes using the provided function if not provided
    if alloc_sizes is None:
        alloc_sizes = sorted(generate_alloc_sizes(factor, max_size, min_size, alignment))

    # Write alloc_sizes to a JSON file in the output directory
    os.makedirs(output_dir, exist_ok=True)
    alloc_sizes_json_path = os.path.join(output_dir, "alloc_size.json")
    with open(alloc_sizes_json_path, 'w') as json_file:
        json.dump(alloc_sizes, json_file, indent=4)
        
    # Extract the base name of the input file (without extension)
    subtrace_stat_output_path = os.path.join(output_dir, "subtrace_stat.csv")
    miss_ratio_output_path = os.path.join(output_dir, "miss_ratios.csv")
    
    with open(subtrace_stat_output_path, 'w', newline='') as stat_file,\
         open(miss_ratio_output_path, 'w', newline='') as miss_ratio_file:

        # Prepare the CSV writers
        stat_writer = csv.writer(stat_file)
        miss_ratio_writer = csv.writer(miss_ratio_file)

        # Write headers to the output files
        stat_writer.writerow(['subtrace_name', 'record_count', 'distinct_object_count', 'zipf_slope', 'zipf_intercept', 'zipf_r2', 'p_value'])
        miss_ratio_writer.writerow(['subtrace_name', 'cache_size', 'slab_cnt', 'miss_count', 'miss_ratio', 'miss_ratio_delta'])

        # Process each allocation size
        for alloc_size in alloc_sizes:
            print(f"Processing allocation size: {alloc_size}")

            # Generate subtrace for the current allocation size
            subtrace_path, object_ids = generate_one_subtrace(binary_file_path, name, output_dir, alloc_sizes, alloc_size)
            record_count, distinct_object_count, slope, intercept, zipf_r2, p_value = subtrace_statistics_helper(object_ids)
            stat_writer.writerow([os.path.basename(subtrace_path), record_count, distinct_object_count, slope, intercept, zipf_r2, p_value])
            
            # Compute reuse distance histogram
            reuse_distance_histogram = compute_reuse_distances(object_ids)

            # Total number of records in the subtrace
            total_records = record_count

            # Initialize the last miss ratio to 1
            last_miss_ratio = 1

            # Define memory size range (4MB to 4GB in steps of 4MB)
            memory_sizes = np.arange(4 * 1024 * 1024, 4 * 1024 * 1024 * 1025, 4 * 1024 * 1024)  # 4MB to 4GB

            # Calculate miss ratios for each memory size
            for memory_size in memory_sizes:
                slab_cnt = memory_size // (4 * 1024 * 1024)  # Number of 4MB slabs
                max_objects = memory_size // alloc_size  # Maximum objects that can fit in the cache

                # Calculate miss count by filtering the histogram
                miss_count = sum(count for reuse_distance, count in reuse_distance_histogram.items() if (reuse_distance >= max_objects or reuse_distance == -1))
                miss_ratio = miss_count / total_records
                miss_ratio_delta = last_miss_ratio - miss_ratio

                # Write the result to the miss ratios file
                miss_ratio_writer.writerow([os.path.basename(subtrace_path), memory_size, slab_cnt, miss_count, miss_ratio, miss_ratio_delta])

                # Update the last miss ratio
                last_miss_ratio = miss_ratio

        
        
# Example usage
if __name__ == "__main__":
    
    configs = [
        # {
        #     "input_path": "/proj/latencymodel-PG0/hongshu/traces/cluster52.oracleGeneral.sample10.zst",
        #     "output_dir": "/proj/latencymodel-PG0/hongshu/traces/subtraces/cluster52_sample10",
        #     "maxsize": 6300,
        #     "name": "cluster52_sample10"
        # },
        # {
        #     "input_path": "/proj/latencymodel-PG0/hongshu/traces/202210_kv_traces_all_sort.csv.oracleGeneral.zst",
        #     "output_dir": "/proj/latencymodel-PG0/hongshu/traces/subtraces/meta_2022",
        #     "maxsize": 523350,
        #     "name": "meta_2022"
        # },
        {
            "input_path": "/proj/latencymodel-PG0/hongshu/traces/202401_kv_traces_all_sort.csv.oracleGeneral.zst",
            "output_dir": "/proj/latencymodel-PG0/hongshu/traces/subtraces/meta_2024",
            "maxsize": 523350,
            "name": "meta_2024"
        }
    ]
    
    for config in configs:
    
        subtrace_files = process_binary_and_generate_subtraces(
            binary_file_path=config['input_path'],
            output_dir=config['output_dir'],
            factor=1.5,
            max_size=config['maxsize'],
            min_size=72,
            name=config['name'],
            # factor=None,
            # max_size=None,
            # min_size=None,
            # alloc_sizes=[256, 512, 1024, 2048, 4096]
        )
    
    