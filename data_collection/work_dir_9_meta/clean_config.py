import os
import json

current_dir = os.path.dirname(__file__)
config_path = os.path.join(current_dir, 'exp_configs.json')

with open(config_path, 'r') as f:
     existing_configs = json.load(f)
print(len(existing_configs))
existing_configs = [cfg for cfg in existing_configs if 'mhMinDiff' not in cfg.get('cache_config', {})]
print(len(existing_configs))

with open(config_path, 'w') as f:
    json.dump(existing_configs, f, indent=2)
                
