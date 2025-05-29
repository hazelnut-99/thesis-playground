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
    "twitter_cluster_50": {
        "extra": {
            "minAllocSize": 84,
            "maxAllocSize": 184413,
            "allocFactor": 1.5
        },
        "slabs": [1024],
        "file_path": BASE_FILE_PATH + "traces/cluster50.oracleGeneral.zst",
        "zstdTrace": True
    },
    "twitter_cluster_53": {
        "extra": {
            "minAllocSize": 84,
            "maxAllocSize": 40635,
            "allocFactor": 1.5
        },
        "slabs": [256],
        "file_path": BASE_FILE_PATH + "traces/cluster53.oracleGeneral.zst",
        "zstdTrace": True
    },
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
            for cache_size in info['slabs']:
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