import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

mpl.rcParams.update({
    "font.size": 18,
    "axes.titlesize": 24,
    "axes.labelsize": 16,
    "xtick.labelsize": 16,
    "ytick.labelsize": 16,
    "figure.titlesize": 22,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.spines.left": False,
    "axes.spines.bottom": True,
    "figure.dpi": 300,
    "legend.frameon": False,
})

# Example buckets and heights (arbitrary, decreasing)
bucket_labels = ['Bucket 1', 'Bucket 2',  '...', 'Bucket $x_i$', 'Bucket $x_i$+1', '...']
bar_heights = [15, 12, 9, 8, 7, 5]

fig, ax = plt.subplots(figsize=(9, 5))

# Default bar color
bar_colors = ["#636EFA"] * len(bar_heights)
bar_hatch = [None] * len(bar_heights)

# Give Bucket $x_i$ and Bucket $x_i$+1 a different pattern
bar_colors[3] = "#636EFA"
bar_colors[4] = "#636EFA"
bar_hatch[3] = "//"
bar_hatch[4] = "xx"

# ...existing code...

bars = ax.bar(range(len(bar_heights)), bar_heights, color=bar_colors, width=0.6, edgecolor='black')

# Apply hatching to specific bars
for i, bar in enumerate(bars):
    if bar_hatch[i]:
        bar.set_hatch(bar_hatch[i])

# Set x-ticks and labels
ax.set_xticks(range(len(bucket_labels)))
ax.set_xticklabels(bucket_labels)

# Remove y-ticks but keep axis label
ax.set_yticks([])
ax.set_ylabel("Number of Requests\n(Utility)", labelpad=12)
ax.set_xlabel("Reuse Distance (bucketed)", labelpad=10)

# Add vertical arrow and label at x_i bar (index 4)
xi_idx = 3
bar = bars[xi_idx]
bar_top = bar.get_height()
bar_center = bar.get_x() + bar.get_width() / 2

ax.annotate(
    "current allocation: $x_i$ slabs",
    xy=(bar_center, bar_top),
    xytext=(bar_center, bar_top + 5),
    ha='center',
    va='bottom',
    fontsize=16,
    arrowprops=dict(arrowstyle='->', color='black', lw=2)
)

# Remove grid and unnecessary spines
ax.grid(False)
ax.spines['left'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['top'].set_visible(False)

plt.tight_layout()
plt.savefig("../../figures/illustrative_reuse_distance_histogram.pdf", bbox_inches='tight')
plt.close(fig)