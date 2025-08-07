"""
prepare for experiment configs, each config is a subdirectory under work_dir
each subdirectory contains:
- config.json, the config for cachebench, we should generate this config first, 
    use uuid = trace_name + md5(config) as name of the subdir
- meta_data.json
    contains 
        uuid
        memory_requirement in mb
        cpu_requirement in cores
        trace_file it relies on to run
        tag_name
        slab_size
- return code, 0 success, non-zero fails, doesn't exist means haven't run or havne't finished yet
- after running, there will be a result.json in the subdir
"""



import itertools
import os
import json
import copy
import sys
import math
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from const import *
from util import dict_hash
import shutil


import pandas as pd

def read_trace_info_csv(csv_path):
    """
    Reads trace_info.csv and returns a dictionary:
    key = trace_name, value = dict of other fields with correct types
    """
    df = pd.read_csv(csv_path)
    df = df.convert_dtypes()  # Use best possible dtypes
    trace_dict = {}
    for _, row in df.iterrows():
        row_dict = row.to_dict()
        trace_name = row_dict.pop('trace_name')
        trace_dict[trace_name] = row_dict
    return trace_dict


allocators = [
    {
        "lru2qHotPct": 100, # placeholders for simple2q
        "lru2qColdPct": 0,
        "allocator": "SIMPLE2Q",
        "rebalanceOnRecordAccess": True,
    },
    {
        "lru2qHotPct": 30, # this is the real 2q
        "lru2qColdPct": 30,
        "allocator": "LRU2Q",
        "rebalanceOnRecordAccess": True,
    },
    {
        "lru2qHotPct": 30, 
        "lru2qColdPct": 30,
        "allocator": "LRU2Q",
        "rebalanceOnRecordAccess": True,
        "countColdTailHitsOnly": True
    },
    {
        "lru2qHotPct": 30, 
        "lru2qColdPct": 30,
        "allocator": "LRU2Q",
        "rebalanceOnRecordAccess": False,
        "countColdTailHitsOnly": True
    },
    {
        'allocator': 'TINYLFU'
    },
    {
        'allocator': 'TINYLFUTail'
    }  
]

lru2q_real = allocators[1]
lru2q_real_coldtail = allocators[2]
special_lru2q_configs = [lru2q_real, lru2q_real_coldtail]
special_strategies = {"marginal-hits-old", "marginal-hits-new"}


trace_names = ['meta_202210_kv'] 
working_set_ratios = [0.001, 0.002, 0.004, 0.01, 0.02, 0.04, 0.1, 0.2, 0.4]


default_interval = 50_000
rebalance_intervals = [default_interval]

default_decay = 0.3
default_initial_threshold = 2
default_additive_step = 2
default_emr_low = 0.5
default_emr_high = 0.95

thresholds = [2, 5, 10, 20, 50, 100, 200, 500, 1000]

cache_configs = {
    "marginal-hits-new": [
        {
            "wakeUpRebalancerEveryXReqs": default_interval,
            "mhMovingAverageParam": default_decay,
            "mhOnlyUpdateHitIfRebalance": False,
            "minRequestsObserved": default_interval,
            "mhMinDiff": thresh, 
            "mhMinDiffRatio": 0.00,
            "thresholdAIADStep": 2,
            "thesholdMIMDFactor": 2.0,
            "emrLow": default_emr_low,
            "emrHigh": default_emr_high,
            "thresholdAI": False,
            "thresholdAD": False,
            "thresholdMI": False,
            "thresholdMD": False,
        }
        for thresh in thresholds
    ] 
}



