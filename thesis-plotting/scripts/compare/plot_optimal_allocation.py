import os
import json
import pandas as pd
import matplotlib.pyplot as plt

trace_name = "synth_static_202"
workload_label = "workload_3"

alloc_sizes = [256, 512, 1024, 2048, 4096]
alloc_labels = {
    256: "Class 0: 256 bytes",
    512: "Class 1: 512 bytes",
    1024: "Class 2: 1024 bytes",
    2048: "Class 3: 2048 bytes",
    4096: "Class 4: 4096 bytes"
}
color_map = {
    256: "#636EFA",
    512: "#EF553B",
    1024: "#00CC96",
    2048: "#AB63FA",
    4096: "#FFA15A"
}

max_x = 512

fig, ax = plt.subplots(figsize=(8, 6))

greedy_allocs_path = f"{trace_name}_optimal_allocs.csv"
greedy_allocs_df = pd.read_csv(greedy_allocs_path)
greedy_allocs_df = greedy_allocs_df[greedy_allocs_df['total_slab_cnt'] <= max_x]

for alloc in alloc_sizes:
    if str(alloc) in greedy_allocs_df.columns:
        ax.plot(
            greedy_allocs_df['total_slab_cnt'],
            greedy_allocs_df[str(alloc)],
            label=alloc_labels[alloc],
            color=color_map[alloc],
            linewidth=3,
            marker='o',
            markersize=3,
            alpha=0.9
        )

ax.set_xlim(0, max_x)
ax.set_xlabel("Total Number of Slabs", fontsize=22)
ax.set_ylabel("Optimal Allocation", fontsize=22)
ax.tick_params(axis='x', labelsize=16)
ax.tick_params(axis='y', labelsize=18)
ax.legend(title="Allocation Class", fontsize=16, title_fontsize=18, loc='best')
ax.grid(True, linestyle='--', alpha=0.3)


plt.suptitle("Optimal Allocation", fontsize=32)
plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig("../../figures/synth_static_202_optimal_allocation.pdf", dpi=300, bbox_inches='tight')
plt.show()