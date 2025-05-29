
config =  {
        "type": "periodic",
        "time_span": 604800,
        "total_requests": 40000000,
        "output_file": "/mydata/hongshu/traces/synth_dynamic_504.csv",
        "generators_config": [
            [
                {"m": 200000, "alpha": 0.85, "share": 4, "size": 2006},
                {"m": 100000, "alpha": 1.0, "share": 1, "size": 4054}
            ],
            [
                {"m": 200000, "alpha": 0.85, "share": 1, "size": 2006},
                {"m": 100000, "alpha": 1.0, "share": 4, "size": 4054}
            ]
        ],
        "weight_array": [1, 1],
        "request_per_cycle": 1000000
    }
request_per_cycle = config['request_per_cycle']
total_requests = config['total_requests']
num_cycles = total_requests // request_per_cycle

base_id = 0
reset_timings = []
for cycle in range(num_cycles):
    total_weights = sum(config['weight_array'])
    request_per_share = request_per_cycle / total_weights
    for weight in config['weight_array']:
        request_count = int(weight * request_per_share)
        reset_timings.append(base_id + request_count - 1)
        base_id += request_count


print(','.join(map(str, reset_timings[:-1])))
    
        



