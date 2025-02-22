import json
import os
import subprocess
import uuid
from itertools import product

base_config_path = 'base_config.json'
cachebench_path = '/users/Hongshu/CacheLib/opt/cachelib/bin/cachebench'


rebalance_configs = [
    {"rebalanceStrategy": "default"},
    {"rebalanceStrategy": "lru-tail", "rebalanceDiffRatio": 0.25},
    {"rebalanceStrategy": "free-mem"},
    {"rebalanceStrategy": "marginal-hits"},
    {"rebalanceStrategy": "hits", "rebalanceDiffRatio": 0.1},
    {"rebalanceStrategy": "random"},
]

cache_size_configs = [
    {"cacheSizeMB": 256},
    {"cacheSizeMB": 512},
    {"cacheSizeMB": 1024},
    {"cacheSizeMB": 2048},
    {"cacheSizeMB": 8192},
    {"cacheSizeMB": 16384},
    {"cacheSizeMB": 32768},
    {"cacheSizeMB": 65536},
]

cache_eviction_configs = [
    {"allocator": "LRU"},
    {"allocator": "LRU2Q"},
    {"allocator": "TINYLFU"}
]


"""
Tail hits tracking cannot be enabled on MMTypes except MM2Q.
"""
test_configs = [
    {**rebalance, **cache_size, **eviction}
    for rebalance, cache_size, eviction in product(rebalance_configs, cache_size_configs, cache_eviction_configs)
    if not (rebalance["rebalanceStrategy"] == "marginal-hits" and eviction["allocator"] != "LRU2Q")
]

with open(base_config_path, 'r') as f:
    base_config = json.load(f)

for config in test_configs:
    test_config = base_config.copy()
    test_config['cache_config'].update(config)

    test_dir = 'outcome/' + str(uuid.uuid4())
    os.makedirs(test_dir)

    config_path = os.path.join(test_dir, 'config.json')
    with open(config_path, 'w') as f:
        json.dump(test_config, f, indent=2)

    std_out_path = os.path.join(test_dir, 'std.out')
    with open(std_out_path, 'w') as std_out:
        subprocess.run([cachebench_path, '--json_test_config', config_path], stdout=std_out, stderr=subprocess.STDOUT)

    print(f"Test completed for configuration: {config}. Output written to {std_out_path}")