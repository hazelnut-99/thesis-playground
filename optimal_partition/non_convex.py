import random

class NonConvexTraceGenerator:
    def __init__(self, length=100000, working_set_size=1024, sharp_increase_distance=5000):
        self.length = length
        self.working_set_size = working_set_size
        self.sharp_increase_distance = sharp_increase_distance
        self.trace = self._generate_non_convex_trace()
        self.current_index = -1

    def _generate_non_convex_trace(self):
        """Generates a trace with a potential for non-convex miss ratio."""
        trace = []
        # Initial high locality within the working set
        for _ in range(self.length // 3):
            trace.append(random.randint(0, self.working_set_size - 1))

        # Introduce a phase with periodic reuse
        periodic_items = list(range(self.working_set_size, self.working_set_size + 100)) # A smaller set for periodic reuse
        for _ in range(self.length // 3):
            trace.append(random.choice(periodic_items))
            # Simulate reuse after 'sharp_increase_distance' for some items
            if random.random() < 0.01: # Introduce with a small probability
                index_to_reuse = len(trace) - self.sharp_increase_distance - 1
                if index_to_reuse >= 0 and trace[index_to_reuse] in periodic_items:
                    trace.append(trace[index_to_reuse])

        # Some more general working set access
        for _ in range(self.length - len(trace)):
            trace.append(random.randint(0, self.working_set_size + 199))

        random.shuffle(trace) # Interleave the patterns
        return trace

    def next(self):
        self.current_index = (self.current_index + 1) % self.length
        return self.trace[self.current_index]

    def get_trace(self):
        return self.trace

