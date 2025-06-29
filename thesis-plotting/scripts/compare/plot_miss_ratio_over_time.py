import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.lines as mlines

# Use a modern style for publication quality
mpl.rcParams.update({
    "font.size": 16,
    "axes.titlesize": 18,
    "axes.labelsize": 16,
    "legend.fontsize": 15,
    "xtick.labelsize": 15,
    "ytick.labelsize": 15,
    "figure.titlesize": 19,
    "axes.titlepad": 12,
    "axes.labelpad": 8,
    "legend.frameon": False,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 300,
})

strategy_labels = {
    "disabled": r"$\mathit{Disabled}$",
    "tail-age": r"$\mathit{LRU\text{-}Tail\text{-}Age}$",
    "free-mem": r"$\mathit{Free\text{-}Memory}$",
    "hits": r"$\mathit{Hits\text{-}Per\text{-}Slab}$",
    "marginal-hits": r"$\mathit{Marginal\text{-}Hits}$",
    "optimal": r"$\mathit{Optimal}$"
}
strategy_colors = {
    "disabled": "#636EFA",
    "tail-age": "#AB63FA",
    "free-mem": "#FFA15A",
    "hits": "#00CC96",
    "marginal-hits": "#EF553B",
    "optimal": "#19D3F3"
}
# Define marker and line styles for each strategy
strategy_markers = {
    "disabled": "o",
    "tail-age": "s",
    "free-mem": "D",
    "hits": "^",
    "marginal-hits": "v",
    "optimal": "P"
}
strategy_linestyles = {
    "disabled": "-",
    "tail-age": "--",
    "free-mem": "-.",
    "hits": ":",
    "marginal-hits": (0, (3, 1, 1, 1)),
    "optimal": (0, (1, 1))
}

# Read data
df = pd.read_csv("synth_static_202_miss_ratio_over_time.csv")


def plot_metric_over_time(metric, ylabel, title, filename):
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)
    slab_counts = [128, 256]
    subplot_labels = ['(a)', '(b)']
    legend_handles = []
    # Choose a neutral annotation color
    annotation_color = "#444444"
    for i, slab_count in enumerate(slab_counts):
        ax = axs[i]
        df_sub = df[df["slab_count"] == slab_count]
        for strategy, group in df_sub.groupby("rebalance_strategy"):
            label = strategy_labels.get(strategy, strategy)
            color = strategy_colors.get(strategy, None)
            marker = strategy_markers.get(strategy, "o")
            linestyle = strategy_linestyles.get(strategy, "-")
            group_sorted = group.sort_values("request_id")
            x = group_sorted["request_id"] / 1e6
            y = group_sorted[metric]
            # Scatter with unique marker per strategy
            ax.scatter(x, y, s=3, color=color, alpha=0.7, marker=marker)
            # Line
            ax.plot(x, y, color=color, linewidth=2, linestyle=linestyle)
            # Only add one handle per strategy (for the first subplot)
            if i == 0:
                handle = mlines.Line2D([], [], color=color, marker=marker, linestyle=linestyle,
                                       markersize=7, linewidth=2, label=label)
                legend_handles.append(handle)
        ax.set_title(f"Total number of slabs: {slab_count}")
        ax.set_xlabel("Request ID (Million)")
        if i == 0:
            ax.set_ylabel(ylabel)
        ax.grid(True, linestyle="--", alpha=0.3)
        # Add subplot label (a), (b)
        ax.text(-0.08, 1.08, subplot_labels[i], transform=ax.transAxes, fontsize=15, fontweight='bold', va='top', ha='left')
        # Add vertical dashed line and annotation
        if slab_count == 128:
            vline_x = 1.0
        elif slab_count == 256:
            vline_x = 2.9
        else:
            vline_x = None
        if vline_x is not None:
            ax.axvline(x=vline_x, color=annotation_color, linestyle="--", linewidth=1.5, alpha=0.8)
            ax.annotate(
                "All slabs allocated",
                xy=(vline_x, ax.get_ylim()[1]),
                xytext=(5, -25),
                textcoords="offset points",
                ha="left",
                va="top",
                fontsize=11,
                color=annotation_color,
                fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=annotation_color, lw=1, alpha=0.7)
            )
    fig.legend(handles=legend_handles, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.15), title = "Rebalance Strategy")
    fig.suptitle(title)
    plt.tight_layout(rect=[0, 0.04, 1, 0.97])
    plt.savefig(filename, bbox_inches="tight")
    plt.close(fig)
    
# Plot 1: Miss Ratio Over Time
plot_metric_over_time(
    metric="miss_ratio",
    ylabel="Miss Ratio",
    title="Miss Ratio Over Time",
    filename="../../figures/synth_static_202_miss_ratio_over_time.pdf"
)