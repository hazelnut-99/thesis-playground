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

def run_cachebench(top_dir, repeat=1):
    config_file = os.path.join(top_dir, "config.json")
    meta_file = os.path.join(top_dir, "meta.json")
    output_file = os.path.join(top_dir, "result.json")
    log_file = os.path.join(top_dir, "log.txt")
    tx_file = os.path.join(top_dir, "tx")
    
    with open(meta_file, 'r') as f:
        meta_content = json.load(f)
    with open(config_file, 'r') as f:
        config_content = json.load(f)
    
    cachelib_path = CACHEBENCH_BINARY_PATH2 if int(meta_content["slab_size"]) == 1 else CACHEBENCH_BINARY_PATH

    if config_content["test_config"]["useTraceTimer"]:
        command = [
            "LD_PRELOAD=" + MOCK_TIMER_PATH,
            cachelib_path,
            "--json_test_config", config_file,
            "--dump_result_json_file", output_file,
            "--dump_tx_file", tx_file,
            "--disable_progress_tracker=true"
        ]
    else:
        command = [
            cachelib_path,
            "--json_test_config", config_file,
            "--dump_result_json_file", output_file,
            "--dump_tx_file", tx_file,
            "--disable_progress_tracker=true"
        ]

    rc_file = os.path.join(top_dir, "rc.txt")
    for i in range(repeat):
        with open(log_file, 'w') as out:
            result = subprocess.run(" ".join(command), shell=True, stdout=out, stderr=subprocess.STDOUT)
        if result.returncode != 0:
            with open(rc_file, 'w') as rc_out:
                rc_out.write(str(result.returncode) + "\n")
            return result.returncode
    # If all runs succeed, write last return code (should be 0)
    with open(rc_file, 'w') as rc_out:
        rc_out.write(str(result.returncode) + "\n")
    return result.returncode