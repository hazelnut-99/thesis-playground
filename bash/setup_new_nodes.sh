#!/bin/bash

# Configurable list of machines (edit as needed)
MACHINES=(
    "Hongshu@clnode302.clemson.cloudlab.us"
    "Hongshu@clnode290.clemson.cloudlab.us"
    "Hongshu@clnode303.clemson.cloudlab.us"
    "Hongshu@clnode287.clemson.cloudlab.us"
    "Hongshu@clnode301.clemson.cloudlab.us"
    "Hongshu@clnode286.clemson.cloudlab.us"
)

SETUP_CMDS=$(cat <<'END_CMDS'
sudo apt-get update -y
sudo apt-get install python3-pip libglib2.0-dev parallel -y
pip3 install pandas plotly matplotlib seaborn requests

cd /users/Hongshu

# Setup cachelib_v1 (4mb slab)
mkdir -p cachelib_v1
cd cachelib_v1
if [ ! -d ".git" ]; then
    git clone https://github.com/hazelnut-99/CacheLib.git .
fi
git fetch origin
current_branch=$(git rev-parse --abbrev-ref HEAD)
if [ "$current_branch" != "benchmark-4mb-slab" ]; then
    git checkout benchmark-4mb-slab
fi
git pull origin benchmark-4mb-slab
git config --global --add safe.directory /nfs/hongshu/CacheLib/cachelib/external/zstd
sudo ./contrib/build.sh -j -T

# Setup cachelib_v2 (1mb slab)
cd /users/Hongshu
mkdir -p cachelib_v2
cd cachelib_v2
if [ ! -d ".git" ]; then
    git clone https://github.com/hazelnut-99/CacheLib.git .
fi
git fetch origin
current_branch=$(git rev-parse --abbrev-ref HEAD)
if [ "$current_branch" != "benchmark-1mb-slab" ]; then
    git checkout benchmark-1mb-slab
fi
git pull origin benchmark-1mb-slab
git config --global --add safe.directory /nfs/hongshu/CacheLib/cachelib/external/zstd
sudo ./contrib/build.sh -j -T
END_CMDS
)

for MACHINE in "${MACHINES[@]}"; do
    echo "Setting up $MACHINE ..."
    ssh "$MACHINE" "$SETUP_CMDS" &
done

wait
echo "All setups finished."