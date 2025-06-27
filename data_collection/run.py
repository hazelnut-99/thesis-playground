import json
import concurrent.futures
from util import run_experiment_with_config

WORK_DIR = 'work_dir_21_new/'
PARALLELISM = 12
category = "default"

with open(WORK_DIR + 'exp_configs.json', 'r') as f:
    experiment_configs = json.load(f)

base_config_path = WORK_DIR + 'base_config.json'

def run_experiment(index, config):
    return run_experiment_with_config(index, config, base_config_path, WORK_DIR, category)

with concurrent.futures.ProcessPoolExecutor(max_workers=PARALLELISM) as executor:
    futures = [executor.submit(run_experiment, index, config) for index, config in enumerate(experiment_configs)]
    for future in concurrent.futures.as_completed(futures):
        try:
            result = future.result()
            print(f"Experiment completed with return code: {result}")
        except Exception as e:
            print(f"Experiment generated an exception: {e}")

print("All experiments have been processed.")