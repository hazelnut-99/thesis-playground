import os
import json
import pandas as pd
import matplotlib.pyplot as plt

trace_info = [
    ("synth_thesis_static_100", "workload_1"),
    ("synth_thesis_static_103", "workload_2"),
]

alloc_sizes = [2048, 4096]
alloc_labels = {
    2048: "Class 0: 2048 bytes",
    4096: "Class 1: 4096 bytes"
}
color_map = {
    2048: "#636EFA",
    4096: "#EF553B"
}
panel_labels = ['(a)', '(b)', '(c)', '(d)']

fig, axes = plt.subplots(1, 2, figsize=(16, 6), sharex=False, sharey=True)
axes = axes.flatten()
max_x = 512

for idx, (trace_name, workload_label) in enumerate(trace_info):
    ax = axes[idx]
    greedy_allocs_path = f"{trace_name}_greedy_allocs.csv"
    greedy_allocs_df = pd.read_csv(greedy_allocs_path)
    greedy_allocs_df = greedy_allocs_df[greedy_allocs_df['total_slab_cnt'] <= max_x]
    for alloc in alloc_sizes:
        ax.plot(
            greedy_allocs_df['total_slab_cnt'],
            greedy_allocs_df[str(alloc)],
            label=alloc_labels[alloc],
            color=color_map[alloc],
            linewidth=3,
            marker='o',
            markersize=5,
            alpha=0.9
        )
    ax.set_xlim(0, max_x)
    ax.set_xlabel("Total Number of Slabs", fontsize=22)
    ax.set_ylabel("Optimal Allocation", fontsize=22)
    ax.tick_params(axis='x', labelsize=16)
    ax.tick_params(axis='y', labelsize=18)
    ax.legend(title="Allocation Class", fontsize=16, title_fontsize=18, loc='best')
    ax.grid(True, linestyle='--', alpha=0.3)
    # Panel label
    ax.annotate(
        panel_labels[idx],
        xy=(0, 1), xycoords='axes fraction',
        xytext=(-40, 32), textcoords='offset points',
        fontsize=16, fontweight='normal', va='top', ha='left'
    )
    # Workload label
    ax.text(0.5, 1.13, workload_label, fontsize=22, fontstyle='italic', ha='center', va='top', transform=ax.transAxes)

plt.suptitle("Optimal Allocation", fontsize=32)
plt.tight_layout(rect=[0, 0, 1, 0.96], h_pad=2.0, w_pad=2.0)
plt.savefig("../../figures/greedy_optimal_allocation.pdf", dpi=300, bbox_inches='tight')
plt.show()