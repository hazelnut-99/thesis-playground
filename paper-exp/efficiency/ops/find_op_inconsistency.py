import os
import json
import shutil

base_dir = "../work_dir_new"  # Change to your directory if needed

diff_count = 0

for subdir in os.listdir(base_dir):
    subdir_path = os.path.join(base_dir, subdir)
    if not os.path.isdir(subdir_path):
        continue

    config_path = os.path.join(subdir_path, "config.json")
    if not os.path.exists(config_path):
        continue

    # Find tx.*.json file
    tx_files = [f for f in os.listdir(subdir_path) if f.startswith("tx.") and f.endswith(".json")]
    if not tx_files:
        continue
    tx_path = os.path.join(subdir_path, tx_files[0])

    try:
        with open(config_path) as cf:
            config = json.load(cf)
        num_ops = config.get("test_config", {}).get("numOps", None)
    except Exception:
        continue

    try:
        with open(tx_path) as tf:
            tx = json.load(tf)
        ops = tx.get("ops", None)
    except Exception:
        continue

    if num_ops != ops and num_ops and ops:
        ratio = ops / num_ops if num_ops != 0 else float('inf')
        print(f"Deleting {subdir}: numOps={num_ops}, ops={ops}, ratio={ratio:.4f}")
        shutil.rmtree(subdir_path)
        diff_count += 1

print(f"Total subdirs deleted due to different ops: {diff_count}")