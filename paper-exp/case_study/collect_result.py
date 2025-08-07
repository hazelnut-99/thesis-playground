import pandas as pd
import json
import os
import glob

base_dir=f"work_dir_synthetic_thesis"


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
    return None if not found
    """
    import re
    log_path = os.path.join(dir, "log.txt")
    if not os.path.isfile(log_path):
        return None
    with open(log_path, "r") as f:
        for line in f:
            m = re.search(r"Released\s+([\d,]+)\s+slabs", line)
            if m:
                num = m.group(1).replace(",", "")
                try:
                    return int(num)
                except Exception:
                    return
    

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
    for d in os.listdir(base_dir):
        dir = os.path.join(base_dir, d)
        try:
            result = process_dir(dir)
            if result:
                result_list.extend(result)
        except Exception as e:
            print(f"Error processing directory {dir}: {e}")
    return pd.DataFrame(result_list)


df = collect_result()
if '_getMissCnt' in df.columns and '_getCnt' in df.columns:
    df['_missRatio'] = df['_getMissCnt'] / df['_getCnt']
print("finished collecting results")
df.to_csv(f"report_synthetic_thesis.csv", index=False)

