#!/usr/bin/env python3
import os
import json
from collections import defaultdict
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from const import *
WORK_DIR = f"{HOME_DIR}/thesis-playground/paper-exp/efficiency/work_dir"

def scan_experiments(work_dir):
    """Scans the work directory to find all experiment subdirectories and their metadata."""
    exps = []
    if not os.path.isdir(work_dir):
        print(f"ERROR: Work directory '{work_dir}' not found.")
        return []
    for subdir in os.listdir(work_dir):
        exp_dir = os.path.join(work_dir, subdir)
        if not os.path.isdir(exp_dir):
            continue
        # We now need to load meta.json to get resource requirements
        meta_path = os.path.join(exp_dir, "meta.json")
        if not os.path.exists(meta_path):
            continue
        with open(meta_path) as f:
            meta = json.load(f)
        exps.append({"dir": exp_dir, "meta": meta})
    return exps

def get_running_info(exp):
    """
    Checks if an experiment is running. If so, returns the hostname it's running on.
    Otherwise, returns None.
    """
    lock_file = os.path.join(exp["dir"], "running.lock")
    if os.path.exists(lock_file):
        with open(lock_file, 'r') as f:
            hostname = f.read().strip()
        return hostname if hostname else None
    return None

def get_exp_status(exp):
    """Determines the status of an experiment: finished, failed, running, or todo."""
    rc_file = os.path.join(exp["dir"], "rc.txt")
    if os.path.exists(rc_file):
        with open(rc_file) as f:
            rc = f.read().strip()
        return "finished" if rc == "0" else "failed"
    
    if get_running_info(exp):
        return "running"
    
    return "todo"

def summarize_status():
    """
    Scans the work directory, tallies the status of all experiments,
    and prints a summary report including node resource usage.
    """
    all_exps = scan_experiments(WORK_DIR)
    if not all_exps:
        print("No experiments found to summarize.")
        return

    status_counts = defaultdict(int)
    failed_jobs = []
    node_usage = defaultdict(lambda: {"cpu": 0, "mem": 0, "jobs": 0})

    for exp in all_exps:
        status = get_exp_status(exp)
        status_counts[status] += 1
        
        if status == "failed":
            failed_jobs.append(os.path.basename(exp["dir"]))
        
        if status == "running":
            hostname = get_running_info(exp)
            if hostname:
                # Aggregate resource usage for the node this job is running on
                node_usage[hostname]["cpu"] += exp["meta"].get("cpu_requirement", 0)
                node_usage[hostname]["mem"] += exp["meta"].get("memory_requirement", 0)
                node_usage[hostname]["jobs"] += 1

    total_jobs = len(all_exps)
    
    print("\n--- Experiment Status Summary ---")
    print(f"Total Experiments: {total_jobs}")
    print("---------------------------------")
    print(f"  Finished: {status_counts['finished']:>5}")
    print(f"  Running:  {status_counts['running']:>5}")
    print(f"  Pending:  {status_counts['todo']:>5}")
    print(f"  Failed:   {status_counts['failed']:>5}")
    print("---------------------------------")

    if node_usage:
        print("\n--- Node Resource Usage (Based on running jobs) ---")
        for host, usage in sorted(node_usage.items()):
            # Memory usage in GB for better readability
            mem_gb = usage['mem'] / 1024
            print(f"  - Host: {host}")
            print(f"    - Running Jobs:   {usage['jobs']}")
            print(f"    - CPU Cores Used: {usage['cpu']}")
            print(f"    - Memory Used:    {mem_gb:.2f} GB")
        print("-----------------------------------------------------")

    if failed_jobs:
        print("\nList of Failed Experiments (UUIDs):")
        for job_uuid in sorted(failed_jobs):
            print(f"  - {job_uuid}")
        print("\nTo retry a failed job, manually delete its 'rc.txt' file.")
    
    print()


if __name__ == "__main__":
    summarize_status()


"""
parallel-ssh -h hosts.txt -l Hongshu "pgrep -f 'run_cachebench_efficiency' | xargs -r kill -9"
"""