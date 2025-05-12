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
    f"synth_zipf_{name}": {
        "file_path": f"traces/synth_zipf_{name}.csv",
        "allocSizes": [int(name.split('_')[1])]
    }
    for name in ['100_512', '050_512', '100_1024', '050_1024']
}

cache_sizes = list(set([i * 4 + 4 for i in (list(range(0, 256, 2)) + list(range(256, 512, 16)) + [1]) if i != 0] ))
allocators = ['LRU2Q']
rebalanceStrategies = {
    "marginal-hits": {}
}

experiment_configs = []
rebalance_intervals = [5_000, 500_000]
    
for trace_name, info in traces.items():
    op_count = 21000000
    path = BASE_FILE_PATH + info['file_path']

    for cache_size, allocator, (rebalanceStrategy, rebalanceParams), xreq in \
        itertools.product(cache_sizes, allocators, rebalanceStrategies.items(), rebalance_intervals):
        cache_config = {
            "allocator": allocator,
            "cacheSizeMB": cache_size,
            "allocSizes": info["allocSizes"],
            "moveOnSlabRelease": False,
            "rebalanceStrategy": rebalanceStrategy,
            "poolRebalanceIntervalSec": 1,
            "wakeUpRebalancerEveryXReqs": xreq,
            **rebalanceParams
        }
        test_config = {
            "numOps": op_count,
            "traceFileNames": [path]
        }
        memo_config = {
            "trace_name": trace_name,
            "cache_size": cache_size,
            "allocator": allocator,
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