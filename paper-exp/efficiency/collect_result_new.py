import pandas as pd
import json
import os
import glob
import numpy as np

# Configuration

base_path1 = "/nfs/hongshu/thesis-playground/paper-exp/efficiency/"
base_path2 = "/proj/latencymodel-PG0/hongshu/paper-exp/"

base_dirs = [
    base_path1 + "work_dir_meta_detailed_wsr",
    base_path1 + "work_dir_new",
    base_path1 + "work_dir_cdn",
    base_path2 + "lama/work_dir_lama_full",
    base_path2 + "lama_new/work_dir_meta_thesis",
    #base_path1 + "work_dir_lama_window"
]
output_file = "report/end-to-end/report_complete.csv"
#output_file = "report/end-to-end/report_lama_detailed.csv"
# base_dirs = [
#     base_path1 + "work_dir_meta_sensitivity",
# ]
# output_file = "report/fixed-thresh/report_sensitivity.csv"



def read_cachebench_config(dir):
    with open(f"{dir}/config.json") as f:
        return json.load(f)

def read_meta_config(dir):
    with open(f"{dir}/meta.json") as f:
        return json.load(f)

def read_result_json(dir):
    try:
        with open(f"{dir}/result.json") as f:
            return json.load(f)
    except:
        print(f"Failed to read {dir}/out.json")
        return None

def read_throughput_json(dir):
    """
    Finds a file in 'dir' matching 'tx.*.json', reads and returns its JSON content.
    Returns None if not found or on error.
    """
    pattern = os.path.join(dir, "tx.*.json")
    files = glob.glob(pattern)
    if not files:
        return None
    try:
        with open(files[0]) as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to read {files[0]}: {e}")
        return None


def read_rebalanced_slabs(dir):
    """
    read file dir/log.txt
    grep the row 'Released X slabs'
    extract the number X (may have commas), cast to int, return it
    return 0 if not found
    """
    import re
    log_path = os.path.join(dir, "log.txt")
    if not os.path.isfile(log_path):
        return 0
    with open(log_path, "r") as f:
        for line in f:
            m = re.search(r"Released\s+([\d,]+)\s+slabs", line)
            if m:
                num = m.group(1).replace(",", "")
                try:
                    return int(num)
                except Exception:
                    return 0
    return 0

def add_config_columns(df):
    new_columns = {}

    for index, row in df.iterrows():
        if not row['directory'].strip():
            continue
        exp_config = read_meta_config(row['directory'])
        cache_config = exp_config.get('cache_config', {})
        memo_config = exp_config.get('memo_config', {})

        combined_config = {**cache_config, **memo_config}

        for k, v in combined_config.items():
            if k not in new_columns:
                new_columns[k] = [None] * len(df)
            new_columns[k][index] = v

    for k, v in new_columns.items():
        df[k] = v

    return df


def process_dir(dir):
    config_path = os.path.join(dir, "config.json")
    meta_path = os.path.join(dir, "meta.json")
    result_json_path = os.path.join(dir, "result.json")

    if os.path.isfile(config_path) and os.path.isfile(meta_path) and os.path.isfile(result_json_path):
        # Check operation count consistency after file validation
        # Find tx.*.json file
        tx_files = [f for f in os.listdir(dir) if f.startswith("tx.") and f.endswith(".json")]
        if not tx_files:
            return []
        tx_path = os.path.join(dir, tx_files[0])

        # Check operation count consistency
        try:
            with open(config_path) as cf:
                config = json.load(cf)
            num_ops = config.get("test_config", {}).get("numOps", None)
        except Exception:
            return []

        try:
            with open(tx_path) as tf:
                tx = json.load(tf)
            ops = tx.get("ops", None)
        except Exception:
            return []

        if num_ops != ops and num_ops and ops and (num_ops - ops) > 100:
            ratio = ops / num_ops if num_ops != 0 else float('inf')
            print(f"Skipping {dir}: numOps={num_ops}, ops={ops}, ratio={ratio:.4f} - inconsistent operation count")
            return []
        
        # Proceed with normal processing if all checks pass        
        meta_config = read_meta_config(dir)
        result_json = read_result_json(dir)
        bench_config = read_cachebench_config(dir)
        throughput_result = read_throughput_json(dir)
        rebalanced_slabs_value = read_rebalanced_slabs(dir)
        
        
        if not result_json:
            return []

        if isinstance(result_json, dict):
            result_json = [result_json]  
        results = []
        for item in result_json:
            item = {'_' + k: v for k, v in item.items()}  
            combined_result = {
                **meta_config,
                **throughput_result,
                **bench_config['cache_config'],
                **bench_config['test_config'],
                **item
            }
            combined_result['rebalanced_slabs'] = rebalanced_slabs_value
            results.append(combined_result)

        return results
    return []
    

