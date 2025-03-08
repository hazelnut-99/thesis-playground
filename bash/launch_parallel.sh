#!/bin/bash

# Define the command to run
command="./bin/cachebench --json_test_config ./test_configs/trace_replay/oracle_general/config_ogtrace.json -progress=50000"

# Launch 10 parallel processes
for i in {1..10}; do
    # Redirect stdout and stderr to separate files
    LD_PRELOAD=/users/Hongshu/libmock_time.so $command > "output_$i.log" 2> "error_$i.log" &
done

# Wait for all background processes to finish
wait

echo "All processes have completed."