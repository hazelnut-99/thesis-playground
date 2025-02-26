# Timer

### Timer in CacheLib mostly replies on std::chrono

 [(Time.h util class)](https://github.com/facebook/CacheLib/blob/main/cachelib/common/Time.h)

- e.g. LRU replies on std::chrono [(code snippet)](https://github.com/facebook/CacheLib/blob/5db3b00bcd45da0b20c186b332e16387d285038e/cachelib/allocator/MMLru.h#L526)
- `PoolRebalancer` works as a daemon thread that periodically wakes up. Sleeps are implemented using the [std::condition_variable::wait_until](https://en.cppreference.com/w/cpp/thread/condition_variable/wait_until), which under the hood replies on `std::chrono` as the clock. **[[PeriodicWorker in CacheLib]](https://github.com/facebook/CacheLib/blob/5db3b00bcd45da0b20c186b332e16387d285038e/cachelib/common/PeriodicWorker.cpp#L59)**
- The `Reaper` daemon (for ttls) also uses the same logic as `PoolRebalancer`
- Looks like even in unit tests, they use the real-world clock to sleep as well [(code snippet)](https://github.com/facebook/CacheLib/blob/5db3b00bcd45da0b20c186b332e16387d285038e/cachelib/allocator/tests/BaseAllocatorTest.h#L331)

**Conclusion for now:** the library doesn’t provide a straight-forward way to override the timer.

### Concerns with rebalancing frequencies

Suppose we can figure out a way to enforce CacheLib to use a MockTimer that ticks according to the trace time. If we finish replaying a 1 hour trace within 1 minute, the rebalancer wakes up under the MockTimer 3600 times (instead of 60). Will it incur too many overheads? Because in reality the rebalancing cost is amortized to 1 hour.