def generate_configs(
    trace_info_csv="../../trace_info.csv",
    base_config_path="base_config.json",
    work_dir=f"{HOME_DIR}/thesis-playground/paper-exp/efficiency/work_dir_meta_fixed_thresh",
    force_delete=False
):
    total_confs = 0
    new_confs = 0
    deleted_confs = 0
    intended_uuids = set()

    # Create work_dir if it doesn't exist
    if not os.path.exists(work_dir):
        os.makedirs(work_dir)
        print(f"Created work directory: {work_dir}")

    trace_info_dict = read_trace_info_csv(trace_info_csv)

    for allocator_config, (trace_name, trace_info) in itertools.product(allocators, trace_info_dict.items()):
        if trace_name not in trace_names:
            continue
        download_path = trace_info["download_path"]
        file_name = trace_info["file_name"]
        slab_size = int(trace_info["slab_size"])
        wss = float(trace_info["wss"])

        with open(base_config_path, "r") as f:
            base_config = json.load(f)

        # --- Begin: Restrict combinations as requested ---
        for wsr in working_set_ratios:
            for rebalanceStrategy, rebalanceParamsList in cache_configs.items():
                # Special LRU2Q configs: only combine with special strategies
                if allocator_config in special_lru2q_configs:
                    if rebalanceStrategy not in special_strategies:
                        # For non-special strategies, only use the first LRU2Q config
                        if allocator_config != lru2q_real:
                            continue
                        # Only allow the first LRU2Q config for other strategies
                        if rebalanceStrategy not in VALID_ALLOCATOR_REBALANCE_COMBINATIONS.get(allocator_config["allocator"], set()):
                            continue
                    # For special strategies, allow both special configs
                else:
                    # For other allocators, use normal validation
                    if rebalanceStrategy not in VALID_ALLOCATOR_REBALANCE_COMBINATIONS.get(allocator_config["allocator"], set()):
                        continue

                for param in rebalanceParamsList:
                    cachebench_config = copy.deepcopy(base_config)
                    # cache config
                    cachebench_config["cache_config"]["rebalanceStrategy"] = rebalanceStrategy
                    raw_size = wss * wsr * 1024
                    slab_cnt = int(math.ceil(raw_size / slab_size))
                    num_slab_for_headers = (7 * slab_cnt + slab_size * 1024 - 1) // (slab_size * 1024)
                    total_slabs = slab_cnt + num_slab_for_headers
                    # potentially if total_slab fewer than the number of classes, skip it.
                    if slab_cnt < trace_info["num_slab_classes"]:
                        print(f"Trace {trace_name} with slab size {slab_size} has fewer slabs ({total_slabs}) than classes ({trace_info['num_slab_classes']}). Skipping.")
                        continue
                    rounded_size = total_slabs * slab_size
                    cachebench_config["cache_config"]["cacheSizeMB"] = rounded_size
                    cachebench_config["cache_config"]["maxAllocSize"] = slab_size * 1024 * 1024
                    cachebench_config["cache_config"].update(param)
                    cachebench_config["cache_config"].update(allocator_config)

                    # test_config
                    cachebench_config["test_config"]["traceFileName"] = f"{TRACE_FILE_PATH}/{file_name}"
                    cachebench_config["test_config"]["numOps"] = int(trace_info["number_of_requests"])

                    uuid = f"{trace_name}-{dict_hash(cachebench_config)}"
                    intended_uuids.add(uuid)

                    meta_config = {
                        "trace_name": trace_name,
                        "uuid": uuid,
                        "memory_requirement": cachebench_config["cache_config"]["cacheSizeMB"] * 1.1,
                        "cpu_requirement": 2.5,  # reserve 3 cores per task
                        "download_path": f"{WGET_PATH}/{download_path}",
                        "trace_file": f"{TRACE_FILE_PATH}/{file_name}",
                        "slab_size": slab_size,
                        "purpose": "efficiency",
                        "wsr": wsr,
                        "slab_cnt": slab_cnt,
                    }
                    
                    meta_config.update(trace_info)
                    meta_config["slab_size"] = slab_size

                    subdir = os.path.join(work_dir, uuid)
                    total_confs += 1
                    if os.path.exists(subdir):
                        print(f"Directory {subdir} exists, skipping.")
                        continue
                    new_confs += 1
                    os.makedirs(subdir)
                    with open(os.path.join(subdir, "config.json"), "w") as f:
                        json.dump(cachebench_config, f, indent=2)
                    with open(os.path.join(subdir, "meta.json"), "w") as f:
                        json.dump(meta_config, f, indent=2)
        # --- End: Restrict combinations as requested ---

    # Delete subdirs not in intended_uuids if force_delete is True
    if force_delete:
        for sub in os.listdir(work_dir):
            sub_path = os.path.join(work_dir, sub)
            if os.path.isdir(sub_path) and sub not in intended_uuids:
                print(f"Deleting obsolete config directory: {sub_path}")
                shutil.rmtree(sub_path)
                deleted_confs += 1

    print(f"Total configs: {total_confs}")
    print(f"New configs created: {new_confs}")
    print(f"Deleted obsolete configs: {deleted_confs}")


generate_configs(force_delete=True)