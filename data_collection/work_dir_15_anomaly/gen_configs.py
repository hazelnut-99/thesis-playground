# this is for testing out online learning


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
    "synth_static_202": {
        "extra": {
            "allocSizes": [256, 512, 1024, 2048, 4096]
        },
        "cache_sizes": [64, 128, 256],
        "file_path": BASE_FILE_PATH + "traces/synth_static_202.csv"
    },
    "synth_dynamic_400": {
        "extra": {
            "allocSizes": [256, 512, 1024, 2048, 4096]
        },
        "cache_sizes": [64, 128, 256],
        "file_path": BASE_FILE_PATH + "traces/synth_dynamic_400.csv",
        "resetTiming": "39999999"
    },
    "synth_dynamic_401": {
        "extra": {
            "allocSizes": [256, 512, 1024, 2048, 4096]
        },
        "cache_sizes": [64, 128, 256],
        "file_path": BASE_FILE_PATH + "traces/synth_dynamic_401.csv",
        "resetTiming": "26666665,39999998,53333331"
    },
    "synth_dynamic_402": {
        "extra": {
            "allocSizes": [256, 512, 1024, 2048, 4096]
        },
        "cache_sizes": [64, 128, 256],
        "file_path": BASE_FILE_PATH + "traces/synth_dynamic_402.csv",
        "resetTiming": "31999999,39999999,71999999"
    },
    "synth_dynamic_403": {
        "extra": {
            "allocSizes": [256, 512, 1024, 2048, 4096]
        },
        "cache_sizes": [64, 128, 256],
        "file_path": BASE_FILE_PATH + "traces/synth_dynamic_403.csv",
        "resetTiming": "26666665,29090907,31515149,33939391,36363633,38787875,41212117,43636359,46060601,48484843,50909085,53333327"
    },
    "synth_dynamic_500": {
        "extra": {
            "allocSizes": [2048, 4096]
        },
        "cache_sizes": [32, 50],
        "file_path": BASE_FILE_PATH + "traces/synth_dynamic_500.csv",
        "resetTiming": "9999999,19999999,29999999"
    },
    "synth_dynamic_501": {
        "extra": {
            "allocSizes": [2048, 4096]
        },
        "cache_sizes": [32, 50],
        "file_path": BASE_FILE_PATH + "traces/synth_dynamic_501.csv",
        "resetTiming": "4999999,9999999,14999999,19999999,24999999,29999999,34999999"
    },
    "synth_dynamic_502": {
        "extra": {
            "allocSizes": [2048, 4096]
        },
        "cache_sizes": [32, 50],
        "file_path": BASE_FILE_PATH + "traces/synth_dynamic_502.csv",
        "resetTiming": "2499999,4999999,7499999,9999999,12499999,14999999,17499999,19999999,22499999,24999999,27499999,29999999,32499999,34999999,37499999"
    },
    "synth_dynamic_503": {
        "extra": {
            "allocSizes": [2048, 4096]
        },
        "cache_sizes": [32, 50],
        "file_path": BASE_FILE_PATH + "traces/synth_dynamic_503.csv",
        "resetTiming": "999999,1999999,2999999,3999999,4999999,5999999,6999999,7999999,8999999,9999999,10999999,11999999,12999999,13999999,14999999,15999999,16999999,17999999,18999999,19999999,20999999,21999999,22999999,23999999,24999999,25999999,26999999,27999999,28999999,29999999,30999999,31999999,32999999,33999999,34999999,35999999,36999999,37999999,38999999"
    },        
    "synth_dynamic_504": {
        "extra": {
            "allocSizes": [2048, 4096]
        },
        "cache_sizes": [32, 50],
        "file_path": BASE_FILE_PATH + "traces/synth_dynamic_504.csv",
        "resetTiming": "499999,999999,1499999,1999999,2499999,2999999,3499999,3999999,4499999,4999999,5499999,5999999,6499999,6999999,7499999,7999999,8499999,8999999,9499999,9999999,10499999,10999999,11499999,11999999,12499999,12999999,13499999,13999999,14499999,14999999,15499999,15999999,16499999,16999999,17499999,17999999,18499999,18999999,19499999,19999999,20499999,20999999,21499999,21999999,22499999,22999999,23499999,23999999,24499999,24999999,25499999,25999999,26499999,26999999,27499999,27999999,28499999,28999999,29499999,29999999,30499999,30999999,31499999,31999999,32499999,32999999,33499999,33999999,34499999,34999999,35499999,35999999,36499999,36999999,37499999,37999999,38499999,38999999,39499999"
    }
}


