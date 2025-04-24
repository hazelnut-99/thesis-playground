import numpy as np
from collections import OrderedDict

class NonConvexTraceGenerator:
    def __init__(self, m, alpha=1.2, seed=None):
        """
        Same interface as ZipfGenerator.
        - m: Number of distinct objects (e.g., 100)
        - alpha: "Skewness" (unused here, but kept for compatibility)
        - seed: Random seed (optional)
        """
        np.random.seed(seed)
        self.m = m
        self.alpha = alpha  # Not used, but kept for interface consistency
        
        # Define working sets (A, B, C) as partitions of `m` objects
        self.A = list(range(0, m//2))           # Hot working set (50% of objects)
        self.B = list(range(m//2, 3*m//4))      # Disruptor set (25%)
        self.C = list(range(3*m//4, m))         # Critical set (25%)
        
        self.phase = 0  # Tracks which phase we're in
        self.step = 0   # Counts accesses within phase

    def next(self):
        """
        Returns the next object in the trace.
        Alternates between phases to create non-convexity.
        """
        if self.phase == 0:
            # Phase 1: Hot working set (A)
            obj = np.random.choice(self.A)
            self.step += 1
            if self.step >= 1000:  # Switch after 1000 accesses
                self.phase = 1
                self.step = 0
        elif self.phase == 1:
            # Phase 2: Mix A and B (creates plateau)
            if np.random.rand() < 0.8:
                obj = np.random.choice(self.A)
            else:
                obj = np.random.choice(self.B)
            self.step += 1
            if self.step >= 1000:
                self.phase = 2
                self.step = 0
        elif self.phase == 2:
            # Phase 3: Return to A (B lingers)
            obj = np.random.choice(self.A)
            self.step += 1
            if self.step >= 1000:
                self.phase = 3
                self.step = 0
        else:
            # Phase 4: Introduce C (creates cliff)
            if np.random.rand() < 0.7:
                obj = np.random.choice(self.A)
            else:
                obj = np.random.choice(self.C)
        
        return obj

# Initialize generator (same interface as ZipfGenerator)
generator = NonConvexTraceGenerator(m=100, alpha=1.2)

# Generate a trace (e.g., 10,000 accesses)
trace = [generator.next() for _ in range(10000)]

# Simulate LRU miss rates
cache_sizes = np.arange(10, 100, 5)
miss_rates = []
for C in cache_sizes:
    cache = OrderedDict()
    misses = 0
    for obj in trace:
        if obj in cache:
            cache.move_to_end(obj)
        else:
            misses += 1
            if len(cache) >= C:
                cache.popitem(last=False)
            cache[obj] = True
    miss_rates.append(misses / len(trace))

# Plot
import matplotlib.pyplot as plt
plt.plot(cache_sizes, miss_rates, marker='o')
plt.xlabel("Cache Size")
plt.ylabel("Miss Rate")
plt.title("Non-Convex Miss Curve (Custom Generator)")
plt.grid()
plt.show()