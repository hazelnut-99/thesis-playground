import bisect
import time
import random
from collections import defaultdict

def generate_sequence(length, num_unique):
    """Generate a random sequence with controlled uniqueness."""
    unique_objs = list(range(num_unique))  # Integers for faster hashing
    return [random.choice(unique_objs) for _ in range(length)]

def compute_reuse_distances(sequence):
    """Optimized implementation using bisect."""
    last_access = {}
    access_tree = []
    hist = defaultdict(int)
    
    for t, elem in enumerate(sequence):
        reuse_dist = float('inf')
        
        if elem in last_access:
            last_time = last_access[elem]
            # Calculate reuse distance
            idx = bisect.bisect_right(access_tree, last_time)
            reuse_dist = len(access_tree) - idx
            # Remove previous access - bisect_left is faster for deletion
            del access_tree[bisect.bisect_left(access_tree, last_time)]
        
        hist[reuse_dist] += 1
        bisect.insort(access_tree, t)
        last_access[elem] = t
    
    return hist

# Benchmark
if __name__ == "__main__":
    seq = generate_sequence(1_000_0000, 10_0000)  # 1M accesses, 10K unique
    
    start = time.time()
    distances, hist = compute_reuse_distances(seq)
    elapsed = time.time() - start
    
    print(f"Time: {elapsed:.2f}s")
    print("Top reuse distances:", sorted(hist.items(), key=lambda x: -x[1])[:5])