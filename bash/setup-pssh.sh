#!/bin/bash

# All node names in one place
NODES=(
    "Hongshu@clnode370.clemson.cloudlab.us"
    "Hongshu@clnode355.clemson.cloudlab.us"
    "Hongshu@clnode337.clemson.cloudlab.us"
    "Hongshu@clnode322.clemson.cloudlab.us"
    "Hongshu@clnode332.clemson.cloudlab.us"
)

PUBKEY_CONTENT=$(cat ./id_rsa_370.pub)

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


# on master
# ssh -o StrictHostKeyChecking=accept-new Hongshu@clnode139.clemson.cloudlab.us
# ssh -o StrictHostKeyChecking=accept-new Hongshu@clnode290.clemson.cloudlab.us
# ssh -o StrictHostKeyChecking=accept-new Hongshu@clnode287.clemson.cloudlab.us
# ssh -o StrictHostKeyChecking=accept-new Hongshu@clnode289.clemson.cloudlab.us
# ssh -o StrictHostKeyChecking=accept-new Hongshu@clnode302.clemson.cloudlab.us
# ssh -o StrictHostKeyChecking=accept-new Hongshu@clnode314.clemson.cloudlab.us
#parallel-ssh -h hosts.txt -i "hostname && whoami"


ssh -o StrictHostKeyChecking=accept-new Hongshu@clnode334.clemson.cloudlab.us
ssh -o StrictHostKeyChecking=accept-new Hongshu@clnode394.clemson.cloudlab.us
ssh -o StrictHostKeyChecking=accept-new Hongshu@clnode374.clemson.cloudlab.us