def collect_result():
    result_list = []
    for base_dir in base_dirs:
        if not os.path.exists(base_dir):
            print(f"Warning: Directory {base_dir} does not exist, skipping...")
            continue
        
        print(f"Processing base directory: {base_dir}")
        for d in os.listdir(base_dir):
            dir = os.path.join(base_dir, d)
            try:
                result = process_dir(dir)
                if result:
                    # Add base_dir info to each result for tracking
                    for item in result:
                        item['base_dir'] = base_dir
                    result_list.extend(result)
            except Exception as e:
                print(f"Error processing directory {dir}: {e}")
    return pd.DataFrame(result_list)


def remap_df(df):
    df = df.copy()
    
    # Handle missing num_slab_classes column by reading from trace_info.csv
    try:
        trace_info_path = "../trace_info.csv"
        trace_info_df = pd.read_csv(trace_info_path)
        trace_info_dict = trace_info_df.set_index('trace_name')['num_slab_classes'].to_dict()
        
        # Add or fill num_slab_classes column based on trace_name
        if 'num_slab_classes' not in df.columns:
            df['num_slab_classes'] = df['trace_name'].map(trace_info_dict)
        else:
            # Fill missing values in existing column
            df['num_slab_classes'] = df['num_slab_classes'].fillna(df['trace_name'].map(trace_info_dict))
        print(f"Added/filled num_slab_classes column from {trace_info_path}")
    except Exception as e:
        print(f"Warning: Could not read trace_info.csv or add num_slab_classes: {e}")
        # If we can't read the file, skip the filtering step
        print("Skipping num_slab_classes filtering")
    
    # Only apply the filter if num_slab_classes column exists and has valid values
    if 'num_slab_classes' in df.columns:
        # Filter out rows where num_slab_classes > slab_cnt (but keep rows with missing num_slab_classes)
        df = df[(df['num_slab_classes'].isna()) | (df['num_slab_classes'] <= df['slab_cnt'])]

    # 1. Rebalance strategy mapping
    def map_rebalance_strategy(x):
        if x == "marginal-hits-new":
            return "marginal-hits-tuned"
        elif x == "marginal-hits-old":
            return "marginal-hits"
        else:
            return x

    df["rebalance_strategy"] = df["rebalanceStrategy"].apply(map_rebalance_strategy)
    
    # Check if columns exist before applying filters to avoid bugs
    if 'maxDecayInterval' in df.columns:
        df = df[(df['maxDecayInterval'].isna()) | (df['maxDecayInterval'] == 50_000)]
    if 'countColdTailHitsOnly' in df.columns:
        df = df[(df['countColdTailHitsOnly'].isna()) | (df['countColdTailHitsOnly'] == True)]
    if 'mhMovingAverageParam' in df.columns:
        df = df[(df['mhMovingAverageParam'].isna()) | (df['mhMovingAverageParam'] == 0.3)]

    # 2. Allocator mapping
    def map_allocator(x):
        if x == "TINYLFUTail":
            return "TINYLFU"
        elif x == "SIMPLE2Q":
            return "LRU"
        else:
            return x

    df["allocator"] = df["allocator"].apply(map_allocator)

    # 3. Tag mapping
    def map_tag(row):
        if row["rebalanceStrategy"] in ["marginal-hits-new", "marginal-hits-old"] and row["allocator"] == "LRU2Q":
            val = row.get("countColdTailHitsOnly", False)
            if pd.notnull(val) and bool(val):
                return "cold"
            else:
                return "warm-cold"
        else:
            return None

    df["tag"] = df.apply(map_tag, axis=1)

    # 5. Rename columns
    rename_dict = {
        "_missRatio": "miss_ratio",
        "_rebalancerNumRebalancedSlabs": "n_rebalanced_slabs",
        "wakeUpRebalancerEveryXReqs": "monitor_interval",
        "_allocFailures": "n_alloc_failures"
    }
    df = df.rename(columns=rename_dict)

    # 6. Select columns to keep
    keep_cols = [
        "trace_name", "number_of_requests", "wsr", "slab_size", "slab_cnt", "rebalanceDiffRatio", "mhMinDiff",
        "rebalance_strategy", "allocator", "tag", "throughput", "rebalanced_slabs", 
        "miss_ratio", "n_rebalanced_slabs", "monitor_interval", "n_alloc_failures", "uuid", 
        "mhMovingAverageParam", "mhMinDiff", "thresholdAIADStep", "emrLow", "emrHigh", "footprintBufferSize"
    ]
    # Add base_dir to keep_cols if it exists
    if 'base_dir' in df.columns:
        keep_cols.append('base_dir')
    
    keep_cols = [col for col in keep_cols if col in df.columns]
    return df[keep_cols]


