import pandas as pd
import json

base_dir="work_dir_5/outcome"
df = pd.read_csv(f"{base_dir}/report_raw.csv")

def read_cachebench_config(dir):
    with open(f"{base_dir}/{dir}/config.json") as f:
        return json.load(f)

def read_exp_config(dir):
    with open(f"{base_dir}/{dir}/exp_config.json") as f:
        return json.load(f)

def add_config_columns(df):
    new_columns = {}

    for index, row in df.iterrows():
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
print(df.columns)
df = add_config_columns(df)
df.rename(columns={'wss': 'wss_MiB'}, inplace=True)
df['_missRatio'] = df['_numCacheGetMisses'] / df['_numCacheGet']
df.to_csv(f"{base_dir}/report.csv", index=False)

