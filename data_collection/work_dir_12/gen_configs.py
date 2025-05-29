# this is for interval and alpha


import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pandas as pd
import math
import copy
import itertools
import data_collection.util as util
import json
import uuid

BASE_FILE_PATH = "/mydata/hongshu/"

current_dir = os.path.dirname(__file__)

traces = {
    "synth_dynamic_400": {
        "extra": {
            "allocSizes": [256, 512, 1024, 2048, 4096]
        },
        "cache_sizes": [64, 128, 256],
        "file_path": BASE_FILE_PATH + "traces/synth_dynamic_400.csv"
    },
    "synth_dynamic_500": {
        "extra": {
            "allocSizes": [2048, 4096]
        },
        "cache_sizes": [32],
        "file_path": BASE_FILE_PATH + "traces/synth_dynamic_500.csv"
    },
    "synth_dynamic_501": {
        "extra": {
            "allocSizes": [2048, 4096]
        },
        "cache_sizes": [32],
        "file_path": BASE_FILE_PATH + "traces/synth_dynamic_501.csv"
    },
    "synth_dynamic_502": {
        "extra": {
            "allocSizes": [2048, 4096]
        },
        "cache_sizes": [32],
        "file_path": BASE_FILE_PATH + "traces/synth_dynamic_502.csv"
    },
    "synth_dynamic_503": {
        "extra": {
            "allocSizes": [2048, 4096]
        },
        "cache_sizes": [32],
        "file_path": BASE_FILE_PATH + "traces/synth_dynamic_503.csv"
    },        
    "synth_dynamic_504": {
        "extra": {
            "allocSizes": [2048, 4096]
        },
        "cache_sizes": [32],
        "file_path": BASE_FILE_PATH + "traces/synth_dynamic_504.csv"
    }, 
    "meta_2024_50m_1": {
        "extra": {
            "allocSizes": [
                72,
                112,
                168,
                256,
                384,
                576,
                864,
                1296,
                1944,
                2920,
                4384,
                6576,
                9864,
                14800,
                22200,
                33304,
                49960,
                74944,
                112416,
                168624,
                252936,
                379408,
                523352
            ]
        },
        "cache_sizes": [128, 256, 512, 1024],
        "file_path": BASE_FILE_PATH + "traces/meta2024_50m.csv"
    }
       
}


reset_timings = {
    "synth_dynamic_400": "39999999",
    "synth_dynamic_500": "9999999,19999999,29999999,39999999",
    "synth_dynamic_501": "4999999,9999999,14999999,19999999,24999999,29999999,34999999,39999999",
    "synth_dynamic_502": "2499999,4999999,7499999,9999999,12499999,14999999,17499999,19999999,22499999,24999999,27499999,29999999,32499999,34999999,37499999,39999999",
    "synth_dynamic_503": "1249999,2499999,3749999,4999999,6249999,7499999,8749999,9999999,11249999,12499999,13749999,14999999,16249999,17499999,18749999,19999999,21249999,22499999,23749999,24999999,26249999,27499999,28749999,29999999,31249999,32499999,33749999,34999999,36249999,37499999,38749999,39999999",
}


allocators = ['LRU2Q']
wakeUpRebalancerEveryXReqs = [i * 1000 for i in range(20, 1100, 20)]

rebalanceStrategies = {
    "marginal-hits": [
        {
            "tailSlabCnt": 1, 
            "mhMovingAverageParam": 0.3, 
            "wakeUpRebalancerEveryXReqs": wakeup
        }
        for wakeup in wakeUpRebalancerEveryXReqs
    ] + [
        {
            "tailSlabCnt": 1, 
            "mhMovingAverageParam": 0.3, 
            "wakeUpRebalancerEveryXReqs": wakeup,
            "useAdaptiveRebalanceInterval": True
        }
        for wakeup in wakeUpRebalancerEveryXReqs
    ]
}

experiment_configs = []
    
for trace_name, info in traces.items():
    path = info['file_path']

    for allocator, (rebalanceStrategy, rebalanceParamsList) in \
        itertools.product(allocators, rebalanceStrategies.items()):

        for rebalanceParams in rebalanceParamsList:  # Iterate over list of configurations
            for cache_size in info['cache_sizes']:
                cache_config = {
                    "allocator": allocator,
                    "cacheSizeMB": cache_size * 4 + 4,
                    "moveOnSlabRelease": False,
                    "rebalanceStrategy": rebalanceStrategy,
                    "poolRebalanceIntervalSec": 1,
                    **rebalanceParams,
                    **info['extra']
                }
                if 'useAdaptiveRebalanceInterval' in cache_config and trace_name in reset_timings:
                    cache_config['resetIntervalTimings'] = reset_timings[trace_name]
                    
                if 'zstdTrace' in info and info['zstdTrace']:
                    test_config = {
                        "numOps": sys.maxsize,
                        "traceFileName": path,
                        "zstdTrace": True
                    }
                else:
                    test_config = {
                        "numOps": sys.maxsize,
                        "traceFileNames": [path]
                    }
                memo_config = {
                    "trace_name": trace_name,
                    "cache_size": cache_size,
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

def write_config_to_file(experiment_configs, force_overwrite=False):
    config_path = os.path.join(current_dir, 'exp_configs.json')
    if force_overwrite:
        with open(config_path, 'w') as f:
            json.dump(experiment_configs, f, indent=2)
            
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            try:
                existing_configs = json.load(f)
            except json.JSONDecodeError:
                existing_configs = []
    else:
        existing_configs = []

    if not isinstance(existing_configs, list):
        existing_configs = []
        
    def normalize_config(config):
        config_copy = copy.deepcopy(config)
        if "memo_config" in config_copy and "uuid" in config_copy["memo_config"]:
            del config_copy["memo_config"]["uuid"]
        return json.dumps(config_copy, sort_keys=True)

    existing_config_set = {normalize_config(cfg) for cfg in existing_configs}
    new_configs = [cfg for cfg in experiment_configs if normalize_config(cfg) not in existing_config_set]

    if new_configs:
        print(f"Found {len(new_configs)} new configurations to add.")
        updated_configs = existing_configs + new_configs
        with open(config_path, 'w') as f:
            json.dump(updated_configs, f, indent=2)
        print(f"Added {len(new_configs)} new configurations.")
    else:
        print("No new configurations to add.")


write_config_to_file(experiment_configs)