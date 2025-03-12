import json
import os
from itertools import product

base_config_path = 'base_config.json'
cachebench_path = '/users/Hongshu/CacheLib/opt/cachelib/bin/cachebench'


rebalance_strategies = {
    "default": [{}],
    "lru-tail": [{"rebalanceDiffRatio": 0.25}],
    "free-mem": [{}],
    "marginal-hits": [{}],
    "hits": [{"rebalanceDiffRatio": 0.1}]
}



cache_size_configs = [
    {"cacheSizeMB": 256},
    {"cacheSizeMB": 512},
    {"cacheSizeMB": 1024},
    {"cacheSizeMB": 2048},
    {"cacheSizeMB": 8192},
    {"cacheSizeMB": 16384},
    {"cacheSizeMB": 32768},
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
    for rebalance, cache_size, eviction in product(rebalance_strategies, cache_size_configs, cache_eviction_configs)
    if "rebalanceStrategy" in rebalance and not (rebalance["rebalanceStrategy"] == "marginal-hits" and eviction["allocator"] != "LRU2Q")
] 




# cache_sizes = [256, 512, 1024, 2048]
# # lru-tail
# rebalanceDiffRatio = [0.1, 0.25, 0.5]
# ltaMinTailAgeDifference = [3, 5, 10, 100]
# rebalanceMinSlabs = [0, 1, 2]
# ltaNumSlabsFreeMem = [1, 3, 5]
# ltaSlabProjectionLength = [0, 1, 2]

# lru_tail_configs = [
#     {
#         "rebalanceStrategy": "lru-tail",
#         "rebalanceDiffRatio": r,
#         "ltaMinTailAgeDifference": t,
#         "rebalanceMinSlabs": s,
#         "ltaNumSlabsFreeMem": n,
#         "ltaSlabProjectionLength": p,
#         "allocator": "LRU",
#         "poolRebalanceIntervalSec": 1,
#         "allocFactor": 1.25,
#         "cacheSizeMB": c,
#         "test_group": 'lru-tail-configs'
#     }
#     for r, t, s, n, p, c in product(rebalanceDiffRatio, ltaMinTailAgeDifference, rebalanceMinSlabs, ltaNumSlabsFreeMem, ltaSlabProjectionLength, cache_sizes)
# ]

# # hits
# rebalanceDiffRatio = [0.05, 0.1, 0.25]
# hpsMinDiff = [10, 50, 100, 200]
# rebalanceMinSlabs = [0, 1, 2]
# hpsNumSlabsFreeMem = [1, 3, 5]
# hpsMinLruTailAge = [0, 1, 2]
# hpsMaxLruTailAge = [0, 1, 2]

# hits_configs = [
#     {
#         "rebalanceStrategy": "hits",
#         "rebalanceDiffRatio": a,
#         "hpsMinDiff": b,
#         "rebalanceMinSlabs": c,
#         "hpsNumSlabsFreeMem": d,
#         "hpsMinLruTailAge": e,
#         "hpsMaxLruTailAge": f,
#         "allocator": "LRU",
#         "poolRebalanceIntervalSec": 1,
#         "allocFactor": 1.25,
#         "cacheSizeMB": g,
#         "test_group": 'hits-configs'
#     }
#     for a, b, c, d, e, f, g in product(rebalanceDiffRatio, hpsMinDiff, rebalanceMinSlabs, hpsNumSlabsFreeMem, hpsMinLruTailAge, hpsMaxLruTailAge, cache_sizes)
# ]

# # marginal hits
# rebalanceMinSlabs = [0, 1, 2]
# mhMovingAverageParam = [0.3, 0.5]
# mhMaxFreeMemSlabs = [0, 1, 2]

# marginal_hits_configs = [
#     {
#         "rebalanceStrategy": "marginal-hits",
#         "rebalanceMinSlabs": a,
#         "mhMovingAverageParam": b,
#         "mhMaxFreeMemSlabs": c,
#         "allocator": "LRU2Q",
#         "poolRebalanceIntervalSec": 1,
#         "allocFactor": 1.25,
#         "cacheSizeMB": d,
#         "test_group": 'marginal-hit-configs'
#     }
#     for a, b, c, d in product(rebalanceMinSlabs, mhMovingAverageParam, mhMaxFreeMemSlabs, cache_sizes)
# ]

# # free mem
# rebalanceMinSlabs = [0, 1, 2]
# fmNumFreeSlabs = [1, 3, 5]
# fmMaxUnAllocatedSlabs = [0, 10, 1000, 1500]

# free_mem_configs = [
#     {
#         "rebalanceStrategy": "free-mem",
#         "rebalanceMinSlabs": a,
#         "fmNumFreeSlabs": b,
#         "fmMaxUnAllocatedSlabs": c,
#         "allocator": "TINYLFU",
#         "poolRebalanceIntervalSec": 1,
#         "allocFactor": 1.25,
#         "cacheSizeMB": d,
#         "test_group": 'free-mem'
#     }
#     for a, b, c, d in product(rebalanceMinSlabs, fmNumFreeSlabs, fmMaxUnAllocatedSlabs, cache_sizes)
# ]

# # random
# rebalanceMinSlabs = [0, 1, 2]

# random_configs = [
#     {
#         "rebalanceStrategy": "random",
#         "rebalanceMinSlabs": a,
#         "allocator": "LRU",
#         "poolRebalanceIntervalSec": 1,
#         "allocFactor": 1.25,
#         "cacheSizeMB": b,
#         "test_group": 'random-configs'
#     }
#     for a, b in product(rebalanceMinSlabs, cache_sizes)
# ]

# test_configs.extend(lru_tail_configs)
# test_configs.extend(hits_configs)
# test_configs.extend(marginal_hits_configs)
# test_configs.extend(free_mem_configs)
# test_configs.extend(random_configs)

print(f"total number of configs: {len(test_configs)}")

with open('w06_configs_0303.json', 'w') as f:
    json.dump(test_configs, f, indent=2)