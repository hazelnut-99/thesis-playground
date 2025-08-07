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
    import json
    import re

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

    command = [
        cachelib_path,
        "--json_test_config", config_file,
        "--dump_result_json_file", output_file,
        "--dump_tx_file", tx_file,
        "--disable_progress_tracker=true",
        "--enable_debug_log=true"
    ]
    env = os.environ.copy()
    if config_content["test_config"].get("useTraceTimer", False):
        env["LD_PRELOAD"] = MOCK_TIMER_PATH

    rc_file = os.path.join(top_dir, "rc.txt")
    for i in range(repeat):
        miss_ratio_log = os.path.join(top_dir, f"miss_ratio_{i+1}.log")
        delta_stats_log = os.path.join(top_dir, f"delta_statistics_{i+1}.log")
        slab_movement_log = os.path.join(top_dir, f"slab_movement_event_{i+1}.log")
        rebalance_trigger_log = os.path.join(top_dir, f"rebalance_trigger_{i+1}.log")

        # Track current request_id for associating with rebalance details
        current_request_id = None
        rebalance_data = []

        with open(miss_ratio_log, "w") as miss_f, \
             open(delta_stats_log, "w") as delta_f, \
             open(slab_movement_log, "w") as slab_event_f, \
             open(rebalance_trigger_log, "w") as rebalance_f:

            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
            for line in process.stdout:
                # Parse miss ratio logging
                match_miss = re.search(r'miss_ratio_logging:\s*(\{.*\})', line)
                if match_miss:
                    try:
                        json_obj = json.loads(match_miss.group(1))
                        miss_f.write(json.dumps(json_obj) + "\n")
                    except json.JSONDecodeError as e:
                        print(f"Error decoding miss_ratio_logging JSON: {e}")

                # Parse delta statistics logging
                match_delta = re.search(r'Delta_statistics_logging:\s*(\{.*\})', line)
                if match_delta:
                    try:
                        json_obj = json.loads(match_delta.group(1))
                        delta_f.write(json.dumps(json_obj) + "\n")
                    except json.JSONDecodeError as e:
                        print(f"Error decoding Delta_statistics_logging JSON: {e}")

                # Parse slab movement event
                match_slab = re.search(r'Slab_movement_event:\s*(\{.*\})', line)
                if match_slab:
                    try:
                        json_obj = json.loads(match_slab.group(1))
                        slab_event_f.write(json.dumps(json_obj) + "\n")
                    except json.JSONDecodeError as e:
                        print(f"Error decoding Slab_movement_event JSON: {e}")

                # Parse trigger rebalance request_id
                match_trigger = re.search(r'Trigger rebalance at request_id:\s*(\d+)', line)
                if match_trigger:
                    current_request_id = int(match_trigger.group(1))

                # Parse rebalancing details (effective move rate and threshold)
                match_rebalance = re.search(
                    r'Rebalancing: effective move rate = ([^,]+), window size = ([^,]+), diff = ([^,]+), threshold = ([^,]+), \((\d+)->(\d+)\)',
                    line
                )
                if match_rebalance and current_request_id is not None:
                    try:
                        rebalance_info = {
                            "request_id": current_request_id,
                            "effective_move_rate": float(match_rebalance.group(1)),
                            "threshold": float(match_rebalance.group(4)),
                            "window_size": int(match_rebalance.group(2)),
                            "diff": float(match_rebalance.group(3)),
                            "victim_class_id": int(match_rebalance.group(5)),
                            "receiver_class_id": int(match_rebalance.group(6))
                        }
                        rebalance_data.append(rebalance_info)
                        rebalance_f.write(json.dumps(rebalance_info) + "\n")
                    except (ValueError, IndexError) as e:
                        print(f"Error parsing rebalancing details: {e}")

            process.wait()
            result_code = process.returncode
            if result_code != 0:
                with open(rc_file, 'w') as rc_out:
                    rc_out.write(str(result_code) + "\n")
                return result_code

    # If all runs succeed, write last return code (should be 0)
    with open(rc_file, 'w') as rc_out:
        rc_out.write(str(result_code) + "\n")
    return result_code