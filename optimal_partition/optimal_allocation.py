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
from calc_optimal import compute_optimal_allocations
import subprocess
import re
from concurrent.futures import ProcessPoolExecutor
from zstandard import ZstdDecompressor

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


import numpy as np

class ReuseDistanceCalculator:
    def __init__(self):
        self.last_access_time = {}  # Maps elements to last access time
        self.access_times_tree = []  # Sorted list of access times
        self.histogram = defaultdict(int)
        self.current_time = 0

    def feed(self, element):
        """
        Feeds a new access element and updates reuse distance histogram.

        Args:
            element: The accessed element.
        
        Returns:
            int: The reuse distance for this access (-1 for first-time access).
        """
        reuse_distance = -1

        if element in self.last_access_time:
            last_time = self.last_access_time[element]
            idx = bisect.bisect_right(self.access_times_tree, last_time)
            reuse_distance = len(self.access_times_tree) - idx
            # Remove the old access time
            del self.access_times_tree[bisect.bisect_left(self.access_times_tree, last_time)]
        
        self.histogram[reuse_distance] += 1
        
        # Insert the current access time and update last seen time
        bisect.insort(self.access_times_tree, self.current_time)
        self.last_access_time[element] = self.current_time
        self.current_time += 1

        return reuse_distance

    def get_histogram(self):
        """Returns the current histogram of reuse distances."""
        return dict(self.histogram)

    def reset(self):
        """Resets the internal state for reuse with a new sequence."""
        self.__init__()

    def query_mrc(self, object_size, max_slab_cnt):
        reuse_distance_histogram = self.get_histogram()
        memory_sizes = np.arange(4 * 1024 * 1024, 4 * (max_slab_cnt + 1) * 1024 * 1024, 4 * 1024 * 1024)
        total_records = sum(reuse_distance_histogram.values())
        last_miss_ratio = 1
        mrc = defaultdict(lambda: 1)
        mrc_delta = defaultdict(lambda: 0)
        if total_records == 0:
            return mrc, mrc_delta

        for memory_size in memory_sizes:
            slab_cnt = memory_size // (4 * 1024 * 1024)
            max_objects = memory_size // object_size

            miss_count = sum(
                count for reuse_distance, count in reuse_distance_histogram.items()
                if reuse_distance >= max_objects or reuse_distance == -1
            )

            miss_ratio = miss_count / total_records
            miss_ratio_delta = last_miss_ratio - miss_ratio
            mrc[slab_cnt] = miss_ratio
            mrc_delta[slab_cnt] = miss_ratio_delta
            last_miss_ratio = miss_ratio

        return mrc, mrc_delta
    
    def reset_histogram(self):
        self.histogram.clear()


def read_csv_dict_line_by_line(file_path):
    with open(file_path, mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)  # Automatically handles the header
        for row in reader:
            yield row  # Row is a dict with keys from the header


def process_chunk(reuse_distance_calculators, alloc_sizes, max_slab, nr_requests, chunk_index, final_results):
    """
    Process a chunk of data to compute miss ratio curves and optimal allocations.

    Args:
        reuse_distance_calculators (dict): Reuse distance calculators for each allocation size.
        alloc_sizes (list): List of allocation sizes.
        max_slab (int): Maximum number of slabs.
        nr_requests (dict): Number of requests for each allocation size.
        chunk_index (int): Index of the current chunk.
        final_results (list): List to store the final results.

    Returns:
        None
    """
    print(f"Processing chunk {chunk_index}, nr_requests: {sum(nr_requests.values())}")
    mrc_dict = {}
    mrc_delta_dict = {}

    # Compute miss ratio curves
    for alloc_size in alloc_sizes:
        mrc, mrc_delta = reuse_distance_calculators[alloc_size].query_mrc(alloc_size, max_slab)
        mrc_dict[alloc_size] = mrc
        mrc_delta_dict[alloc_size] = mrc_delta

    # Compute optimal allocations
    r, _ = compute_optimal_allocations(
        mrc_dict, mrc_delta_dict, max_slab, alloc_sizes, [nr_requests[alloc_size] for alloc_size in alloc_sizes]
    )

    # Add metadata and append results
    for row in r:
        row['chunk_index'] = chunk_index
        row['request_cnt'] = sum(nr_requests.values())
    final_results.extend(r)

    # Reset calculators and request counters
    for reuse_distance_calculator in reuse_distance_calculators.values():
        reuse_distance_calculator.reset_histogram()
    for alloc_size in alloc_sizes:
        nr_requests[alloc_size] = 0


