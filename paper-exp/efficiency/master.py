import os
import json
import subprocess
import time
import requests
from collections import defaultdict
import logging
import random
from datetime import datetime, timedelta

from const import *

WORK_DIR = f"{HOME_DIR}/thesis-playground/paper-exp/efficiency/work_dir"
TRACE_DIR = f"{HOME_DIR}/traces"
SCRIPTS_DIR = f"{HOME_DIR}/thesis-playground/paper-exp/efficiency/" # Directory for util.py
HOSTS_FILE = "hosts.txt"                 # A file in the same directory as the script
PYTHON_EXEC = "python3"                  # or "python" as needed
STATE_FILE = "scheduler_state.json"      # File for dumping the central state

# Per-node resource limits (fill in actual values)
NODE_RESOURCES = {
    "clnode257.clemson.cloudlab.us": {"cpu": 70, "mem": 122880},
    #"clnode258.clemson.cloudlab.us": {"cpu": 140, "mem": 250880},
    "clnode263.clemson.cloudlab.us": {"cpu": 140, "mem": 250880},
    "clnode268.clemson.cloudlab.us": {"cpu": 140, "mem": 250880},
    "clnode281.clemson.cloudlab.us": {"cpu": 140, "mem": 250880},
    "clnode134.clemson.cloudlab.us": {"cpu": 40, "mem": 204800},
}
# =====================

# --- HELPER FUNCTIONS ---

def get_remote_file_size(url):
    """Gets the size of a remote file in bytes using an HTTP HEAD request."""
    try:
        r = requests.head(url, allow_redirects=True, timeout=10)
        r.raise_for_status()  # Raise an exception for bad status codes
        size = r.headers.get('Content-Length')
        return int(size) if size else None
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to get size for {url}: {e}")
        return None

def get_nfs_free_bytes(path):
    """Gets the free space in bytes for the filesystem that a path resides on."""
    try:
        stat = os.statvfs(path)
        return stat.f_bavail * stat.f_frsize
    except FileNotFoundError:
        logging.error(f"Path not found for statvfs: {path}. Returning 0 free space.")
        return 0

def scan_experiments(work_dir):
    """Scans the work directory to find all experiment subdirectories and their metadata."""
    exps = []
    if not os.path.isdir(work_dir):
        logging.critical(f"WORK_DIR '{work_dir}' does not exist. Exiting.")
        exit(1)
    for subdir in os.listdir(work_dir):
        exp_dir = os.path.join(work_dir, subdir)
        if not os.path.isdir(exp_dir):
            continue
        meta_path = os.path.join(exp_dir, "meta.json")
        if not os.path.exists(meta_path):
            continue
        with open(meta_path) as f:
            meta = json.load(f)
        exps.append({"dir": exp_dir, "meta": meta})
    return exps

def group_by_trace(exps):
    """Groups experiments by their required trace file."""
    trace_to_exps = defaultdict(list)
    for exp in exps:
        trace_file = exp["meta"]["trace_file"]
        trace_to_exps[trace_file].append(exp)
    return trace_to_exps

def all_exps_done(exps):
    """Checks if all experiments in a list are finished (have an rc.txt file)."""
    for exp in exps:
        if not os.path.exists(os.path.join(exp["dir"], "rc.txt")):
            return False
    return True

def download_trace(meta):
    """
    Downloads a trace file if it doesn't exist and there is enough space.
    Uses 'sudo' for wget and rm, assuming passwordless sudo is configured.
    """
    url = meta["download_path"]
    url = f"{WGET_PATH}/{url}"
    local_path = meta["trace_file"]
    trace_dir = os.path.dirname(local_path)

    # Ensure the trace directory exists using sudo
    if not os.path.exists(trace_dir):
        subprocess.run(["sudo", "mkdir", "-p", trace_dir])
        subprocess.run(["sudo", "chown", "-R", f"{os.getuid()}:{os.getgid()}", trace_dir])

    size = get_remote_file_size(url)
    
    if os.path.exists(local_path):
        if size is not None and os.path.getsize(local_path) < size:
            logging.warning(f"Partial file detected at {local_path}. Deleting for re-download.")
            subprocess.run(["sudo", "rm", "-f", local_path]) # Use sudo to remove
        else:
            logging.info(f"Trace {os.path.basename(local_path)} already exists.")
            return True

    free_space = get_nfs_free_bytes(trace_dir)
    if size is None:
        logging.warning(f"Could not determine size of {url}. Cannot download.")
        return False
    if free_space < size:
        logging.warning(f"Not enough space for {local_path} ({size/1e9:.2f}GB needed, {free_space/1e9:.2f}GB free)")
        return False

    logging.info(f"Downloading {url} to {local_path} with sudo...")
    # Use wget with sudo
    res = subprocess.run(["sudo", "wget", "-O", local_path, url], capture_output=True)
    if res.returncode != 0:
        logging.error(f"Failed to download {url}. Wget stderr: {res.stderr.decode()}")
        if os.path.exists(local_path):
             subprocess.run(["sudo", "rm", "-f", local_path]) # Use sudo to clean up
        return False
    return True

