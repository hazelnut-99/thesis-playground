import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

mpl.rcParams.update({
    "font.size": 18,
    "axes.titlesize": 24,
    "axes.labelsize": 16,
    "xtick.labelsize": 12,
    "ytick.labelsize": 16,
    "figure.titlesize": 22,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.spines.left": False,
    "axes.spines.bottom": True,
    "figure.dpi": 300,
    "legend.frameon": False,
})

# Data for left plot (class i)
bucket_labels = ['Bucket 1', '...', 'Bucket $x_i$-1', 'Bucket $x_i$', 'Bucket $x_i$+1', '...']
bar_heights = [30, 26, 24, 14, 10, 8]

# Data for right plot (class j)
bucket_labels_2 = ['Bucket 1', '...', 'Bucket $x_j$-1', 'Bucket $x_j$', 'Bucket $x_j$+1', '...']
bar_heights_2 = [34, 32, 30, 28, 18, 10]

fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)

# --- Left plot (class i) ---
ax = axes[0]
bar_colors = ["#636EFA"] * len(bar_heights)
bar_hatch = [None] * len(bar_heights)
# Special marks for i-1, i, i+1
bar_hatch[2] = "//"
bar_hatch[3] = "xx"
bar_hatch[4] = "\\\\"

bars = ax.bar(range(len(bar_heights)), bar_heights, color=bar_colors, width=0.6, edgecolor='black')
for i, bar in enumerate(bars):
    if bar_hatch[i]:
        bar.set_hatch(bar_hatch[i])

ax.set_xticks(range(len(bucket_labels)))
ax.set_xticklabels(bucket_labels)
ax.set_yticks([])
ax.set_ylabel("Number of Requests\n(Utility)", labelpad=12)
ax.set_xlabel("Reuse Distance (bucketed)", labelpad=10)
ax.set_title("Class $i$")

# Arrow for x_i
xi_idx = 3
bar = bars[xi_idx]
bar_top = bar.get_height()
bar_center = bar.get_x() + bar.get_width() / 2
ax.annotate(
    "current allocation: $x_i$ slabs",
    xy=(bar_center, bar_top),
    xytext=(bar_center, bar_top + 16),
    ha='center',
    va='bottom',
    fontsize=14,
    arrowprops=dict(arrowstyle='->', color='black', lw=2)
)

# --- Right plot (class j) ---
ax2 = axes[1]
bar_colors_2 = ["#00B894"] * len(bar_heights_2)
bar_hatch_2 = [None] * len(bar_heights_2)
# Special marks for j-1, j, j+1
bar_hatch_2[2] = "//"
bar_hatch_2[3] = "xx"
bar_hatch_2[4] = "\\\\"

bars2 = ax2.bar(range(len(bar_heights_2)), bar_heights_2, color=bar_colors_2, width=0.6, edgecolor='black')
for i, bar in enumerate(bars2):
    if bar_hatch_2[i]:
        bar.set_hatch(bar_hatch_2[i])

ax2.set_xticks(range(len(bucket_labels_2)))
ax2.set_xticklabels(bucket_labels_2)
ax2.set_yticks([])
ax2.set_xlabel("Reuse Distance (bucketed)", labelpad=10)
ax2.set_title("Class $j$")

# Arrow for x_j
xj_idx = 3
bar2 = bars2[xj_idx]
bar2_top = bar2.get_height()
bar2_center = bar2.get_x() + bar2.get_width() / 2
ax2.annotate(
    "current allocation: $x_j$ slabs",
    xy=(bar2_center, bar2_top),
    xytext=(bar2_center, bar2_top + 4),
    ha='center',
    va='bottom',
    fontsize=14,
    arrowprops=dict(arrowstyle='->', color='black', lw=2)
)

# Remove grid and unnecessary spines for both axes
for axx in axes:
    axx.grid(False)
    axx.spines['left'].set_visible(False)
    axx.spines['right'].set_visible(False)
    axx.spines['top'].set_visible(False)

plt.tight_layout()
plt.savefig("../../figures/illustrative_reuse_distance_histogram_side_by_side.pdf", bbox_inches='tight')
plt.close(fig)