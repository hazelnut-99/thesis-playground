
# open
sudo sh -c 'echo 1 >/proc/sys/kernel/perf_event_paranoid'
# close
sudo sh -c 'echo 2 >/proc/sys/kernel/perf_event_paranoid'
