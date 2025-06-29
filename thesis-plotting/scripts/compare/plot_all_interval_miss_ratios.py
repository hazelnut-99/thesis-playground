import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl

# Modern style for publication quality
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
    "tail-age": "#EF553B",
    "free-mem": "#00CC96",
    "hits": "#FFA15A",
    "marginal-hits": "#AB63FA",
    "optimal": "#19D3F3"
}

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
    "marginal-hits": (0, (3, 1, 1, 1)),  # dash-dot-dot
    "optimal": (0, (1, 1))  # densely dotted
}

df = pd.read_csv("synth_static_202_all_interval_results.csv", sep=None, engine="python")

def plot_metric(metric, ylabel, filename):
    fig, axs = plt.subplots(1, 2, figsize=(12, 5), sharey=False)
    slab_counts = [128, 256]
    subplot_labels = ['(a)', '(b)']

    legend_handles = []
    legend_labels = []
    for i, slab_cnt in enumerate(slab_counts):
        ax = axs[i]
        df_sub = df[df["slab_cnt"] == slab_cnt]
        for strategy in strategy_labels.keys():
            color = strategy_colors.get(strategy, None)
            marker = strategy_markers.get(strategy, "o")
            linestyle = strategy_linestyles.get(strategy, "-")
            df_strat = df_sub[df_sub["rebalance_strategy"] == strategy]
            # Special handling for Disabled and (for miss_ratio plot only) Optimal
            if strategy == "disabled" or (strategy == "optimal" and metric == "miss_ratio"):
                if not df_strat.empty:
                    y_val = df_strat.iloc[0][metric]
                    star = ax.scatter(
                        [0], [y_val], s=180, color=color, marker="*", edgecolor="black", zorder=10, label=strategy_labels[strategy]
                    )
                    # Only add to legend if (disabled) or (optimal and miss_ratio plot)
                    if i == 0 and (strategy == "disabled" or (strategy == "optimal" and metric == "miss_ratio")):
                        legend_handles.append(
                            plt.Line2D([0], [0], color=color, marker="*", linestyle="None", markersize=18, label=strategy_labels[strategy], markeredgecolor="black")
                        )
                        legend_labels.append(strategy_labels[strategy])
                continue
            if df_strat.empty:
                continue
            df_strat = df_strat.sort_values("rebalance_interval")
            x = df_strat["rebalance_interval"] / 1e3
            sc = ax.scatter(x, df_strat[metric], s=5, color=color, alpha=0.7, marker=marker)
            ln, = ax.plot(x, df_strat[metric], color=color, linewidth=2, linestyle=linestyle, label=strategy_labels[strategy], marker=None)
            # Only add to legend if not optimal for rebalanced_slabs plot
            if i == 0 and not (strategy == "optimal" and metric != "miss_ratio"):
                legend_handles.append(
                    plt.Line2D([0], [0], color=color, marker=marker, linestyle=linestyle, linewidth=2, markersize=8, label=strategy_labels[strategy])
                )
                legend_labels.append(strategy_labels[strategy])
        ax.set_xlabel("Rebalance Interval (k requests)")
        ax.set_title(f"Total number of slabs: {slab_cnt}")
        ax.grid(True, linestyle="--", alpha=0.3)
        ax.text(-0.08, 1.08, subplot_labels[i], transform=ax.transAxes, fontsize=15, fontweight='bold', va='top', ha='left')
        if i == 0:
            ax.set_ylabel(ylabel)

    fig.legend(legend_handles, legend_labels, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.15), title="Rebalance Strategy")
    plt.tight_layout(rect=[0, 0.04, 1, 0.97])
    plt.savefig(filename, bbox_inches="tight")
    plt.close(fig)
    
# Figure 1: miss_ratio
plot_metric(
    metric="miss_ratio",
    ylabel="Miss Ratio",
    filename="../../figures/synth_static_202_all_interval_miss_ratio.pdf"
)

# Figure 2: rebalanced_slabs
plot_metric(
    metric="rebalanced_slabs",
    ylabel="Rebalanced Slabs",
    filename="../../figures/synth_static_202_all_interval_rebalanced_slabs.pdf"
)