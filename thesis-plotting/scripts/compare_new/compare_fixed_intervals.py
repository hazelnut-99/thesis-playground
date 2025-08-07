import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# --- CONFIGURATION ---

csv_path = "synth_static_202_fixed_interval_plotting_data.csv"  # Change to your CSV file path

strategy_order = ["disabled", "tail-age", "eviction-rate", "hits", "marginal-hits", "optimal"]
strategy_labels = {
    "disabled": r"$\mathit{Disabled}$",
    "tail-age": r"$\mathit{Tail\text{-}Age}$",
    "eviction-rate": r"$\mathit{Eviction\text{-}Rate}$",
    "hits": r"$\mathit{Hits\text{-}Per\text{-}Slab}$",
    "marginal-hits": r"$\mathit{Marginal\text{-}Hits}$",
    "optimal": r"$\mathit{Optimal}$"
}
strategy_colors = {
    "disabled": "#636EFA",
    "tail-age": "#AB63FA",
    "eviction-rate": "#FFA15A",
    "hits": "#00CC96",
    "marginal-hits": "#EF553B",
    "optimal": "#19D3F3"
}
slab_counts = [32, 64, 128, 256]
x_ticks_labels = [str(x) for x in slab_counts]

label_map = {
    "slab_count": "Total Number of Slabs",
    "miss_ratio": "Miss Ratio",
    "distance_to_optimal_allocation": "Distance to Optimal Allocation",
    "number_of_rebalanced_slabs": "Number of Rebalanced Slabs",
    "rebalance_strategy": "Rebalance Strategy"
}

# Make all fonts bigger
font_title = 32
font_label = 28
font_tick = 24
font_legend = 26
font_panel = 36

df = pd.read_csv(csv_path)

def grouped_barplot(ax, plot_df, y_col, y_label, exclude_optimal=False, is_increase_plot=False):
    if exclude_optimal:
        plot_df = plot_df[plot_df["rebalance_strategy"] != "optimal"]

    plot_df["slab_count"] = pd.Categorical(plot_df["slab_count"], categories=slab_counts, ordered=True)
    plot_df = plot_df.sort_values("slab_count")

    if is_increase_plot:
        # Compute miss ratio increase from optimal
        optimal_df = df[df["rebalance_strategy"] == "optimal"][["slab_count", "miss_ratio"]]
        optimal_dict = dict(zip(optimal_df["slab_count"], optimal_df["miss_ratio"]))
        plot_df["miss_ratio_increase"] = plot_df.apply(
            lambda row: row["miss_ratio"] - optimal_dict.get(row["slab_count"], np.nan), axis=1
        )
        y_col = "miss_ratio_increase"

    n_strategies = len([s for s in strategy_order if (s != "optimal" if (exclude_optimal or is_increase_plot) else True) and s in plot_df["rebalance_strategy"].unique()])
    bar_width = 0.12
    x = np.arange(len(slab_counts))

    for idx, strat in enumerate(strategy_order):
        if (exclude_optimal or is_increase_plot) and strat == "optimal":
            continue
        if strat not in plot_df["rebalance_strategy"].unique():
            continue
        strat_df = plot_df[plot_df["rebalance_strategy"] == strat]
        yvals = []
        for sc in slab_counts:
            row = strat_df[strat_df["slab_count"] == sc]
            if not row.empty:
                yvals.append(row.iloc[0][y_col])
            else:
                yvals.append(np.nan)
        ax.bar(
            x + (idx - (n_strategies - 1)/2) * bar_width,
            yvals,
            width=bar_width,
            label=strategy_labels[strat],
            color=strategy_colors[strat],
            alpha=0.95,
            edgecolor='black'
        )

    ax.set_xlabel(label_map["slab_count"], fontsize=font_label)
    ax.set_ylabel(y_label, fontsize=font_label)
    ax.set_xticks(x)
    ax.set_xticklabels(x_ticks_labels, fontsize=font_tick)
    ax.tick_params(axis="y", labelsize=font_tick)
    ax.grid(True, linestyle="--", alpha=0.3, axis='y')

# --- 2x2 SUBPLOTS ---

fig, axs = plt.subplots(2, 2, figsize=(22, 16))

# (1) slab_count vs miss_ratio
grouped_barplot(
    axs[0, 0], df.copy(), "miss_ratio", "Miss Ratio", exclude_optimal=False
)
axs[0, 0].set_title("Miss Ratio", fontsize=font_title, pad=24)

# (2) Miss ratio increase from optimal (barplot)
grouped_barplot(
    axs[0, 1], df.copy(), "miss_ratio", "Miss Ratio Increase\nfrom the Optimal", exclude_optimal=True, is_increase_plot=True
)
axs[0, 1].set_title("Miss Ratio Increase from the Optimal", fontsize=font_title, pad=24)

# (3) slab_count vs distance_to_optimal_allocation (exclude optimal)
grouped_barplot(
    axs[1, 0], df.copy(), "distance_to_optimal_allocation", "Distance to Optimal Allocation", exclude_optimal=True
)
axs[1, 0].set_title("Distance to Optimal Allocation", fontsize=font_title, pad=24)

# (4) slab_count vs number_of_rebalanced_slabs (exclude optimal)
grouped_barplot(
    axs[1, 1], df.copy(), "number_of_rebalanced_slabs", "Number of Rebalanced Slabs", exclude_optimal=True
)
axs[1, 1].set_title("Number of Rebalanced Slabs", fontsize=font_title, pad=24)

# (a) (b) (c) (d) panel labels
panel_labels = ['(a)', '(b)', '(c)', '(d)']
for ax, label in zip(axs.flat, panel_labels):
    ax.text(-0.13, 1.1, label, transform=ax.transAxes,
            fontsize=22, fontweight='bold', va='top', ha='left')  # Reduced font size from font_panel to 20

# Legend (shared, only once)
handles, labels = axs[0, 0].get_legend_handles_labels()
plt.tight_layout(rect=[0, 0.10, 1, 1])  # Increase bottom margin for legend
fig.legend(
    handles, labels,
    fontsize=font_legend + 4,
    title=label_map["rebalance_strategy"],
    title_fontsize=font_legend + 6,
    loc="lower center",
    bbox_to_anchor=(0.5, -0.08),  # Move legend further down
    ncol=3,
    frameon=False,
)
plt.savefig("synth_202_fixed_interval_barplots.pdf", bbox_inches="tight", dpi=300)
plt.close()