from zstandard import ZstdDecompressor

def process_trace(trace_file_path, chunk_size, alloc_sizes, max_slab, output_dir, binary_file=False):
    """
    Process a trace file (CSV or binary) to compute optimal slab allocations.

    Args:
        trace_file_path (str): Path to the trace file.
        chunk_size (int): Number of rows per chunk.
        alloc_sizes (list): List of allocation sizes.
        max_slab (int): Maximum number of slabs.
        output_dir (str): Directory to save the output.
        binary_file (bool): Whether the input file is a binary file.

    Returns:
        None
    """
    reuse_distance_calculators = {alloc_size: ReuseDistanceCalculator() for alloc_size in alloc_sizes}
    nr_requests = {alloc_size: 0 for alloc_size in alloc_sizes}
    final_results = []
    chunk_index = 0

    if binary_file:
        # Process binary file
        with open(trace_file_path, 'rb') as binary_file:
            decompressor = ZstdDecompressor()
            with decompressor.stream_reader(binary_file) as reader:
                while True:
                    # Read a single record (24 bytes per record)
                    record = reader.read(24)
                    if len(record) < 24:
                        break  # End of file

                    # Parse the binary record
                    obj_id = int.from_bytes(record[4:12], byteorder='little', signed=False)
                    obj_size = int.from_bytes(record[12:16], byteorder='little', signed=False)

                    # Common logic for processing the object
                    obj_size = max(24, obj_size)
                    obj_size += (32 + len(str(obj_id)))
                    index = bisect.bisect_left(alloc_sizes, obj_size)
                    if index < len(alloc_sizes):
                        alloc_size = alloc_sizes[index]
                        reuse_distance_calculators[alloc_size].feed(obj_id)
                        nr_requests[alloc_size] += 1

                    # Process the current chunk
                    if sum(nr_requests.values()) >= chunk_size:
                        process_chunk(reuse_distance_calculators, alloc_sizes, max_slab, nr_requests, chunk_index, final_results)
                        chunk_index += 1

    else:
        # Process CSV file
        with open(trace_file_path, mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row_index, row in enumerate(reader):
                obj_id = row['object_id']
                obj_size = int(row['object_size'])

                # Common logic for processing the object
                obj_size = max(24, obj_size)
                obj_size += (32 + len(str(obj_id)))
                index = bisect.bisect_left(alloc_sizes, obj_size)
                if index < len(alloc_sizes):
                    alloc_size = alloc_sizes[index]
                    reuse_distance_calculators[alloc_size].feed(obj_id)
                    nr_requests[alloc_size] += 1

                # Process the current chunk
                if row_index != 0 and row_index % chunk_size == 0:
                    process_chunk(reuse_distance_calculators, alloc_sizes, max_slab, nr_requests, chunk_index, final_results)
                    chunk_index += 1

    if sum(nr_requests.values()) > 0:
        process_chunk(reuse_distance_calculators, alloc_sizes, max_slab, nr_requests, chunk_index, final_results)

    # Save results to a CSV file
    df = pd.DataFrame(final_results)
    os.makedirs(output_dir, exist_ok=True)
    df.to_csv(os.path.join(output_dir, "optimal.csv"), index=False)
    
def call(csv_file_path, output_dir, max_slab, factor=None, max_size=None, min_size=None, 
         alignment=8, alloc_sizes=None, chunk_size=sys.maxsize, binary=False):
    if alloc_sizes is None:
        alloc_sizes = sorted(generate_alloc_sizes(factor, max_size, min_size, alignment))

    # Write alloc_sizes to a JSON file in the output directory
    os.makedirs(output_dir, exist_ok=True)
    alloc_sizes_json_path = os.path.join(output_dir, "alloc_size.json")
    with open(alloc_sizes_json_path, 'w') as json_file:
        json.dump(alloc_sizes, json_file, indent=4)
        
    
    process_trace(csv_file_path, chunk_size, alloc_sizes, max_slab, output_dir, binary)


from multiprocessing import Pool

def run_config(config):
    """
    Wrapper function to run the call function with updated output_dir.
    """
    file_path = config["file_path"]
    output_dir = f"{config['output_dir']}/chunk_size_{config['chunk_size']}"
    max_slab = config["max_slab"]
    alloc_sizes = config.get("alloc_sizes", None)
    chunk_size = config["chunk_size"]
    min_size = config.get("min_alloc_size", None)
    max_size = config.get("max_alloc_size", None)
    alloc_factor = config.get("alloc_factor", None)

    call(
        csv_file_path=file_path,
        output_dir=output_dir,
        max_slab=max_slab,
        alloc_sizes=alloc_sizes,
        chunk_size=chunk_size,
        factor=alloc_factor,
        max_size=max_size,
        min_size=min_size,
        binary='binary' in config and config['binary']  
    )

if __name__ == "__main__":
    configs = [
        {
            "file_path": "/mydata/hongshu/traces/meta2024_50m.csv",
            "output_dir": "/mydata/hongshu/optimal/meta2024_50m",
            "alloc_sizes": [
                72, 112, 168, 256, 384, 576, 864, 1296, 1944, 2920, 4384, 6576, 9864,
                14800, 22200, 33304, 49960, 74944, 112416, 168624, 252936, 379408, 523352
            ],
            "chunk_size": 500_000,
            "max_slab": 2048
        },
        {
            "file_path": "/mydata/hongshu/traces/meta2024_50m.csv",
            "output_dir": "/mydata/hongshu/optimal/meta2024_50m",
            "alloc_sizes": [
                72, 112, 168, 256, 384, 576, 864, 1296, 1944, 2920, 4384, 6576, 9864,
                14800, 22200, 33304, 49960, 74944, 112416, 168624, 252936, 379408, 523352
            ],
            "chunk_size": 1000_000,
            "max_slab": 2048
        },
        # {
        #     "file_path": "/mydata/hongshu/traces/synth_static_202.csv",
        #     "output_dir": "/mydata/hongshu/optimal/synth_static_202",
        #     "alloc_sizes": [256, 512, 1024, 2048, 4096],
        #     "chunk_size": 500_000,
        #     "max_slab": 2048
        # },
        # {
        #     "file_path": "/mydata/hongshu/traces/synth_static_202.csv",
        #     "output_dir": "/mydata/hongshu/optimal/synth_static_202",
        #     "alloc_sizes": [256, 512, 1024, 2048, 4096],
        #     "chunk_size": 1000_000,
        #     "max_slab": 2048
        # },
        # {
        #     "file_path": "/mydata/hongshu/traces/synth_dynamic_400.csv",
        #     "output_dir": "/mydata/hongshu/optimal/synth_dynamic_400",
        #     "alloc_sizes": [256, 512, 1024, 2048, 4096],
        #     "chunk_size": 500_000,
        #     "max_slab": 2048
        # },
        # {
        #     "file_path": "/mydata/hongshu/traces/synth_dynamic_400.csv",
        #     "output_dir": "/mydata/hongshu/optimal/synth_dynamic_400",
        #     "alloc_sizes": [256, 512, 1024, 2048, 4096],
        #     "chunk_size": 1000_000,
        #     "max_slab": 2048
        # },
        # {
        #     "file_path": "/mydata/hongshu/traces/synth_dynamic_500.csv",
        #     "output_dir": "/mydata/hongshu/optimal/synth_dynamic_500",
        #     "alloc_sizes": [2048, 4096],
        #     "chunk_size": 500_000,
        #     "max_slab": 2048
        # },
        # {
        #     "file_path": "/mydata/hongshu/traces/synth_dynamic_501.csv",
        #     "output_dir": "/mydata/hongshu/optimal/synth_dynamic_501",
        #     "alloc_sizes": [2048, 4096],
        #     "chunk_size": 500_000,
        #     "max_slab": 2048
        # },
        # {
        #     "file_path": "/mydata/hongshu/traces/synth_dynamic_502.csv",
        #     "output_dir": "/mydata/hongshu/optimal/synth_dynamic_502",
        #     "alloc_sizes": [2048, 4096],
        #     "chunk_size": 500_000,
        #     "max_slab": 2048
        # },
        # {
        #     "file_path": "/mydata/hongshu/traces/synth_dynamic_503.csv",
        #     "output_dir": "/mydata/hongshu/optimal/synth_dynamic_503",
        #     "alloc_sizes": [2048, 4096],
        #     "chunk_size": 500_000,
        #     "max_slab": 2048
        # },
        # {
        #     "file_path": "/mydata/hongshu/traces/synth_dynamic_504.csv",
        #     "output_dir": "/mydata/hongshu/optimal/synth_dynamic_504",
        #     "alloc_sizes": [2048, 4096],
        #     "chunk_size": 500_000,
        #     "max_slab": 2048
        # },
        {
            "file_path": "/mydata/hongshu/traces/cluster50.oracleGeneral.zst",
            "output_dir": "/mydata/hongshu/optimal/cluster50",
            "min_alloc_size": 84,
            "max_alloc_size": 184413,
            "alloc_factor": 1.5,
            "chunk_size": 1000_000,
            "max_slab": 4096,
            "binary": True
        },
        {
            "file_path": "/mydata/hongshu/traces/cluster53.oracleGeneral.zst",
            "output_dir": "/mydata/hongshu/optimal/cluster53",
            "min_alloc_size": 84,
            "max_alloc_size": 40635,
            "alloc_factor": 1.5,
            "chunk_size": 1000_000,
            "max_slab": 4096,
            "binary": True
        },
        {
            "file_path": "/mydata/hongshu/traces/cluster49.oracleGeneral.zst",
            "output_dir": "/mydata/hongshu/optimal/cluster49",
            "min_alloc_size": 104,
            "max_alloc_size": 61964,
            "alloc_factor": 1.5,
            "chunk_size": 1000_000,
            "max_slab": 4096,
            "binary": True
        },
        {
            "file_path": "/mydata/hongshu/traces/cluster45.oracleGeneral.zst",
            "output_dir": "/mydata/hongshu/optimal/cluster45",
            "min_alloc_size": 84,
            "max_alloc_size": 4224,
            "alloc_factor": 1.5,
            "chunk_size": 1000_000,
            "max_slab": 4096,
            "binary": True
        },
        {
            "file_path": "/mydata/hongshu/traces/cluster26.oracleGeneral.zst",
            "output_dir": "/mydata/hongshu/optimal/cluster26",
            "min_alloc_size": 84,
            "max_alloc_size": 226387,
            "alloc_factor": 1.5,
            "chunk_size": 1000_000,
            "max_slab": 4096,
            "binary": True
        },
        {
            "file_path": "/mydata/hongshu/traces/cluster22.oracleGeneral.zst",
            "output_dir": "/mydata/hongshu/optimal/cluster22",
            "min_alloc_size": 84,
            "max_alloc_size": 174,
            "alloc_factor": 1.5,
            "chunk_size": 1000_000,
            "max_slab": 4096,
            "binary": True
        }
    ]

    # Use multiprocessing Pool to run configs in parallel
    with Pool(processes=2) as pool:
        pool.map(run_config, configs)