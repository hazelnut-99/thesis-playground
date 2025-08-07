import glob
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from const import *
meta_dir = f"{HOME_DIR}/thesis-playground/paper-exp/efficiency/work_dir_new"
for lock_path in glob.glob(f"{meta_dir}/*/running.lock.grace"):
    subdir = os.path.dirname(lock_path)
    # Delete the subdir containing running.lock.grace
    import shutil
    shutil.rmtree(subdir)
    print(f"Deleted: {subdir}")

for lock_path in glob.glob(f"{meta_dir}/*/running.lock"):
    subdir = os.path.dirname(lock_path)
    # Delete the subdir containing running.lock.grace
    import shutil
    shutil.rmtree(subdir)
    print(f"Deleted: {subdir}")
