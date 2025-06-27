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
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from const import *
from util import dict_hash

import csv

def read_trace_info_csv(csv_path):
    """
    Reads trace_info.csv and returns a dictionary:
    key = trace_name, value = dict of other fields
    """
    trace_dict = {}
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            trace_name = row.pop('trace_name')
            trace_dict[trace_name] = row
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
        'allocator': 'TINYLFU'
    } 
]

#trace_names = ['meta_202312_kv', 'meta_meta_kvcache', 'meta_202210_kv', 'meta_202206_kv', 'meta_202401_kv']
trace_names = ['meta_202401_kv']
working_set_ratios = [0.05]

rebalance_intervals = [10_000, 100_000]
placeholder_interval = 1000
cache_configs = {
    "marginal-hits-old": [
        {
            "wakeUpRebalancerEveryXReqs": wakeup,
            "mhMovingAverageParam": 0.3, 
        }
        for wakeup in rebalance_intervals
    ] + 
    # interval mimd
    [
        {
            "wakeUpRebalancerEveryXReqs": wakeup,
            "useAdaptiveRebalanceIntervalV2": True, 
            "mhMovingAverageParam": 0.3 
        }
        for wakeup in rebalance_intervals
    ],
    "marginal-hits-new": [
        {
            "wakeUpRebalancerEveryXReqs": wakeup,
            "mhMovingAverageParam": 0.0,
            "mhOnlyUpdateHitIfRebalance": True,
            "mhMinDiff": 2, 
            "mhMinDiffRatio": 0.05,
            "thresholdAI": False,
            "thresholdAD": False,
            "thresholdMI": True,
            "thresholdMD": True,
        }
        for wakeup in rebalance_intervals
    ],
    "disabled": [{"wakeUpRebalancerEveryXReqs": placeholder_interval}],
    "hits": [{"rebalanceDiffRatio": 0.1, "wakeUpRebalancerEveryXReqs": wakeup} for wakeup in rebalance_intervals],
    "tail-age": [{"rebalanceDiffRatio": 0.25, "wakeUpRebalancerEveryXReqs": wakeup} for wakeup in rebalance_intervals],
    "free-mem": [{"wakeUpRebalancerEveryXReqs": wakeup} for wakeup in rebalance_intervals],
}

import shutil

def generate_configs(
    trace_info_csv="../../trace_info.csv",
    base_config_path="base_config.json",
    work_dir=f"{HOME_DIR}/thesis-playground/paper-exp/efficiency/work_dir",
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

        for wsr, (rebalanceStrategy, rebalanceParamsList) in itertools.product(working_set_ratios, cache_configs.items()):
            if allocator_config["allocator"] not in ("SIMPLE2Q", "LRU2Q") and rebalanceStrategy in ("marginal-hits-old", "marginal-hits-new"):
                continue
            for param in rebalanceParamsList:
                cachebench_config = copy.deepcopy(base_config)
                # cache config
                cachebench_config["cache_config"]["rebalanceStrategy"] = rebalanceStrategy
                cachebench_config["cache_config"]["cacheSizeMB"] = int(wss * wsr * 1024) + 4
                cachebench_config["cache_config"]["maxAllocSize"] = slab_size * 1024 * 1024
                cachebench_config["cache_config"].update(param)
                cachebench_config["cache_config"].update(allocator_config)

                # test_config
                cachebench_config["test_config"]["traceFileName"] = f"{TRACE_FILE_PATH}/{file_name}"
                cachebench_config["test_config"]["zstdTrace"] = trace_info["zstdTrace"]
                cachebench_config["test_config"]["numOps"] = int(trace_info["number_of_requests"])

                uuid = f"{trace_name}-{dict_hash(cachebench_config)}"
                intended_uuids.add(uuid)

                meta_config = {
                    "trace_name": trace_name,
                    "uuid": uuid,
                    "memory_requirement": cachebench_config["cache_config"]["cacheSizeMB"],
                    "cpu_requirement": 6,  # reserve 6 cores reserved per task
                    "download_path": f"{WGET_PATH}/{download_path}",
                    "trace_file": f"{TRACE_FILE_PATH}/{file_name}",
                    "slab_size": slab_size,
                    "purpose": "efficiency",
                    "wsr": wsr,
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