def delete_trace(trace_file):
    """
    Deletes a trace file from the filesystem using sudo.
    """
    if os.path.exists(trace_file):
        logging.info(f"Deleting trace file {trace_file} with sudo...")
        subprocess.run(["sudo", "rm", "-f", trace_file])


def get_hosts(hosts_file):
    """Reads a list of hosts from a file."""
    try:
        with open(hosts_file) as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        logging.critical(f"Hosts file '{hosts_file}' not found. Exiting.")
        exit(1)

def log_status_summary(exps, running_jobs):
    """Logs a summary of the status of all experiments."""
    status_count = defaultdict(int)
    for exp in exps:
        status = get_exp_status(exp)
        status_count[status] += 1
    logging.info(f"STATUS: {status_count['todo']} ToDo, {len(running_jobs)} Running, "
                 f"{status_count['finished']} Finished, {status_count['failed']} Failed.")

def log_node_system_stats(hosts):
    """Logs the current CPU and Memory utilization for each host."""
    logging.info("--- System-wide Resource Utilization ---")
    for host in hosts:
        try:
            # Get CPU Utilization (100 - idle %)
            cpu_util_cmd = "top -bn1 | grep 'Cpu(s)' | awk '{print 100.0 - $8}'"
            cpu_result = subprocess.run(
                ["ssh", host, cpu_util_cmd],
                capture_output=True, text=True, check=True, timeout=10
            )
            cpu_util = float(cpu_result.stdout.strip())

            # Get Free Memory Percentage ( (available / total) * 100 )
            mem_util_cmd = "free -m | awk '/^Mem:/ {printf \"%.2f\", $7/$2 * 100.0}'"
            mem_result = subprocess.run(
                ["ssh", host, mem_util_cmd],
                capture_output=True, text=True, check=True, timeout=10
            )
            mem_free_percent = float(mem_result.stdout.strip())

            logging.info(f"  - Host: {host:<30} CPU Util: {cpu_util:5.1f}% | Mem Free: {mem_free_percent:5.1f}%")

        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError) as e:
            logging.warning(f"  - Host: {host:<30} FAILED to retrieve stats. Reason: {e}")
    logging.info("----------------------------------------")

def log_running_job_stats(running_jobs):
    """Logs the runtime of each currently running job."""
    if not running_jobs:
        return
    logging.info("--- Running Job Runtimes ---")
    now = time.time()
    for exp_dir, job_info in sorted(running_jobs.items(), key=lambda item: item[1]['start_time']):
        run_time_seconds = now - job_info['start_time']
        # Format seconds into a more readable HH:MM:SS format
        run_time_formatted = str(timedelta(seconds=int(run_time_seconds)))
        host = job_info['host']
        uuid = os.path.basename(exp_dir)
        logging.info(f"  - Job: {uuid} on {host:<25} has been running for {run_time_formatted}")
    logging.info("----------------------------")


# --- STATE MANAGEMENT FUNCTIONS (ENHANCED) ---

def is_process_actually_running(hostname, uuid):
    """
    Connects to a remote host and checks if a process with a specific
    tag (UUID) is currently running.
    """
    process_tag = f"CACHEBENCH_UUID={uuid}"
    # pgrep -f searches the full command line for the pattern.
    # It returns 0 if a process is found, 1 if not.
    check_cmd = f"pgrep -f '{process_tag}'"
    try:
        # We check the return code. If it's 0, the process exists.
        subprocess.run(["ssh", hostname, check_cmd], check=True, capture_output=True, timeout=15)
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        # CalledProcessError with non-zero return code means pgrep found nothing.
        # TimeoutExpired means the host might be down or unresponsive.
        return False

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

def mark_exp_running(exp, hostname):
    """Marks an experiment as running by writing the hostname to the lock file."""
    lock_file = os.path.join(exp["dir"], "running.lock")
    with open(lock_file, 'w') as f:
        f.write(hostname)

def unmark_exp_running(exp):
    """Unmarks an experiment by deleting the lock file. Called when job finishes."""
    lock_file = os.path.join(exp["dir"], "running.lock")
    if os.path.exists(lock_file):
        os.remove(lock_file)

