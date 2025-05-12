import json

# Load the JSON data from a file
with open('exp_configs.json', 'r') as f:
    data = json.load(f)

# Filter out objects where memo_config.trace_name == 'cluster16_sample10'
filtered_data = [
    obj for obj in data
    if obj.get('memo_config', {}).get('trace_name') != 'cluster16_sample10'
]

# Write the filtered data back to the file
with open('exp_configs.json', 'w') as f:
    json.dump(filtered_data, f, indent=2)
