#!/bin/bash

# All node names in one place
NODES=(
    "Hongshu@clnode055.clemson.cloudlab.us"
    "Hongshu@clnode077.clemson.cloudlab.us"
    "Hongshu@clnode079.clemson.cloudlab.us"
)

PUBKEY_CONTENT=$(cat ./id_rsa_055.pub)

for NODE in "${NODES[@]}"; do
    echo "Copying public key to $NODE ..."
    ssh "$NODE" "mkdir -p ~/.ssh && chmod 700 ~/.ssh
        grep -qxF '$PUBKEY_CONTENT' ~/.ssh/authorized_keys || echo '$PUBKEY_CONTENT' >> ~/.ssh/authorized_keys
        chmod 600 ~/.ssh/authorized_keys"
    echo "Done with $NODE"
done

# # this runs on master node
# for NODE in "${NODES[@]}"; do
#     ssh -o StrictHostKeyChecking=accept-new "$NODE" exit
# done
# ssh -o StrictHostKeyChecking=accept-new Hongshu@clnode134.clemson.cloudlab.us exit

#parallel-ssh -h hosts.txt -i "hostname && whoami"