import pandas as pd
import matplotlib.pyplot as plt

trace_info = [
    ("synth_thesis_static_100", "workload_1"),
    ("synth_thesis_static_103", "workload_2"),
]

# --- First Figure: Relative Difference to the Optimal Miss Ratio ---
fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharey=False)
color = '#EF553B'  # Modern color for relative gap

for idx, (trace, title) in enumerate(trace_info):
    df = pd.read_csv(f"{trace}_compare.csv")
    df = df.sort_values("total_slabs")
    relative_gap = (df['miss_ratio_disabled'] - df['miss_ratio_optimal'])
    ax = axes[idx]
    ax.plot(
        df['total_slabs'], relative_gap,
        label='Miss Ratio Increase',
        color=color, linewidth=3, marker='o', markersize=3, alpha=0.9
    )
    ax.set_xlabel("Number of Slabs", fontsize=18)
    ax.set_ylabel("Miss Ratio Increase\nFrom the Optimal", fontsize=18)
    ax.set_title(title, fontsize=20, fontstyle='italic', pad=14)
    ax.tick_params(axis='both', labelsize=15)
    ax.grid(True, linestyle='--', alpha=0.3)

fig.suptitle("Miss Ratio Increase From the Optimal", fontsize=24)
plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig("../../figures/miss_ratio_increase_from_optimal.pdf", dpi=300, bbox_inches='tight')

# --- Second Figure: Distance to the Optimal Allocation ---
fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharey=False)
color = '#00CC96'

for idx, (trace, title) in enumerate(trace_info):
    df = pd.read_csv(f"{trace}_compare.csv")
    df = df.sort_values("total_slabs")
    ax = axes[idx]
    ax.plot(
        df['total_slabs'], df['distance_to_optimal'],
        label='Distance to Optimal',
        color=color, linewidth=3, marker='o', markersize=3, alpha=0.9
    )
    ax.set_xlabel("Number of Slabs", fontsize=18)
    ax.set_ylabel("Distance to Optimal Allocation", fontsize=18)
    ax.set_title(title, fontsize=20, fontstyle='italic', pad=14)
    ax.tick_params(axis='both', labelsize=15)
    ax.grid(True, linestyle='--', alpha=0.3)

fig.suptitle("Distance to Optimal Allocation of the Default Allocation", fontsize=24)
plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig("../../figures/compare_distance_to_optimal.pdf", dpi=300, bbox_inches='tight')
plt.show()