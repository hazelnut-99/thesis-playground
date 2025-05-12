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
    "synth_static_1": {
        "file_path": "traces/synth_static_1.csv",
        "allocSizes": [512, 1024]
    },
    "synth_static_2": {
        "file_path": "traces/synth_static_2.csv",
        "allocSizes": [512, 1024]
    },
    "synth_static_4": {
        "file_path": "traces/synth_static_4.csv",
        "allocSizes": [512, 1024]
    }, 
    "synth_periodic_1": {
        "file_path": "traces/synth_periodic_1.csv",
        "allocSizes": [128, 1024]
    },
    "synth_periodic_2": {
        "file_path": "traces/synth_periodic_2.csv",
        "allocSizes": [128, 1024]
    },
    "synth_periodic_3": {
        "file_path": "traces/synth_periodic_3.csv",
        "allocSizes": [128, 1024]
    },
    "synth_periodic_4": {
        "file_path": "traces/synth_periodic_4.csv",
        "allocSizes": [128, 1024]
    },
    "synth_periodic_5": {
        "file_path": "traces/synth_periodic_5.csv",
        "allocSizes": [128, 1024]
    }
}


cache_configs = {
    "poolRebalanceIntervalSec": [(0, False), (1, True), (2, False), (4, False), (8, False)],
    "moveOnSlabRelease": [(True, False), (False, True)]
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
rebalanceStrategies = {
    "tail-age": {"rebalanceDiffRatio": 0.25},
    "marginal-hits": {},
    "hits": {"rebalanceDiffRatio": 0.1},
    "disabled": {},
    "default": {}
}


experiment_configs = []
    
for trace_name, info in traces.items():
    op_count = 21000000
    path = BASE_FILE_PATH + info['file_path']

    for config, allocator, (rebalanceStrategy, rebalanceParams) in itertools.product(
        configs, allocators, rebalanceStrategies.items()
    ):
        
        cache_config = {
            "allocator": allocator,
            "cacheSizeMB": 64,
            "allocSizes": info["allocSizes"],
            "moveOnSlabRelease": config['moveOnSlabRelease'][0],
            "poolRebalanceIntervalSec": config['poolRebalanceIntervalSec'][0],
            "rebalanceStrategy": rebalanceStrategy,
            **rebalanceParams
        }
        test_config = {
            "numOps": op_count,
            "traceFileNames": [path]
        }
        memo_config = {
            "trace_name": trace_name,
            "uuid": trace_name + '_' + str(uuid.uuid4())
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