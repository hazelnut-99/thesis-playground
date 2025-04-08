import os
import json
import re
import subprocess

def run_cachebench_and_extract_rebalance_states(config_file, output_file, output_json_file):
    command = (
        f"LD_PRELOAD=/users/Hongshu/libmock_time.so "
        f"/users/Hongshu/CacheLib/opt/cachelib/bin/cachebench --json_test_config {config_file} "
        f"-progress=50000 --enable_debug_log=true"
    )

    json_list = []

    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    for line in process.stdout:
        match = re.search(r'Rebalance_states_logging:\s*(\{.*\})', line)
        if match:
            try:
                json_obj = json.loads(match.group(1))
                json_list.append(json_obj)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")

    process.wait()
    with open(output_json_file, "w") as json_out:
        json.dump(json_list, json_out, indent=2)

    return process.returncode

def run_cachebench(config_file, output_file, output_json_file):
    with open(config_file, 'r') as f:
        config_content = json.load(f)
    
    if config_content["test_config"]["useTraceTimer"]:
        command = [
            "LD_PRELOAD=/users/Hongshu/libmock_time.so",
            "/users/Hongshu/CacheLib/opt/cachelib/bin/cachebench",
            "--json_test_config", config_file,
            "-progress=50000",
            "--dump_result_json_file", output_json_file
        ]
    else:
        command = [
            "/users/Hongshu/CacheLib/opt/cachelib/bin/cachebench",
            "--json_test_config", config_file,
            "-progress=50000",
            "--dump_result_json_file", output_json_file
        ]
    
    with open(output_file, 'w') as out:
        result = subprocess.run(" ".join(command), shell=True, stdout=out, stderr=subprocess.STDOUT)
    
    return result.returncode

def update_base_config(base_config_path, config):
    with open(base_config_path, 'r') as f:
        base_config = json.load(f)
    
    base_config['cache_config'].update(config['cache_config'])
    base_config['test_config'].update(config['test_config'])
    
    return base_config

def run_experiment_with_config(index, config, base_config_path, work_dir, category="default"):
    subdir = work_dir + 'outcome/' + config['memo_config']['uuid']
    if os.path.exists(subdir):
        print(f"Directory {subdir} already exists. Skipping experiment.")
        return 0
    
    os.makedirs(subdir, exist_ok=True)
    
    updated_config = update_base_config(base_config_path, config)
    cachebench_config_file_path = os.path.join(subdir, 'config.json')
    exp_config_file_path = os.path.join(subdir, 'exp_config.json')
    with open(cachebench_config_file_path, 'w') as f:
        json.dump(updated_config, f, indent=2)
    with open(exp_config_file_path, 'w') as f:
        json.dump(config, f, indent=2)
    

    output_file = os.path.join(subdir, 'std.out')
    output_json_file = os.path.join(subdir, 'out.json')
    if category == 'collect_rebalance_states':
        return_code =  run_cachebench_and_extract_rebalance_states(cachebench_config_file_path, output_file, output_json_file)
    else:
        return_code = run_cachebench(cachebench_config_file_path, output_file, output_json_file)
    if return_code != 0:
        print(f"Error running experiment with config {index}")
    
    return return_code

def get_aligned_size(size, alignment):
    return (size + alignment - 1) // alignment * alignment

def generate_alloc_sizes(factor, max_size, min_size, alignment=8):
    if max_size > 4 * 1024 * 1024:  # Assuming Slab::kSize is 1MB
        raise ValueError(f"maximum alloc size {max_size} is more than the slab size {1024 * 1024}")

    if factor <= 1.0:
        raise ValueError(f"invalid factor {factor}")

    alloc_sizes = set()
    size = min_size

    while size < max_size:
        n_per_slab = 4 * 1024 * 1024 // size  # Assuming Slab::kSize is 1MB
        if n_per_slab <= 1:
            break
        alloc_sizes.add(size)
        prev_size = size
        size = get_aligned_size(int(size * factor), alignment)
        if prev_size == size:
            raise ValueError(f"invalid incFactor {factor}")

    alloc_sizes.add(get_aligned_size(max_size, alignment))
    return len(alloc_sizes) * 4

def can_work(allocFactor, maxAllocSize, cacheSizeMB, minAllocSize, allocSizes):
    if allocSizes:
        return len(allocSizes) * 4 <= cacheSizeMB
    return generate_alloc_sizes(allocFactor, maxAllocSize, minAllocSize) <= cacheSizeMB

def is_valid_config(config):
    allocator = config["cache_config"]["allocator"]
    rebalanceStrategy = config["cache_config"]["rebalanceStrategy"]
    maxAllocSize = config["cache_config"].get("maxAllocSize", None)
    minAllocSize = config["cache_config"].get("minAllocSize", None)
    allocFactor = config["cache_config"].get("allocFactor", None)
    allocSizes = config["cache_config"].get("allocSizes", None)
    cacheSizeMB = config["cache_config"]["cacheSizeMB"]

    return (
        can_work(allocFactor, maxAllocSize, cacheSizeMB, minAllocSize, allocSizes) and
        (rebalanceStrategy != "marginal-hits" or allocator == "LRU2Q")
    )