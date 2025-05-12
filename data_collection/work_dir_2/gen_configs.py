import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pandas as pd
import math
import itertools
import data_collection.util as util
import json
import uuid

BASE_FILE_PATH = "/users/Hongshu/"

current_dir = os.path.dirname(__file__)
trace_info_path = os.path.join(current_dir, 'trace_info.csv')
trace_info_df = pd.read_csv(trace_info_path)
trace_info_df.set_index('trace_name', inplace=True)
trace_info_dict = trace_info_df.to_dict(orient='index')

traces = {
    "cluster52_100m": {
        "file_path": "traces/cluster52_sample.csv",
        "maxAllocSize": 7000
    },
    "w55": {
        "file_path": "traces/w55.csv",
        "maxAllocSize": 2000000
    },
    "w65": {
        "file_path": "traces/w65.csv",
        "maxAllocSize": 2000000
    },
    "w75": {
        "file_path": "traces/w75.csv",
        "maxAllocSize": 2000000
    },
    "w85": {
        "file_path": "traces/w85.csv",
        "maxAllocSize": 2000000
    },   
    "w95": {
        "file_path": "traces/w95.csv",
        "maxAllocSize": 2000000
    }, 
}

cache_configs = {
   "mhMovingAverageParam": [(0.1, False), (0.2, False), (0.3, True), (0.4, False), (0.5, False), (0.6, False), (0.7, False), (0.8, False), (0.9, False)],
}

configs = []

def dfs(configs, keys, current_config, index):
    if index == len(keys):
        configs.append(current_config.copy())
        return

    key = keys[index]
    for value, flag in cache_configs[key]:
        if not flag and any(not f for k, (v, f) in current_config.items() if k != key):
            continue
        current_config[key] = (value, flag)
        dfs(configs, keys, current_config, index + 1)
        del current_config[key]

keys = list(cache_configs.keys())
dfs(configs, keys, {}, 0)




allocators = ["LRU2Q"]



workingSetRatios = [0.005, 0.01, 0.02, 0.05, 0.1]

experiment_configs = []

    
for trace_name, info in trace_info_dict.items():
    op_count = info['number_of_requests']
    path = BASE_FILE_PATH + traces[trace_name]['file_path']
    wss = info['wss']
    maxAllocSize = traces[trace_name]['maxAllocSize']

    for config, allocator, ws_ratio in itertools.product(
        configs, allocators, workingSetRatios
    ):
        
        cache_config = {
            "allocator": allocator,
            "minAllocSize": 72,
            "maxAllocSize": maxAllocSize,
            "allocFactor": 1.25,
            "cacheSizeMB": math.ceil(wss * ws_ratio),
            "poolRebalanceIntervalSec": 1,
            "moveOnSlabRelease": False,
            "rebalanceStrategy": 'marginal-hits',
            "mhMovingAverageParam": config["mhMovingAverageParam"][0]
        }
        test_config = {
            "numOps": op_count,
            "traceFileNames": [path]
        }
        memo_config = {
            "trace_name": trace_name,
            "ws_ratio": ws_ratio,
            "uuid": str(uuid.uuid4())
        }
        memo_config.update(info)
        
        full_config = {
            'cache_config': cache_config,
            'test_config': test_config,
            'memo_config': memo_config
        }
        if util.is_valid_config(full_config):
            experiment_configs.append(full_config)
        else:
            print(f"not valid {json.dumps(full_config, indent=2)}")
        

print(f"total number of configs: {len(experiment_configs)}")

with open(os.path.join(current_dir, 'exp_configs.json'), 'w') as f:
    json.dump(experiment_configs, f, indent=2)