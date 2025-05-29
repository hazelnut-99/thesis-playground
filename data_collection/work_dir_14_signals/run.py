"""

Static 200
Dynamic 400
Dynamic 500
Meta
Twitter cluster 16

Disabled
Rebalancer
Marginal-hits adaptive interval

"""
import json
import uuid
import itertools
import sys
import os
import subprocess
import re
from concurrent.futures import ProcessPoolExecutor, as_completed

BASE_FILE_PATH = "/mydata/hongshu/"

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
        "file_path": BASE_FILE_PATH + "traces/synth_dynamic_400.csv"
    },
    "synth_dynamic_401": {
        "extra": {
            "allocSizes": [256, 512, 1024, 2048, 4096]
        },
        "cache_sizes": [64, 128, 256],
        "file_path": BASE_FILE_PATH + "traces/synth_dynamic_401.csv"
    },
    "synth_dynamic_402": {
        "extra": {
            "allocSizes": [256, 512, 1024, 2048, 4096]
        },
        "cache_sizes": [64, 128, 256],
        "file_path": BASE_FILE_PATH + "traces/synth_dynamic_402.csv"
    },
    "synth_dynamic_403": {
        "extra": {
            "allocSizes": [256, 512, 1024, 2048, 4096]
        },
        "cache_sizes": [64, 128, 256],
        "file_path": BASE_FILE_PATH + "traces/synth_dynamic_403.csv"
    },
    "synth_dynamic_500": {
        "extra": {
            "allocSizes": [2048, 4096]
        },
        "cache_sizes": [32],
        "file_path": BASE_FILE_PATH + "traces/synth_dynamic_500.csv"
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
    },
    "wiki_2019_t": {
        "extra": {
            "minAllocSize": 72,
            "maxAllocSize": 1048676,
            "allocFactor": 1.25
        },
        "cache_sizes": [2048],
        "file_path": BASE_FILE_PATH + "traces/wiki_2019t.oracleGeneral.zst",
        "zstdTrace": True
    },
    "twitter_cluster_52_sample": {
        "extra": {
            "allocSizes": [72, 112, 168, 256, 384, 576, 864, 1296, 1944, 2920, 4384, 6304]
        },
        "cache_sizes": [256, 512, 1024],
        "file_path": BASE_FILE_PATH + "traces/cluster52.oracleGeneral.sample10.zst",
        "zstdTrace": True
    },
    "meta_2024_full": {
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
        "cache_sizes": [512],
        "file_path": BASE_FILE_PATH + "traces/202401_kv_traces_all_sort.csv.oracleGeneral.zst",
        "zstdTrace": True
    }
}

rebalanceStrategies = {
    "marginal-hits": [
        {
            "tailSlabCnt": 1, 
            "mhMovingAverageParam": 0.3, 
            "wakeUpRebalancerEveryXReqs": 100_000
        }
    ] + [
        {
            "tailSlabCnt": 1, 
            "mhMovingAverageParam": 0.3, 
            "wakeUpRebalancerEveryXReqs": 100_000,
            "useAdaptiveRebalanceInterval": True
        }
    ]+ [
        {
            "tailSlabCnt": 1, 
            "mhMovingAverageParam": 0.3, 
            "wakeUpRebalancerEveryXReqs": 100_000,
            "useAdaptiveRebalanceInterval": True,
            "useAnomalyDetection": True
        }
    ],
    "disabled": [{"wakeUpRebalancerEveryXReqs": 100_000}]
}

allocators = ['LRU2Q']

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
                memo_config = {
                    "trace_name": trace_name,
                    "cache_size": cache_size,
                    "uuid": f"{trace_name}_{rebalanceStrategy}_{cache_size}" \
                            f"{'_adaptive_interval' if 'useAdaptiveRebalanceInterval' in cache_config else ''}" \
                            f"{'_anomaly_detection' if 'useAnomalyDetection' in cache_config else ''}"
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
    subdir = 'outcome/' + config['memo_config']['uuid']
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
            