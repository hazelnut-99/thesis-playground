import json
import os
import subprocess
import uuid
import random
from concurrent.futures import ProcessPoolExecutor, as_completed

base_config_path = 'base_config.json'
cachebench_path = '/users/Hongshu/CacheLib/opt/cachelib/bin/cachebench'
test_configs_path = 'w06_trace_test_configs.json'

# Load test configurations from JSON file
with open(test_configs_path, 'r') as f:
    test_configs = json.load(f)

random.shuffle(test_configs)

print(f"total number of configs: {len(test_configs)}")

with open(base_config_path, 'r') as f:
    base_config = json.load(f)

def run_test(config, idx):
    test_config = base_config.copy()
    test_config['cache_config'].update(config)

    test_dir = 'outcome_w06/' + str(uuid.uuid4())
    os.makedirs(test_dir)

    # Dump the test_config to a JSON file
    config_path = os.path.join(test_dir, 'config.json')
    with open(config_path, 'w') as f:
        json.dump(test_config, f, indent=2)

    std_out_path = os.path.join(test_dir, 'std.out')
    
    # Log progress
    print(f"Running config {idx}")

    with open(std_out_path, 'w') as std_out:
        result = subprocess.run([cachebench_path, '--json_test_config', config_path, '-report_ac_memory_usage_stats=human_readable'], stdout=std_out, stderr=subprocess.STDOUT)

    print(f"Test completed for configuration: {config}. Output written to {std_out_path}, return code: {result.returncode}")

# Run tests in parallel using ProcessPoolExecutor
with ProcessPoolExecutor(max_workers=20) as executor:
    futures = [executor.submit(run_test, config, idx) for idx, config in enumerate(test_configs, start=1)]
    for future in as_completed(futures):
        future.result()  # This will raise an exception if the test failed