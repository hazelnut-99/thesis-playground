import pandas as pd
import json
import os

base_dir=f"work_dir"


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
        print(1)
        directory = os.path.basename(dir)
        
        meta_config = read_meta_config(dir)
        result_json = read_result_json(dir)
        bench_config = read_cachebench_config(dir)
        
        
        if not result_json:
            return []

        if isinstance(result_json, dict):
            result_json = [result_json]  
        results = []
        for item in result_json:
            item = {'_' + k: v for k, v in item.items()}  
            combined_result = {
                **meta_config,
                **bench_config['cache_config'],
                **bench_config['test_config'],
                **item
            }
            results.append(combined_result)

        return results
    return []
    

def collect_result():
    result_list = []
    for d in os.listdir(base_dir):
        dir = os.path.join(base_dir, d)
        print(dir)
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
df.to_csv(f"report/report.csv", index=False)