def add_miss_ratio_reduction_from_disabled(df):
    df = df.copy()
    df = df.sort_values(["trace_name", "wsr", "allocator"])
    reduction_series = pd.Series(np.nan, index=df.index)

    group_cols = ["trace_name", "wsr", "allocator"]
    for _, group in df.groupby(group_cols):
        baseline = group[group["rebalance_strategy"] == "disabled"]
        if baseline.empty:
            baseline_miss = np.nan
        else:
            baseline_miss = baseline.iloc[0]["miss_ratio"]
        for idx, row in group.iterrows():
            reduction = baseline_miss - row["miss_ratio"] if pd.notnull(baseline_miss) and pd.notnull(row["miss_ratio"]) else np.nan
            reduction_series.at[idx] = reduction

    df["miss_ratio_reduction_from_disabled"] = reduction_series
    return df


def add_miss_ratio_reduction_from_lru_disabled(df):
    """
    For each group of (trace_name, wsr), use the row with allocator=='LRU' and rebalance_strategy=='disabled' as baseline.
    For each row in the group, compute miss_ratio_reduction_from_lru_disabled = baseline_miss_ratio - row['miss_ratio'].
    """
    df = df.copy()
    reduction_series = pd.Series(np.nan, index=df.index)
    group_cols = ["trace_name", "wsr"]

    # Build a lookup for baseline miss_ratio
    baseline_lookup = (
        df[(df["allocator"] == "LRU") & (df["rebalance_strategy"] == "disabled")]
        .set_index(group_cols)["miss_ratio"]
        .to_dict()
    )

    for idx, row in df.iterrows():
        key = (row["trace_name"], row["wsr"])
        baseline_miss = baseline_lookup.get(key, np.nan)
        if pd.notnull(baseline_miss) and pd.notnull(row["miss_ratio"]):
            reduction_series.at[idx] = baseline_miss - row["miss_ratio"]
        else:
            reduction_series.at[idx] = np.nan

    df["miss_ratio_reduction_from_lru_disabled"] = reduction_series
    return df


def add_tuned_improvement(df):
    df = df.copy()
    mask = df["rebalance_strategy"].str.startswith("marginal-hits-tuned")

    lookup = df[df["rebalance_strategy"] == "marginal-hits"].set_index(
        ["trace_name", "wsr", "allocator", "tag", "monitor_interval"]
    )["miss_ratio"]

    improvements = pd.Series(np.nan, index=df.index)
    for idx, row in df[mask].iterrows():
        key = (row["trace_name"], row["wsr"], row["allocator"], row["tag"], row["monitor_interval"])
        base = lookup.get(key, np.nan)
        if isinstance(base, pd.Series):
            base = base.iloc[0]
        if pd.notnull(base) and pd.notnull(row["miss_ratio"]):
            improvements.at[idx] = base - row["miss_ratio"]
        else:
            improvements.at[idx] = np.nan

    df["tuned_improvement"] = improvements
    return df


raw_df = collect_result()
if '_getMissCnt' in raw_df.columns and '_getCnt' in raw_df.columns:
    raw_df['_missRatio'] = raw_df['_getMissCnt'] / raw_df['_getCnt']

print("finished collecting results")

# Process the raw dataframe
remapped_df = remap_df(raw_df)
remapped_df["trace_name"] = remapped_df["trace_name"].replace({
    "meta_202210_kv_traces_all_sort": "meta_202210_kv",
    "meta_202401_kv_traces_all_sort": "meta_202401_kv"
})

remapped_df = add_miss_ratio_reduction_from_disabled(remapped_df)
remapped_df = add_miss_ratio_reduction_from_lru_disabled(remapped_df)
remapped_df = add_tuned_improvement(remapped_df)

# Filter out warm-cold tag (keep NaN/None tags)
remapped_df = remapped_df[(remapped_df['tag'].isna()) | (remapped_df['tag'] != 'warm-cold')]

# Filter out free-mem strategy
remapped_df = remapped_df[remapped_df['rebalance_strategy'] != 'free-mem']

# Drop duplicate rows from processed dataframe
remapped_df = remapped_df.drop_duplicates()

# Create output directory if it doesn't exist
os.makedirs(os.path.dirname(output_file), exist_ok=True)

# Save both raw and processed results
raw_output_file = output_file.replace('.csv', '_raw.csv')
processed_output_file = output_file.replace('.csv', '_processed.csv')

raw_df.to_csv(raw_output_file, index=False)
remapped_df.to_csv(processed_output_file, index=False)

print(f"Raw results saved to: {raw_output_file}")
print(f"Processed results saved to: {processed_output_file}")
print(f"Total raw records: {len(raw_df)}")
print(f"Total processed records: {len(remapped_df)}")

