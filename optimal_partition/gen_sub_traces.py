import csv
import os
import bisect
import json
import sys
import numpy as np
from collections import Counter
from multiprocessing import Pool
from scipy.stats import linregress
import pandas as pd
import bisect
from collections import defaultdict
from calc_optimal import calc_optimal_allocation
import subprocess
import re


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


def process_csv_and_generate_subtraces(csv_file_path, output_dir, factor=None, max_size=None, min_size=None, alignment=8, alloc_sizes=None, chunk_size=sys.maxsize):
    """
    Process a CSV file, optionally in chunks, generate subtrace files for each allocation size, and calculate stack distance.

    Args:
        csv_file_path (str): Path to the input CSV file.
        output_dir (str): Directory where the subtrace files will be written.
        factor (float): Factor for generating allocation sizes.
        max_size (int): Maximum allocation size.
        min_size (int): Minimum allocation size.
        alignment (int): Alignment for allocation sizes (default is 8).
        alloc_sizes (list): Predefined allocation sizes (optional).
        chunk_size (int): Number of rows per chunk. Defaults to sys.maxsize (process entire file at once).
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
    input_file_name = os.path.splitext(os.path.basename(csv_file_path))[0]

    # Process the CSV file in chunks
    chunk_index = 0
    with open(csv_file_path, 'r') as csv_file:
        reader = csv.DictReader(csv_file)
        rows = []
        for row in reader:
            rows.append(row)
            if len(rows) >= chunk_size:
                # Process the current chunk
                chunk_dir = os.path.join(output_dir, f"chunk_{chunk_index}")
                os.makedirs(chunk_dir, exist_ok=True)
                process_chunk(rows, chunk_dir, input_file_name, alloc_sizes)
                rows = []
                chunk_index += 1

        # Process the remaining rows (if any)
        if rows:
            chunk_dir = os.path.join(output_dir, f"chunk_{chunk_index}")
            os.makedirs(chunk_dir, exist_ok=True)
            process_chunk(rows, chunk_dir, input_file_name, alloc_sizes)


def process_chunk(rows, chunk_dir, input_file_name, alloc_sizes):
    """
    Process a single chunk of rows and generate subtrace files.

    Args:
        rows (list): List of rows in the chunk.
        chunk_dir (str): Directory where the subtrace files will be written.
        input_file_name (str): Base name of the input file.
        alloc_sizes (list): List of allocation sizes.
    """
    # Open a file for each allocation size and write the header row
    alloc_size_files = {
        size: open(os.path.join(chunk_dir, f"{input_file_name}_subtrace_{size}.csv"), 'w', newline='')
        for size in alloc_sizes
    }
    alloc_size_writers = {size: csv.writer(file) for size, file in alloc_size_files.items()}
    for writer in alloc_size_writers.values():
        writer.writerow(['object_id'])  # Add header row

    try:
        # Process each row in the chunk
        for row in rows:
            object_id = row['object_id']
            object_size = int(row['object_size'])
            object_size = max(24, object_size)
            # key size and meta-data overhead
            object_size += (32 + len(str(object_id)))

            # Find the smallest alloc_size >= object_size using binary search
            index = bisect.bisect_left(alloc_sizes, object_size)
            if index < len(alloc_sizes):
                alloc_size = alloc_sizes[index]
                alloc_size_writers[alloc_size].writerow([object_id])
    finally:
        # Close all opened files
        for file in alloc_size_files.values():
            file.close()

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



def get_subtrace_statistics(directory, output_file="subtrace_stat.csv"):
    """
    Count the number of records, distinct object IDs, and perform Zipf linear fitting for each subtrace file.

    Args:
        directory (str): Path to the directory containing subtrace files.
        output_file (str): Name of the output CSV file to store record counts and Zipf fitting results (default: "record_counts.csv").
    """
    # Prepare the output CSV file
    output_path = os.path.join(directory, output_file)
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['subtrace_name', 'record_count', 'distinct_object_count', 'zipf_slope', 'zipf_intercept', 'zipf_r2', 'zipf_p_value'])  # Header row

        # Scan the directory for subtrace files
        for filename in os.listdir(directory):
            if "_subtrace_" in filename and filename.endswith(".csv"):
                subtrace_path = os.path.join(directory, filename)

                # Read the subtrace file
                with open(subtrace_path, 'r') as subtrace_file:
                    reader = csv.DictReader(subtrace_file)
                    object_ids = [row['object_id'] for row in reader]
                
                record_count, distinct_object_count, slope, intercept, zipf_r2, p_value = subtrace_statistics_helper(object_ids)
                
                writer.writerow([filename, record_count, distinct_object_count, slope, intercept, zipf_r2, p_value])


def calculate_miss_ratios(directory, output_file="miss_ratios.csv"):
    """
    Calculate miss ratios for all subtrace files in a directory under different memory sizes.

    Args:
        directory (str): Path to the directory containing subtrace files.
        output_file (str): Name of the output CSV file to store miss ratios (default: "miss_ratios.csv").
    """
    # Define memory size range (4MB to 4GB in steps of 4MB)
    memory_sizes = np.arange(4 * 1024 * 1024, 4 * 1024 * 1024 * 1025, 4 * 1024 * 1024)  # 4MB to 4GB

    # Prepare the output CSV file
    output_path = os.path.join(directory, output_file)
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['subtrace_name', 'cache_size', 'slab_cnt', 'miss_count', 'miss_ratio', 'miss_ratio_delta'])  # Header row

        # Scan the directory for subtrace files
        for filename in os.listdir(directory):
            if "_subtrace_" in filename and filename.endswith(".csv"):
                subtrace_path = os.path.join(directory, filename)

                # Extract object size from the filename
                try:
                    object_size = int(filename.split("_subtrace_")[-1].split(".csv")[0])
                except ValueError:
                    print(f"Skipping file {filename}: Unable to extract object size.")
                    continue

                # Read the subtrace file and load all object_ids into memory
                with open(subtrace_path, 'r') as subtrace_file:
                    reader = csv.reader(subtrace_file)
                    header = next(reader)
                    if header != ['object_id']:
                        print(f"Skipping file {filename}: Invalid header {header}. Expected ['object_id'].")
                        continue
                    object_ids = [row[0] for row in reader]

                # Compute reuse distance histogram
                reuse_distance_histogram = compute_reuse_distances(object_ids)

                # Total number of records in the subtrace
                total_records = sum(reuse_distance_histogram.values())
                if total_records == 0:
                    print(f"Skipping file {filename}: No records found.")
                    continue

                # Initialize the last miss ratio to 1
                last_miss_ratio = 1

                # Calculate miss ratios for each memory size
                for memory_size in memory_sizes:
                    slab_cnt = memory_size // (4 * 1024 * 1024)  # Number of 4MB slabs
                    max_objects = memory_size // object_size  # Maximum objects that can fit in the cache

                    # Calculate miss count by filtering the histogram
                    miss_count = sum(count for reuse_distance, count in reuse_distance_histogram.items() if (reuse_distance >= max_objects or reuse_distance == -1))
                    miss_ratio = miss_count / total_records
                    miss_ratio_delta = last_miss_ratio - miss_ratio

                    # Write the result to the output CSV
                    writer.writerow([filename, memory_size, slab_cnt, miss_count, miss_ratio, miss_ratio_delta])

                    # Update the last miss ratio
                    last_miss_ratio = miss_ratio


def clean_up_subtrace_files(directory):
    """
    Deletes all subtrace files in the specified directory.

    Args:
        directory (str): Path to the directory containing subtrace files.
    """
    if not os.path.isdir(directory):
        raise ValueError(f"The provided path '{directory}' is not a valid directory.")

    for filename in os.listdir(directory):
        if "_subtrace_" in filename and filename.endswith(".csv"):
            file_path = os.path.join(directory, filename)
            try:
                os.remove(file_path)
                print(f"Deleted: {file_path}")
            except Exception as e:
                print(f"Error deleting file {file_path}: {e}")


def simulate_miss_ratio(trace_path: str, cache_size_mb: int) -> float:
    command = [
        "/users/Hongshu/libCacheSim/_build/bin/cachesim",
        trace_path,
        "csv",
        "lru",
        f"{cache_size_mb}mb",
        "-t",
        "time-col=1,obj-id-col=2,obj-size-col=3,obj-id-is-num=1"
    ]
    
    try:
        # Run the command and capture output
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        output = result.stdout + result.stderr  # cachesim might output to stderr
        
        # Find the final line with the total miss ratio
        match = re.search(r"miss ratio ([0-9.]+)", output)
        if match:
            return float(match.group(1))
        else:
            raise ValueError("Miss ratio not found in output.")
    except subprocess.CalledProcessError as e:
        print("Error running cachesim:", e.stderr)
        raise


def simulate_lru_cache_miss_ratios(csv_file_path, total_slabs, directory, output_file="global_lru_miss_ratios.csv"):
    cache_sizes = [s * 4 for s in total_slabs]
    output_path = os.path.join(directory, output_file)
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['trace_path', 'cache_size', 'slab_cnt',  'miss_ratio'])

        for index, cache_size in enumerate(cache_sizes):
            miss_ratio = simulate_miss_ratio(csv_file_path, cache_size)
            writer.writerow([csv_file_path, cache_size, total_slabs[index], miss_ratio])
        


# Example usage
if __name__ == "__main__":
    trace_names = [f"synth_thesis_static_{str(i)}" for i in range(100, 105)]
    for trace_name in trace_names:
        csv_file_path = f"/mydata/hongshu/traces/thesis/{trace_name}.csv"
        output_dir = f'/mydata/hongshu/traces/thesis/subtraces/{trace_name}'
        subtrace_files = process_csv_and_generate_subtraces(
            csv_file_path=csv_file_path,
            output_dir=output_dir,
            alloc_sizes=[2048, 4096]
        )

        for chunk_dir in os.listdir(output_dir):
            chunk_path = os.path.join(output_dir, chunk_dir)
            if os.path.isdir(chunk_path) and chunk_dir.startswith("chunk_"):
                print(f"Processing {chunk_path}...")
                # Perform post-processing steps for each chunk
                calculate_miss_ratios(chunk_path)
                get_subtrace_statistics(chunk_path)
                clean_up_subtrace_files(chunk_path)
    
    
    
    # csv_file_path = "/proj/latencymodel-PG0/hongshu/traces/meta2024_50m.csv"
    # for alloc_factor in [1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0]:
    #     output_dir = f'/proj/latencymodel-PG0/hongshu/traces/subtraces/meta2024_50m_{alloc_factor}'
    #     subtrace_files = process_csv_and_generate_subtraces(
    #         csv_file_path=csv_file_path,
    #         output_dir=output_dir,
    #         factor=alloc_factor,
    #         max_size=523352,
    #         min_size=72,
    #         # alloc_sizes=[256, 512, 1024, 2048, 4096],
    #         #chunk_size=40_000_000
    #     )
        
    #     for chunk_dir in os.listdir(output_dir):
    #         chunk_path = os.path.join(output_dir, chunk_dir)
    #         if os.path.isdir(chunk_path) and chunk_dir.startswith("chunk_"):
    #             print(f"Processing {chunk_path}...")

    #             # Perform post-processing steps for each chunk
    #             calculate_miss_ratios(chunk_path)
    #             get_subtrace_statistics(chunk_path)
    #             clean_up_subtrace_files(chunk_path)
    
        # simulate_lru_cache_miss_ratios(csv_file_path,
        #     total_slabs=[64, 128, 256, 512, 1024],
        #     directory=output_dir,
        #     output_file="global_lru_miss_ratios.csv"
        # )
    
    