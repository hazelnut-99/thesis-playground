"""
cluster_17, wsr = 0.1, LRU
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
    trace_dict = {
        "synth_static_202": {
            "download_path": "placeholder",
            "file_name": "synth_static_202.csv",
            "slab_size": 4,
            "wss": 1.9043,
            "num_slab_classes": 5,
            "number_of_requests": 80000000,
            "allocSizes": [256, 512, 1024, 2048, 4096],
            "slab_cnt": [32, 64, 128, 256]
        }
    }
    return trace_dict


allocators = [
    {
        "lru2qHotPct": 100, # placeholders for simple2q
        "lru2qColdPct": 0,
        "allocator": "SIMPLE2Q",
        "rebalanceOnRecordAccess": True,
    }
]



trace_names = ["synth_static_202"]


rebalance_intervals = [50_000]
placeholder_interval = 50_000
cache_configs = {
    "marginal-hits-old": [
        {
            "wakeUpRebalancerEveryXReqs": wakeup,
            "mhMovingAverageParam": 0.3, 
        }
        for wakeup in rebalance_intervals
    ], 
    "marginal-hits-new": [
        {
            "wakeUpRebalancerEveryXReqs": wakeup,
            "mhMovingAverageParam": 0.3,
            "mhOnlyUpdateHitIfRebalance": True,
            "minRequestsObserved": wakeup,
            "maxDecayInterval": wakeup,
            "mhMinDiff": 2, 
            "mhMinDiffRatio": 0.00,
            "emrLow": 0.5,
            "emrHigh": 0.95,
            "thresholdAI": True,
            "thresholdAD": False,
            "thresholdMI": False,
            "thresholdMD": True,
        }
        for wakeup in rebalance_intervals
    ],
    "disabled": [{"wakeUpRebalancerEveryXReqs": placeholder_interval}],
    "hits": [{"rebalanceDiffRatio": 0.1, "wakeUpRebalancerEveryXReqs": wakeup} for wakeup in rebalance_intervals],
    "eviction-rate": [{"rebalanceDiffRatio": 0.1, "wakeUpRebalancerEveryXReqs": wakeup} for wakeup in rebalance_intervals],
    "tail-age": [{"rebalanceDiffRatio": diffRatio, "wakeUpRebalancerEveryXReqs": wakeup} 
                 for diffRatio, wakeup in itertools.product([0.25], rebalance_intervals)],
    "free-mem": [{"wakeUpRebalancerEveryXReqs": wakeup} for wakeup in rebalance_intervals],
    #"lama": [{"wakeUpRebalancerEveryXReqs": wakeup, "lamaMinThreshold": 0.00001} for wakeup in rebalance_intervals]
}



def generate_configs(
    trace_info_csv="../../trace_info.csv",
    base_config_path="base_config.json",
    work_dir=f"{HOME_DIR}/thesis-playground/paper-exp/case_study/work_dir_synthetic_thesis",
    force_delete=False
):
    total_confs = 0
    new_confs = 0
    deleted_confs = 0
    intended_uuids = set()

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
        for slab_cnt in trace_info["slab_cnt"]:
            for rebalanceStrategy, rebalanceParamsList in cache_configs.items():
                for param in rebalanceParamsList:
                    cachebench_config = copy.deepcopy(base_config)
                    # cache config
                    cachebench_config["cache_config"]["rebalanceStrategy"] = rebalanceStrategy
                    cachebench_config["cache_config"]["cacheSizeMB"] = slab_cnt * 4 + 4
                    del cachebench_config["cache_config"]["minAllocSize"]
                    del cachebench_config["cache_config"]["allocFactor"]
                    cachebench_config["cache_config"]["allocSizes"] = trace_info["allocSizes"]
                    cachebench_config["cache_config"].update(param)
                    cachebench_config["cache_config"].update(allocator_config)

                    # test_config
                    cachebench_config["test_config"]["traceFileName"] = f"{TRACE_FILE_PATH}/{file_name}"
                    cachebench_config["test_config"]["numOps"] = int(trace_info["number_of_requests"])
                    cachebench_config["test_config"]["zstdTrace"] = False

                    uuid = f"{trace_name}-{dict_hash(cachebench_config)}"
                    intended_uuids.add(uuid)

                    meta_config = {
                        "trace_name": trace_name,
                        "uuid": uuid,
                        "memory_requirement": cachebench_config["cache_config"]["cacheSizeMB"] + 100,
                        "cpu_requirement": 2.5,  
                        "download_path": f"{WGET_PATH}/{download_path}",
                        "trace_file": f"{TRACE_FILE_PATH}/{file_name}",
                        "slab_size": slab_size,
                        "purpose": "efficiency",
                        "slab_cnt": slab_cnt,
                    }
                    
                    meta_config.update(trace_info)

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