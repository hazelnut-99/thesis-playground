"""
list all subdirs under work_dir
if it has a rc.txt file and content of the file is not 0
then delete all files in the subdir except config.json and meta.json
print the subdir name if above condition is met
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from const import *

WORK_DIR = f"{HOME_DIR}/thesis-playground/paper-exp/efficiency/work_dir_meta"

for subdir in os.listdir(WORK_DIR):
    subdir_path = os.path.join(WORK_DIR, subdir)
    if not os.path.isdir(subdir_path):
        continue
    rc_file = os.path.join(subdir_path, "rc.txt")
    if os.path.exists(rc_file):
        with open(rc_file) as f:
            rc = f.read().strip()
        if rc != "0":
            for fname in os.listdir(subdir_path):
                if fname not in ("config.json", "meta.json"):
                    fpath = os.path.join(subdir_path, fname)
                    if os.path.isfile(fpath) or os.path.islink(fpath):
                        os.remove(fpath)
                    elif os.path.isdir(fpath):
                        # Recursively delete directories
                        import shutil
                        shutil.rmtree(fpath)
            print(subdir)