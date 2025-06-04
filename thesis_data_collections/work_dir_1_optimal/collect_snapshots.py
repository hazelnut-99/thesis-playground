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
import re
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed

BASE_FILE_PATH = "/mydata/hongshu/traces/thesis/"

traces = {
    "synth_thesis_static_100": {
        "extra": {
            "allocSizes": [2048, 4096]
        },
        "cache_sizes": [32, 64, 128, 256, 512],
        "file_path": BASE_FILE_PATH + "synth_thesis_static_100.csv"
    },
    "synth_thesis_static_101": {
        "extra": {
            "allocSizes": [2048, 4096]
        },
        "cache_sizes": [32, 64, 128, 256, 512],
        "file_path": BASE_FILE_PATH + "synth_thesis_static_101.csv"
    },
    "synth_thesis_static_102": {
        "extra": {
            "allocSizes": [2048, 4096]
        },
        "cache_sizes": [32, 64, 128, 256, 512],
        "file_path": BASE_FILE_PATH + "synth_thesis_static_102.csv"
    },
    "synth_thesis_static_103": {
        "extra": {
            "allocSizes": [2048, 4096]
        },
        "cache_sizes": [32, 64, 128, 256, 512],
        "file_path": BASE_FILE_PATH + "synth_thesis_static_103.csv"
    },
    "synth_thesis_static_104": {
        "extra": {
            "allocSizes": [2048, 4096]
        },
        "cache_sizes": [32, 64, 128, 256, 512],
        "file_path": BASE_FILE_PATH + "synth_thesis_static_103.csv"
    }
}

allocators = ['LRU2Q']

rebalanceStrategies = {
    "disabled": [{"wakeUpRebalancerEveryXReqs": 5000}]
}

experiment_configs = []
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
                interval = cache_config.get('wakeUpRebalancerEveryXReqs', 100_000)
                uuid = f"{trace_name}_{rebalanceStrategy}_{cache_size}"
                if 'useAdaptiveRebalanceInterval' in cache_config:
                    uuid += '_adaptive_interval'
                if 'useAnomalyDetection' in cache_config:
                    uuid += '_anomaly_detection'
                if interval != 100_000:
                    uuid += f"_{interval}"

                memo_config = {
                    "trace_name": trace_name,
                    "cache_size": cache_size,
                    "uuid": uuid
                }
                
                memo_config.update(info)
            
                full_config = {
                    'cache_config': cache_config,
                    'test_config': test_config,
                    'memo_config': memo_config
                }
                experiment_configs.append(full_config)
                
        
print(f"total number of configs: {len(experiment_configs)}")


def update_base_config(base_config_path, config):
    with open(base_config_path, 'r') as f:
        base_config = json.load(f)
    
    base_config['cache_config'].update(config['cache_config'])
    base_config['test_config'].update(config['test_config'])
    
    return base_config


def extract_json_from_line(pattern, line, label):
    match = re.search(pattern, line)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError as e:
            print(f"Error decoding {label} JSON: {e}")
    return None


def run_cachebench_and_extract_info(config_file, output_json_file):
    command = (
        f"LD_PRELOAD=/mydata/hongshu/libmock_time.so "
        f"/mydata/hongshu/CacheLib/opt/cachelib/bin/cachebench --json_test_config {config_file} "
        f"-progress=50000 --enable_debug_log=true"
    )

    patterns = {
        "snapshots": r'Delta_statistics_logging:\s*(\{.*\})',
        "decision": r'Slab_movement_event:\s*(\{.*\})',
    }

    results = {label: [] for label in patterns}

    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    for line in process.stdout:
        for label, pattern in patterns.items():
            json_obj = extract_json_from_line(pattern, line, label)
            if json_obj:
                results[label].append(json_obj)

    process.wait()

    with open(output_json_file, "w") as json_out:
        json.dump(results, json_out, indent=2)

    return process.returncode


def run_experiment(index, config):
    subdir = 'outcome2/' + config['memo_config']['uuid']
    if os.path.exists(subdir):
        return f"[{index}] Directory {subdir} already exists. Skipping experiment."

    os.makedirs(subdir, exist_ok=True)
    updated_config = update_base_config('base_config.json', config)
    cachebench_config_file_path = os.path.join(subdir, 'config.json')
    with open(cachebench_config_file_path, 'w') as f:
        json.dump(updated_config, f, indent=2)
    output_json_file = os.path.join(subdir, 'out.json')
    
    return_code = run_cachebench_and_extract_info(cachebench_config_file_path, output_json_file)
    if return_code == 0:
        return f"[{index}] Experiment {config['memo_config']['uuid']} finished successfully."
    else:
        return f"[{index}] Experiment {config['memo_config']['uuid']} failed with return code {return_code}."



with ProcessPoolExecutor(max_workers=8) as executor:
    futures = [executor.submit(run_experiment, index, config) for index, config in enumerate(experiment_configs)]
    for future in as_completed(futures):
        try:
            result = future.result()
            print(result)  
        except Exception as e:
            print(f"Experiment generated an exception: {e}")
            