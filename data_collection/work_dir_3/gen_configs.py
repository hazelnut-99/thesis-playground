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

traces = {
    "w06": {
        "file_path": "traces/w06.csv"
    }
}

allocators = ["LRU", "LRU2Q", "TINYLFU"]
rebalanceStrategies = {
    "default": {},
    "tail-age": {"rebalanceDiffRatio": 0.25},
    "free-mem": {},
    "marginal-hits": {},
    "hits": {"rebalanceDiffRatio": 0.1},
    "random": {},
    "disabled": {}
}
cacheSizeMBs = [256, 512, 1024, 2048, 4096, 8192, 16384, 32768]

experiment_configs = []

    
for trace_name, info in traces.items():
    path = BASE_FILE_PATH + info['file_path']
    for allocator, (rebalanceStrategy, rebalanceParams), cacheSize, useTraceTimer in itertools.product(
        allocators, rebalanceStrategies.items(), cacheSizeMBs, [True, False]
    ):
        
        cache_config = {
            "allocator": allocator,
            "minAllocSize": 72,
            "maxAllocSize": 4194304,
            "allocFactor": 1.25,
            "cacheSizeMB": cacheSize,
            "poolRebalanceIntervalSec": 1,
            "moveOnSlabRelease": False,
            "rebalanceStrategy": rebalanceStrategy,
            **rebalanceParams
        }
        test_config = {
            "traceFileNames": [path],
            "useTraceTimer": useTraceTimer,
        }
        memo_config = {
            "trace_name": trace_name,
            "uuid": str(uuid.uuid4()),
            "useTraceTimer": useTraceTimer
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