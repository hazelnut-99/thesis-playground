import pandas as pd
import matplotlib.pyplot as plt

def plot_slab_over_time_matplotlib(ax, df, colors, class_ids, x_label):
    x_vals = df['request_id'] / 1_000_000
    for idx, class_id in enumerate(class_ids):
        ax.plot(
            x_vals, df[class_id],
            label=f'Class Id {class_id}',
            color=colors[idx % len(colors)],
            linewidth=2,
            marker='o',
            markersize=2,
            alpha=0.9
        )
    ax.set_xlabel(x_label, fontsize=28)
    ax.set_ylabel('Number of Slabs', fontsize=28)
    handles, labels = ax.get_legend_handles_labels()
    sorted_handles_labels = sorted(zip(labels, handles), key=lambda x: int(x[0].split()[-1]))
    if sorted_handles_labels:
        labels, handles = zip(*sorted_handles_labels)
        ax.legend(handles, labels, title='Class Id', fontsize=22, title_fontsize=24)
    ax.grid(True, linestyle='--', alpha=0.3)
    ax.tick_params(axis='both', labelsize=22)

df1 = pd.read_csv("synth_thesis_static_100_disabled_128_slab_over_time.csv")
df2 = pd.read_csv("synth_thesis_static_103_disabled_128_slab_over_time.csv")

fig, axes = plt.subplots(1, 2, figsize=(18, 8), sharey=True)
colors = ['#636EFA', '#EF553B']
class_ids = sorted([col for col in df1.columns if col in ['0', '1']], key=int)
x_label = 'Request ID (millions)'

plot_slab_over_time_matplotlib(axes[0], df1, colors, class_ids, x_label)
axes[0].set_title("", fontsize=0)  # Remove default title
axes[0].annotate(
    '(a)', xy=(0, 1), xycoords='axes fraction',
    xytext=(-40, 32), textcoords='offset points',
    fontsize=24, fontweight='normal', va='top', ha='left'
)
axes[0].text(
    0.5, 1.10, "workload_1", transform=axes[0].transAxes,
    fontsize=28, fontstyle='italic', ha='center', va='top'
)

plot_slab_over_time_matplotlib(axes[1], df2, colors, class_ids, x_label)
axes[1].set_title("", fontsize=0)  # Remove default title
axes[1].annotate(
    '(b)', xy=(0, 1), xycoords='axes fraction',
    xytext=(-40, 32), textcoords='offset points',
    fontsize=24, fontweight='normal', va='top', ha='left'
)
axes[1].text(
    0.5, 1.10, "workload_2", transform=axes[1].transAxes,
    fontsize=28, fontstyle='italic', ha='center', va='top'
)
plt.suptitle("Number of Allocated Slabs Over Time", fontsize=32)
plt.tight_layout()
plt.savefig("../../figures/slab_over_time_1x2.pdf", dpi=300, bbox_inches='tight')
plt.show()