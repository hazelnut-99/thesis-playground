#define _GNU_SOURCE
#include <iostream>
#include <chrono>
#include <ctime>
#include <dlfcn.h>
#include <time.h>
#include <mutex>

// Define function pointer type for original clock_gettime
typedef int (*clock_gettime_t)(clockid_t, struct timespec*);

static clock_gettime_t real_clock_gettime = nullptr;
static std::mutex time_mutex;
static struct timespec mock_time = {0, 0};
static bool mock_time_set = false;

// Function to set mock time (Exposed via shared library)
extern "C" void set_mock_time(time_t sec, long nsec) {
    std::lock_guard<std::mutex> lock(time_mutex);
    mock_time.tv_sec = sec;
    mock_time.tv_nsec = nsec;
    mock_time_set = true;
}

// Hooked clock_gettime function
extern "C" int clock_gettime(clockid_t clk_id, struct timespec* tp) {
    if (!real_clock_gettime) {
        real_clock_gettime = (clock_gettime_t)dlsym(RTLD_NEXT, "clock_gettime");
    }

    std::lock_guard<std::mutex> lock(time_mutex);

    if (mock_time_set) {
        tp->tv_sec = mock_time.tv_sec;
        tp->tv_nsec = mock_time.tv_nsec;
        return 0;
    }

    return real_clock_gettime(clk_id, tp);
}

// Initialization
__attribute__((constructor)) void init() {
    real_clock_gettime = (clock_gettime_t)dlsym(RTLD_NEXT, "clock_gettime");
}
