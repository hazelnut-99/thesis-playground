import os
import json
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
alloc_ypos = {
    2048: 0,
    4096: 1
}
alloc_yticks = [0, 1]
alloc_yticklabels = ["Class 0", "Class 1"]
color_map = {
    2048: "#636EFA",
    4096: "#EF553B"
}
panel_labels = ['(a)', '(b)']

fig, axes = plt.subplots(1, 2, figsize=(16, 6), sharex=False)
axes = axes.flatten()
max_x = 512

for idx, (trace_name, workload_label) in enumerate(trace_info):
    ax = axes[idx]
    greedy_order_path = f"{trace_name}_greedy_order.json"
    with open(greedy_order_path, "r") as f:
        greedy_order = json.load(f)
    # Only plot up to slab index 512
    x_vals = list(range(1, min(len(greedy_order), max_x) + 1))
    for alloc in alloc_sizes:
        y_vals = [alloc_ypos[alloc] if (i < max_x and v == alloc) else None for i, v in enumerate(greedy_order)]
        ax.scatter(
            x_vals, y_vals[:len(x_vals)],
            label=alloc_labels[alloc],
            color=color_map[alloc],
            s=10,
            alpha=1.0,
            edgecolors='none'
        )
    ax.set_xlim(0, max_x)
    ax.set_yticks(alloc_yticks)
    ax.set_yticklabels(alloc_yticklabels, fontsize=18)
    ax.set_xlabel("Slab index", fontsize=22)
    ax.set_ylabel("Allocation Class", fontsize=22)
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

plt.suptitle("Greedy Allocation Order", fontsize=32)
plt.tight_layout(rect=[0, 0, 1, 0.96], h_pad=2.0, w_pad=2.0)
plt.savefig("../../figures/greedy_allocation_order_1x2.pdf", dpi=300, bbox_inches='tight')
plt.show()