def get_exp_status(exp, grace_period=600):
    """
    Determines the status of an experiment with process-level verification and a grace period.
    States: finished, failed, running, todo.
    """
    rc_file = os.path.join(exp["dir"], "rc.txt")
    lock_file = os.path.join(exp["dir"], "running.lock")
    grace_file = lock_file + ".grace"

    # --- Case 1: The job has a definitive result file. ---
    if os.path.exists(rc_file):
        with open(rc_file) as f:
            rc = f.read().strip()
        
        # Clean up any leftover state files
        if os.path.exists(lock_file):
            unmark_exp_running(exp)
        if os.path.exists(grace_file):
            os.remove(grace_file)
            
        return "finished" if rc == "0" else "failed"

    # --- Case 2: The job has a lock file, meaning it was running. ---
    hostname = get_running_info(exp)
    if hostname:
        uuid = os.path.basename(exp["dir"])
        # Check if the process is still alive
        if is_process_actually_running(hostname, uuid):
            return "running"
        else:
            # Process is gone, but no rc.txt yet. Start or check the grace period.
            now = time.time()
            if not os.path.exists(grace_file):
                # Start the grace period
                with open(grace_file, "w") as f:
                    f.write(str(now))
                logging.info(f"Process for {uuid} is gone. Starting {grace_period}s grace period.")
                return "running" # Pretend it's running during the grace period
            else:
                # Check if grace period has expired
                with open(grace_file) as f:
                    start_time = float(f.read().strip())
                
                if now - start_time < grace_period:
                    return "running" # Still within grace period
                else:
                    # Grace period expired. This is now a confirmed stale job.
                    logging.warning(f"Stale job {uuid} on {hostname} failed after grace period.")
                    with open(rc_file, 'w') as f:
                        f.write("-99") # Mark as failed
                    
                    # Clean up all state files
                    unmark_exp_running(exp)
                    os.remove(grace_file)
                    
                    return "failed"
            
    # --- Case 3: No lock file and no rc.txt. The job is waiting to be scheduled. ---
    return "todo"

def dump_state_to_file(all_exps, running_jobs, filename):
    """
    Gathers the state of all experiments and dumps it to a JSON file.
    """
    logging.info(f"Dumping current state to {filename}...")
    state_data = []
    now = time.time()

    for exp in all_exps:
        exp_dir = exp['dir']
        uuid = os.path.basename(exp_dir)
        status = get_exp_status(exp)
        
        host = None
        start_time_unix = None
        start_time_str = None
        duration_str = None

        if exp_dir in running_jobs:
            job_info = running_jobs[exp_dir]
            host = job_info['host']
            start_time_unix = job_info['start_time']
            start_time_str = datetime.fromtimestamp(start_time_unix).isoformat()
            duration_seconds = now - start_time_unix
            duration_str = str(timedelta(seconds=int(duration_seconds)))

        state_data.append({
            "uuid": uuid,
            "status": status,
            "host": host,
            "start_time_unix": start_time_unix,
            "start_time_iso": start_time_str,
            "duration": duration_str
        })
    
    try:
        with open(filename, 'w') as f:
            json.dump(state_data, f, indent=4)
    except IOError as e:
        logging.error(f"Failed to dump state to {filename}: {e}")

