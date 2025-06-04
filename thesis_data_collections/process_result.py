import pandas as pd
import json
import os

top_dir = "work_dir_1_optimal/"
base_dir=f"{top_dir}/outcome"


def read_cachebench_config(dir):
    with open(f"{dir}/config.json") as f:
        return json.load(f)

def read_exp_config(dir):
    with open(f"{dir}/exp_config.json") as f:
        return json.load(f)

def read_result_json(dir):
    try:
        with open(f"{dir}/out.json") as f:
            return json.load(f)
    except:
        print(f"Failed to read {dir}/out.json")
        return None

def add_config_columns(df):
    new_columns = {}

    for index, row in df.iterrows():
        if not row['directory'].strip():
            continue
        exp_config = read_exp_config(row['directory'])
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
    exp_config_path = os.path.join(dir, "exp_config.json")
    result_json_path = os.path.join(dir, "out.json")

    if os.path.isfile(config_path) and os.path.isfile(exp_config_path) and os.path.isfile(result_json_path):
        directory = os.path.basename(dir)
        exp_config = read_exp_config(dir)
        cache_config = exp_config.get('cache_config', {})
        memo_config = exp_config.get('memo_config', {})
        result_json = read_result_json(dir)
        if not result_json:
            return []

        if isinstance(result_json, dict):
            result_json = [result_json]  
        results = []
        for item in result_json:
            item = {'_' + k: v for k, v in item.items()}  
            combined_result = {
                'directory': directory,
                **cache_config,
                **memo_config,
                **item
            }
            results.append(combined_result)

        return results
    return []
    

def collect_result():
    result_list = []
    for d in os.listdir(base_dir):
        dir = os.path.join(base_dir, d)
        print(d)
        result = process_dir(dir)
        if result:
            result_list.extend(result)
    return pd.DataFrame(result_list)


df = collect_result()
if '_getMissCnt' in df.columns and '_getCnt' in df.columns:
    df['_missRatio'] = df['_getMissCnt'] / df['_getCnt']
df.to_csv(f"{top_dir}/report.csv", index=False)

