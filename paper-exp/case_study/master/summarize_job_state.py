import json
import os
from collections import defaultdict, Counter

with open("scheduler_state_new.json") as f:
    data = json.load(f)

summary = defaultdict(Counter)

for entry in data:
    uuid = entry.get("uuid", "")
    status = entry.get("status", "")
    trace_name = uuid.split("-", 1)[0]
    summary[trace_name][status] += 1

print(f"{'Trace Name':<25} {'todo':>6} {'running':>8} {'finished':>9} {'failed':>7}")
print("-" * 60)
for trace_name, counts in sorted(summary.items()):
    print(f"{trace_name:<25} {counts.get('todo',0):>6} {counts.get('running',0):>8} {counts.get('finished',0):>9} {counts.get('failed',0):>7}")

allocator_counter = Counter()

for entry in data:
    uuid = entry.get("uuid", "")
    trace_name = uuid.split("-", 1)[0]
    status = entry.get("status", "")
    if status == "failed" and uuid:
        config_path = os.path.join("../work_dir_new", uuid, "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path) as cf:
                    config = json.load(cf)
                allocator = config.get("cache_config", {}).get("allocator", "UNKNOWN")
                rebalance_strategy = config.get("cache_config", {}).get("rebalanceStrategy", "UNKNOWN")
                allocator_counter[(trace_name, allocator, rebalance_strategy)] += 1
            except Exception as e:
                allocator_counter[("ERROR", "ERROR", "ERROR")] += 1

print(f"{'Trace Name':<25} {'Allocator':<30} {'Failed Jobs':>12}")
print("-" * 70)
for (trace_name, allocator, rs), count in sorted(allocator_counter.items(), key=lambda x: (x[0][0], x[0][1], x[0][2])):
    print(f"{trace_name:<25} {allocator:<30} {rs:<20} {count:>12}")
    
"""
read all subdirs under ../work_dir_new" read meta.json wsr field and trace_name field
group by wsr count number of distinct trace_names
"""

work_dir = "../work_dir_new"

wsr_to_traces = defaultdict(set)

for subdir in os.listdir(work_dir):
    meta_path = os.path.join(work_dir, subdir, "meta.json")
    if os.path.exists(meta_path):
        try:
            with open(meta_path) as f:
                meta = json.load(f)
            wsr = meta.get("wsr")
            trace_name = meta.get("trace_name")
            if not trace_name.startswith("twitter"):
                continue
            if wsr is not None and trace_name is not None:
                wsr_to_traces[wsr].add(trace_name)
        except Exception as e:
            pass  # skip broken files

print(f"{'wsr':<10} {'n_traces':>10}")
print("-" * 25)
for wsr in sorted(wsr_to_traces, key=lambda x: float(x)):
    print(f"{wsr:<10} {len(wsr_to_traces[wsr]):>10}")