def schedule_experiments_reconstructable():
    """Main scheduler function with state reconstruction."""
    logging.basicConfig(filename="master_scheduler.log", level=logging.INFO,
                        format="%(asctime)s %(levelname)s: %(message)s",
                        datefmt='%Y-%m-%d %H:%M:%S')
    logging.info("--- Scheduler Starting ---")
    master_start_time = time.time() # For reconstructed jobs

    all_exps = scan_experiments(WORK_DIR)
    trace_to_exps = group_by_trace(all_exps)
    hosts = get_hosts(HOSTS_FILE)

    # --- STATE TRACKING ---
    node_usage = {host: {"cpu": 0, "mem": 0} for host in hosts}
    running_jobs = {}  # {exp_dir: {"host": host, "start_time": timestamp}}

    # --- STATE RECONSTRUCTION ON STARTUP ---
    logging.info("Reconstructing state from filesystem...")
    for exp in all_exps:
        # Use the robust get_exp_status during reconstruction
        status = get_exp_status(exp)
        if status == "running":
            exp_dir = exp["dir"]
            running_host = get_running_info(exp) # We know this is valid now
            meta = exp["meta"]
            cpu_req = meta["cpu_requirement"]
            mem_req = meta["memory_requirement"]
            node_usage[running_host]["cpu"] += cpu_req
            node_usage[running_host]["mem"] += mem_req
            running_jobs[exp_dir] = {"host": running_host, "start_time": master_start_time}
            logging.info(f"Reconstructed state for running job {os.path.basename(exp_dir)} on {running_host}")

    logging.info("--- State Reconstruction Complete. Starting Main Loop. ---")
    
    last_system_log_time = 0

    # --- MAIN SCHEDULING LOOP ---
    while True:
        # 1. UPDATE STATE: Check for finished jobs and free up resources
        finished_jobs = []
        for exp_dir, job_info in list(running_jobs.items()):
            host = job_info['host']
            exp_obj = next((exp for exp in all_exps if exp["dir"] == exp_dir), None)
            if exp_obj is None: continue
            
            status = get_exp_status(exp_obj)
            if status != "running": # Job has finished or failed (including stale)
                meta = exp_obj["meta"]
                cpu_req = meta["cpu_requirement"]
                mem_req = meta["memory_requirement"]
                node_usage[host]["cpu"] = max(0, node_usage[host]["cpu"] - cpu_req)
                node_usage[host]["mem"] = max(0, node_usage[host]["mem"] - mem_req)
                
                end_time = time.time()
                run_time_seconds = end_time - job_info['start_time']
                run_time_formatted = str(timedelta(seconds=int(run_time_seconds)))
                
                logging.info(f"Job {os.path.basename(exp_dir)} ended on {host} with status '{status}' after {run_time_formatted}. Freed resources.")
                finished_jobs.append(exp_dir)
        
        for job_dir in finished_jobs:
            if job_dir in running_jobs:
                del running_jobs[job_dir]

        # 2. MANAGE TRACES: Check if any traces can be deleted
        for trace_file, exps_for_trace in trace_to_exps.items():
            if os.path.exists(trace_file) and all_exps_done(exps_for_trace):
                is_still_running = any(exp['dir'] in running_jobs for exp in exps_for_trace)
                if not is_still_running:
                    delete_trace(trace_file)

        # 3. SCHEDULE NEW JOBS
        progress_made = False
        pending_exps = [exp for exp in all_exps if get_exp_status(exp) == "todo"]
        random.shuffle(pending_exps)

        for exp in pending_exps:
            exp_dir = exp["dir"]
            meta = exp["meta"]
            trace_file = meta["trace_file"]
            
            if not os.path.exists(trace_file):
                if not download_trace(meta):
                    continue 

            cpu_req = meta["cpu_requirement"]
            mem_req = meta["memory_requirement"]
            
            eligible_hosts = []
            for host in hosts:
                node_res = NODE_RESOURCES.get(host, {"cpu": 0, "mem": 0})
                usage = node_usage.get(host, {"cpu": 0, "mem": 0})
                if usage["cpu"] + cpu_req <= node_res["cpu"] and usage["mem"] + mem_req <= node_res["mem"]:
                    eligible_hosts.append(host)

            if not eligible_hosts:
                continue

            chosen_host = random.choice(eligible_hosts)
            
            uuid = os.path.basename(exp_dir)
            process_tag = f"CACHEBENCH_UUID={uuid}"

            logging.info(f"Dispatching {uuid} to {chosen_host}...")
            
            remote_cmd_py = f'from util import run_cachebench_efficiency; run_cachebench_efficiency("{exp_dir}")'
            
            remote_cmd = (
                f"cd {SCRIPTS_DIR} && "
                f"nohup env CACHEBENCH_UUID={uuid} {PYTHON_EXEC} -c '{remote_cmd_py}' "
                f"> {exp_dir}/worker.log 2>&1 &"
            )
            
            subprocess.Popen(["ssh", chosen_host, remote_cmd])

            mark_exp_running(exp, chosen_host)
            node_usage[chosen_host]["cpu"] += cpu_req
            node_usage[chosen_host]["mem"] += mem_req
            running_jobs[exp_dir] = {"host": chosen_host, "start_time": time.time()}
            progress_made = True

        # 4. LOGGING AND SLEEP
        now = time.time()
        if now - last_system_log_time > 60:
            log_node_system_stats(hosts)
            log_running_job_stats(running_jobs)
            dump_state_to_file(all_exps, running_jobs, STATE_FILE) # Dump state here
            last_system_log_time = now
            
        log_status_summary(all_exps, running_jobs)

        # Check if all jobs are in a finished or failed state
        all_jobs_accounted_for = all(get_exp_status(exp) in ["finished", "failed"] for exp in all_exps)
        if not running_jobs and all_jobs_accounted_for:
             logging.info("All experiments completed. Shutting down.")
             break
        
        sleep_time = 5 if progress_made else 60
        logging.info(f"Loop finished. Sleeping for {sleep_time} seconds.")
        time.sleep(sleep_time)


if __name__ == '__main__':
    schedule_experiments_reconstructable()