allocators = ['LRU2Q']
wakeUpRebalancerEveryXReqs = [i * 1000 for i in [5, 10, 20, 50, 100, 200, 500, 1000]]

rebalanceStrategies = {
    "marginal-hits": [
        {
            "tailSlabCnt": 1, 
            "wakeUpRebalancerEveryXReqs": wakeup,
            "mhMovingAverageParam": 0.3 
        }
        for wakeup in wakeUpRebalancerEveryXReqs
    ] + [
        {
            "tailSlabCnt": 1, 
            "wakeUpRebalancerEveryXReqs": wakeup,
            "useAdaptiveRebalanceInterval": True, 
            "mhMovingAverageParam": 0.3 
        }
        for wakeup in wakeUpRebalancerEveryXReqs
    ] + [
        {
            "tailSlabCnt": 1, 
            "wakeUpRebalancerEveryXReqs": wakeup,
            "useAdaptiveRebalanceInterval": True, 
            "useAnomalyDetection": True,
            "ewmaL": 3.5,
            "mhMovingAverageParam": 0.3 
        }
        for wakeup in wakeUpRebalancerEveryXReqs
    ] + [
        {
            "tailSlabCnt": 1, 
            "wakeUpRebalancerEveryXReqs": wakeup,
            "useAdaptiveRebalanceInterval": True, 
            "useAnomalyDetection": True,
            "ewmaL": 4,
            "mhMovingAverageParam": 0.3 
        }
        for wakeup in wakeUpRebalancerEveryXReqs
    ] + [
        {
            "tailSlabCnt": 1, 
            "wakeUpRebalancerEveryXReqs": wakeup,
            "useAdaptiveRebalanceInterval": True, 
            "useAnomalyDetection": True,
            "ewmaL": 5,
            "mhMovingAverageParam": 0.3 
        }
        for wakeup in wakeUpRebalancerEveryXReqs
    ]
    + [
        {
            "tailSlabCnt": 1, 
            "wakeUpRebalancerEveryXReqs": wakeup,
            "useAdaptiveRebalanceInterval": True, 
            "manualReset": True,
            "mhMovingAverageParam": 0.3 
        }
        for wakeup in wakeUpRebalancerEveryXReqs
    ],
    "hits": [{"rebalanceDiffRatio": 0.1, "wakeUpRebalancerEveryXReqs": wakeup} for wakeup in wakeUpRebalancerEveryXReqs],
    "tail-age": [{"rebalanceDiffRatio": 0.25, "wakeUpRebalancerEveryXReqs": wakeup} for wakeup in wakeUpRebalancerEveryXReqs],
    "disabled": [{"wakeUpRebalancerEveryXReqs": 5000}]
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
                    "lruRefreshSec": 0,
                    "cacheSizeMB": cache_size * 4 + 4,
                    "moveOnSlabRelease": False,
                    "rebalanceStrategy": rebalanceStrategy,
                    "poolRebalanceIntervalSec": 1,
                    **rebalanceParams,
                    **info['extra']
                }
                if 'manualReset' in rebalanceParams:
                    if "resetTiming" in info:
                        cache_config['resetIntervalTimings'] = info['resetTiming']
                    else:
                        continue
                
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