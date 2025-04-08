
import os
import pandas as pd
from collections import defaultdict


def build_dp_table(mrc_dict, max_total_slabs, trace_names, access_freqs, pretty_print=False):
    """
    Builds the DP table and allocation table for the given trace names and maximum total slabs.

    Parameters:
    mrc_dict (dict): A nested dictionary that maps trace_name to their miss ratio at different slab_cnt.
    max_total_slabs (int): The maximum number of slabs to consider.
    trace_names (list): The trace names that we are interested in.
    access_freqs (list): The access frequencies for the trace names.
    pretty_print (bool): If True, pretty print the DP table and allocation table.

    Returns:
    tuple: (dp, allocation) where:
        - dp: The DP table storing the minimum weighted miss ratio for each trace and slab count.
        - allocation: The allocation table storing the number of slabs allocated to each trace.
    """
    # Number of traces
    n = len(trace_names)
    
    # Initialize the DP table
    dp = [[float('inf')] * (max_total_slabs + 1) for _ in range(n + 1)]
    dp[0][0] = 0  # Base case: 0 slabs for 0 traces has a miss ratio of 0
    
    # Initialize the allocation table
    allocation = [[0] * (max_total_slabs + 1) for _ in range(n + 1)]
    
    # Fill the DP table
    for i in range(1, n + 1):
        trace_name = trace_names[i - 1]
        access_freq = access_freqs[i - 1]
        for j in range(max_total_slabs + 1):
            for k in range(j + 1):
                if k in mrc_dict[trace_name]:
                    miss_ratio = mrc_dict[trace_name][k]
                    miss_count = miss_ratio * access_freq
                    if dp[i - 1][j - k] + miss_count < dp[i][j]:
                        dp[i][j] = dp[i - 1][j - k] + miss_count
                        allocation[i][j] = k
    
    # Pretty print the DP table and allocation table if requested
    if pretty_print:
        print("DP Table:")
        for row in dp:
            print(', '.join([f'{x:.4f}' for x in row]))
        print("\nAllocation Table:")
        for row in allocation:
            print(', '.join([f'{x:3d}' for x in row]))
    
    return dp, allocation


def backtrack_allocation(dp, allocation, trace_names, total_slabs, access_freqs):
    """
    Performs backtracking on the precomputed DP table to determine the optimal allocation for a given total_slabs.

    Parameters:
    dp (list): The DP table built by `build_dp_table`.
    allocation (list): The allocation table built by `build_dp_table`.
    trace_names (list): The trace names that we are interested in.
    total_slabs (int): The total number of slabs to allocate.
    access_freqs (list): The access frequencies for the trace names.

    Returns:
    tuple: (result, normalized_miss_ratio) where:
        - result: A dictionary with the optimal allocation of slabs for each trace name.
        - normalized_miss_ratio: The minimized weighted miss ratio normalized by the total access frequency.
    """
    # Number of traces
    n = len(trace_names)
    
    # Backtrack to find the optimal allocation
    result = {}
    j = total_slabs
    for i in range(n, 0, -1):
        trace_name = trace_names[i - 1]
        result[trace_name] = allocation[i][j]
        j -= allocation[i][j]
    
    # Normalized miss ratio
    normalized_miss_ratio = dp[n][total_slabs] / sum(access_freqs)
    
    return result, normalized_miss_ratio



def compute_optimal_allocations(mrc_dict, mrc_delta_dict, max_total_slabs, trace_names, access_freqs):
    """
    Compute the optimal slab allocations and miss ratios for each total_slab from 1 to max_total_slabs.

    Parameters:
    mrc_dict (dict): A nested dictionary that maps trace_name to their miss ratio at different slab_cnt.
    max_total_slabs (int): The maximum number of slabs to consider.
    trace_names (list): The trace names that we are interested in.
    access_freqs (list): The access frequencies for the trace names.

    Returns:
    pd.DataFrame: A DataFrame where each row corresponds to a total_slab and contains:
        - Columns for each trace_name (number of slabs allocated to the trace).
        - 'total_miss_ratio': The normalized miss ratio for the given total_slab.
        - 'total_slab_cnt': The total number of slabs.
    """

    dp, allocation = build_dp_table(mrc_dict, max_total_slabs, trace_names, access_freqs)


    results = []
    for total_slab in range(1, max_total_slabs + 1):
        alloc, miss_ratio = backtrack_allocation(dp, allocation, trace_names, total_slab, access_freqs)
        
        row = {trace_name: alloc[trace_name] for trace_name in trace_names}
        row['total_miss_ratio'] = miss_ratio
        row['total_slab_cnt'] = total_slab
        for trace_name in trace_names:
            row[f"{trace_name}_miss_ratio"] = mrc_dict[trace_name][alloc[trace_name]]
            row[f"{trace_name}_miss_ratio_delta"] = mrc_delta_dict[trace_name][alloc[trace_name]]
            row[f"{trace_name}_access_freq"] = access_freqs[trace_names.index(trace_name)]
        results.append(row)

    results_df = pd.DataFrame(results)
    return results_df


def calc_optimal_allocation(directory, slab_upper_limit = 4096):
    subtracec_stat_path = os.path.join(directory, "subtrace_stat.csv")
    miss_ratios_path = os.path.join(directory, "miss_ratios.csv")
    
    subtrace_miss_ratio_df = pd.read_csv(miss_ratios_path)
    subtrace_stat_df = pd.read_csv(subtracec_stat_path)
    
    subtrace_miss_ratio_df['class_size'] = subtrace_miss_ratio_df['subtrace_name'].map(lambda x: int(x.split('.')[0].split('_')[-1]))
    subtrace_stat_df['class_size'] = subtrace_stat_df['subtrace_name'].map(lambda x: int(x.split('.')[0].split('_')[-1]))
    

    records = subtrace_miss_ratio_df.to_dict(orient='records')
    mrc_dict = defaultdict(dict)
    mrc_delta_dict = defaultdict(dict)

    for record in records:
        mrc_dict[record['class_size']][record['slab_cnt']] = record['miss_ratio']
        mrc_delta_dict[record['class_size']][record['slab_cnt']] = record['miss_ratio_delta']

    for class_size in mrc_dict:
        mrc_dict[class_size][0] = 1
        mrc_delta_dict[class_size][0] = float('inf')
    
    access_freqs = {
        r['class_size']: r['record_count']
        for r in subtrace_stat_df.to_dict(orient='records')
    }

    optim_allocs_df = compute_optimal_allocations(mrc_dict, mrc_delta_dict, slab_upper_limit, list(mrc_dict.keys()), [access_freqs[k] for k in mrc_dict.keys()])
    
    optim_allocs_df.to_csv(os.path.join(directory, "optimal_allocations.csv"), index=False, float_format='%.6f')

