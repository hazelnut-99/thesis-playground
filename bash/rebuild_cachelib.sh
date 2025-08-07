#!/bin/bash

# Configurable list of machines (edit as needed)
MACHINES=(
    "Hongshu@clnode370.clemson.cloudlab.us"
    "Hongshu@clnode355.clemson.cloudlab.us"
    "Hongshu@clnode337.clemson.cloudlab.us"
    "Hongshu@clnode322.clemson.cloudlab.us"
    "Hongshu@clnode332.clemson.cloudlab.us"
)

SETUP_CMDS=$(cat <<'END_CMDS'
cd /users/Hongshu

# Update cachelib_v1 (4mb slab)
cd cachelib_v1
git fetch origin
current_branch=$(git rev-parse --abbrev-ref HEAD)
if [ "$current_branch" != "benchmark-4mb-slab" ]; then
    git checkout benchmark-4mb-slab
fi
git pull origin benchmark-4mb-slab
cd build-cachelib
sudo make -j
sudo make install

# Update cachelib_v2 (1mb slab)
cd /users/Hongshu/cachelib_v2
git fetch origin
current_branch=$(git rev-parse --abbrev-ref HEAD)
if [ "$current_branch" != "benchmark-1mb-slab" ]; then
    git checkout benchmark-1mb-slab
fi
git pull origin benchmark-1mb-slab
cd build-cachelib
sudo make -j
sudo make install
END_CMDS
)

for MACHINE in "${MACHINES[@]}"; do
    echo "Rebuilding CacheLib on $MACHINE ..."
    ssh "$MACHINE" "$SETUP_CMDS" &
done

wait
echo "All rebuilds finished."