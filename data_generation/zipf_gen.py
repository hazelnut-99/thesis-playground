#!/usr/bin/env python3

import numpy as np
import struct
import csv
from argparse import ArgumentParser
import json
from concurrent.futures import ProcessPoolExecutor, as_completed

class ZipfGenerator:
    def __init__(self, m, alpha, base_id=0):
        # Calculate Zeta values from 1 to n using NumPy:
        print(f"Generating Zipf distribution with m={m}, alpha={alpha}")
        tmp = np.power(np.arange(1, m + 1), -alpha)
        zeta = np.cumsum(tmp)

        # Store the translation map:
        self.distMap = zeta / zeta[-1]
        self.base_id = base_id

    def next(self):
        # Generate a uniform 0-1 pseudo-random value:
        u = np.random.uniform(0, 1)

        # Translate the Zipf variable:
        return (np.searchsorted(self.distMap, u) + self.base_id).item()


class MergedStaticZipfGenerator:
    def __init__(self, generators_config, base_id=0):
        self.generators = []
        for config in generators_config:
            generator = ZipfGenerator(config['m'], config['alpha'], base_id)
            self.generators.append(generator)
            # make sure that obj ids don't overlap
            base_id += config['m']
        # round robin weights
        self.shares = [config['share'] for config in generators_config]
        self.obj_sizes = [config['size'] for config in generators_config]
        self.i = 0
        
        self.generator_index = 0
        self.generator_cnt = 0

    def get_total_requests(self):
        return self.total_requests
    
    def _move_to_next_generator(self):
        self.generator_index = (self.generator_index + 1) % len(self.generators)
        self.generator_cnt = 0
    
    def next(self):
        generator = self.generators[self.generator_index]
        obj_id, obj_size = generator.next(), self.obj_sizes[self.generator_index]
        self.generator_cnt += 1
        if self.generator_cnt >= self.shares[self.generator_index]:
            self._move_to_next_generator()
        return obj_id, obj_size


class PeriodicZipfGenerator:
    def __init__(self, static_generator_configs, weight_array, request_per_cycle, base_id = 0):
        self.requests_per_generator_per_cycle = [weight/(sum(weight_array)) * request_per_cycle for weight in weight_array]
        
        self.generators = []
        for static_generator_config in static_generator_configs:
            generator = MergedStaticZipfGenerator(static_generator_config, base_id)
            # make sure that obj ids don't overlap
            base_id += sum([config['m'] for config in static_generator_config])
            self.generators.append(generator)
            
        self.requests_per_cycle = request_per_cycle
        
        self.generator_index = 0
        self.generator_cnt = 0
        self.cycle_index = 0
        self.cycle_cnt = 0
    
    def _move_to_next_generator(self):
        self.generator_index = (self.generator_index + 1) % len(self.generators)
        self.generator_cnt = 0
    
    def _move_to_next_cycle(self):
        self.cycle_index += 1
        self.cycle_cnt = 0
        self.generator_index = 0
        self.cycle_cnt = 0
    
    def next(self):
        obj_id, obj_size = self.generators[self.generator_index].next()
        self.generator_cnt += 1
        self.cycle_cnt += 1
        if self.generator_cnt >= self.requests_per_generator_per_cycle[self.generator_index]:
            self._move_to_next_generator()
        if self.cycle_cnt >= self.requests_per_cycle:
            self._move_to_next_cycle()
        return obj_id, obj_size
        

def generate(generator, total_requests, time_span=86400 * 7, output_file=None):
    s = struct.Struct("<IQIq")
    i = 0
    if output_file:
        if output_file.endswith("bin"):
            with open(output_file, "wb") as f:
                while i < total_requests:
                    obj_id, obj_size = generator.next()
                    i += 1
                    ts = i * time_span // total_requests
                    f.write(s.pack(ts, obj_id, obj_size, -2))
        else:
            with open(output_file, "w", newline='') as f:
                writer = csv.writer(f, lineterminator='\n')
                writer.writerow(["clock_time", "object_id", "object_size", "next_access_vtime"])
                while i < total_requests:
                    obj_id, obj_size = generator.next()
                    i += 1
                    ts = i * time_span // total_requests
                    writer.writerow([ts, obj_id, obj_size, -2])
            
    else:
        while i < total_requests:
            obj_id, obj_size = generator.next()
            i += 1
            ts = i * time_span // total_requests
            print(f"{ts} {obj_id} {obj_size}")


def process_config(config):
    if config['type'] == 'static':
        generator = MergedStaticZipfGenerator(config['generators_config'], config['total_requests'])
    elif config['type'] == 'periodic':
        generator = PeriodicZipfGenerator(config['generators_config'], config['weight_array'], config['request_per_cycle'])
    else:
        raise ValueError(f"Unknown generator type: {config['type']}")
    generate(generator, config['total_requests'], config['time_span'], config['output_file'])
    print(f"Generated data for {config['output_file']}")

def generate_based_on_config_file(config_file_path):
    with open(config_file_path) as f:
        configs = json.load(f)
    with ProcessPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_config, config) for config in configs]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"An error occurred: {e}")
        

# Example usage
if __name__ == "__main__":
    static_generators_config1 = [
        {'m': 1000000, 'alpha': 1.0, 'share': 2, 'size': 30},
        {'m': 1000000, 'alpha': 0.8, 'share': 2, 'size': 50},
        {'m': 1000000, 'alpha': 1.2, 'share': 1, 'size': 80}
    ]
    static_generators_config2 = [
        {'m': 1000000, 'alpha': 1.0, 'share': 2, 'size': 300},
        {'m': 1000000, 'alpha': 0.8, 'share': 2, 'size': 500},
        {'m': 1000000, 'alpha': 1.2, 'share': 1, 'size': 800}
    ]
    
    periodic_generator = PeriodicZipfGenerator([static_generators_config1, static_generators_config2], [4, 1], 10)
    generate(periodic_generator, 50)
    
    generate_based_on_config_file("periodic_config.json")
    
    