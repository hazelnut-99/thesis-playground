TRACE_FILE_PATH = "/nfs/hongshu/traces"
WGET_PATH = "https://ftp.pdl.cmu.edu/pub/datasets/twemcacheWorkload/cacheDatasets"
HOME_DIR = "/nfs/hongshu"
CACHEBENCH_BINARY_PATH = "/users/Hongshu/cachelib_v1/opt/cachelib/bin/cachebench"
CACHEBENCH_BINARY_PATH2 = "/users/Hongshu/cachelib_v2/opt/cachelib/bin/cachebench"
MOCK_TIMER_PATH = "/nfs/hongshu/libmock_time.so"

VALID_ALLOCATOR_REBALANCE_COMBINATIONS = {
    "SIMPLE2Q": set(["marginal-hits-old", "marginal-hits-new", "free-mem", "disabled", "hits", "tail-age", "lama", 'eviction-rate']),
    "LRU2Q": set(["marginal-hits-old", "marginal-hits-new", "free-mem", "disabled", "hits", "tail-age", 'eviction-rate']),
    "TINYLFU": set(["free-mem", "disabled", "hits", "tail-age", 'eviction-rate']),
    "TINYLFUTail": set(["marginal-hits-old", "marginal-hits-new"]),
}