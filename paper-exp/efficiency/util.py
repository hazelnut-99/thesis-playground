import json
import hashlib
import os
import json
import re
import subprocess
from const import *


def dict_hash(d):
    # Serialize with sorted keys and no whitespace for consistency
    json_str = json.dumps(d, sort_keys=True, separators=(',', ':'))
    return hashlib.md5(json_str.encode('utf-8')).hexdigest()



def run_cachebench_efficiency(top_dir):
    config_file = os.path.join(top_dir, "config.json")
    meta_file = os.path.join(top_dir, "meta.json")
    output_file = os.path.join(top_dir, "result.json")
    log_file = os.path.join(top_dir, "log.txt")
    
    with open(meta_file, 'r') as f:
        meta_content = json.load(f)
    with open(config_file, 'r') as f:
        config_content = json.load(f)
    
    cachelib_path = CACHEBENCH_BINARY_PATH2 if meta_content["slab_size"] == 1 else CACHEBENCH_BINARY_PATH
    if config_content["test_config"]["useTraceTimer"]:
        command = [
            "LD_PRELOAD=" + MOCK_TIMER_PATH,
            cachelib_path,
            "--json_test_config", config_file,
            "-progress=500000",
            "--dump_result_json_file", output_file
        ]
    else:
        command = [
            cachelib_path,
            "--json_test_config", config_file,
            "-progress=500000",
            "--dump_result_json_file", output_file
        ]
    
    with open(log_file, 'w') as out:
        result = subprocess.run(" ".join(command), shell=True, stdout=out, stderr=subprocess.STDOUT)
    
    rc_file = os.path.join(top_dir, "rc.txt")
    with open(rc_file, 'w') as rc_out:
        rc_out.write(str(result.returncode) + "\n")
    
    return result.returncode



