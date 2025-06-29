import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl

mpl.rcParams.update({
    "font.size": 16,
    "axes.titlesize": 18,
    "axes.labelsize": 16,
    "legend.fontsize": 14,
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

strategy_order = [
    "disabled",
    "marginal-hits-interval-1k",
    "marginal-hits-interval-10k",
    "marginal-hits-interval-100k",
    "marginal-hits-interval-500k",
    "marginal-hits-interval-1000k"
]
strategy_labels = {
    "disabled": r"$\mathit{Disabled}$",
    "marginal-hits-interval-1k": "1k",
    "marginal-hits-interval-10k": "10k",
    "marginal-hits-interval-100k": "100k",
    "marginal-hits-interval-500k": "500k",
    "marginal-hits-interval-1000k": "1000k",
}
strategy_colors = {
    "disabled": "#636EFA",                # blue
    "marginal-hits-interval-1k": "#EF553B",   # red
    "marginal-hits-interval-10k": "#00CC96",  # green
    "marginal-hits-interval-100k": "#FFA15A", # orange
    "marginal-hits-interval-500k": "#AB63FA", # purple
    "marginal-hits-interval-1000k": "#19D3F3",# cyan
}
strategy_markers = {
    "disabled": "*",
    "marginal-hits-interval-1k": "o",
    "marginal-hits-interval-10k": "s",
    "marginal-hits-interval-100k": "D",
    "marginal-hits-interval-500k": "^",
    "marginal-hits-interval-1000k": "v",
}
strategy_linestyles = {
    "disabled": "None",
    "marginal-hits-interval-1k": "-",
    "marginal-hits-interval-10k": "-",
    "marginal-hits-interval-100k": "-",
    "marginal-hits-interval-500k": "-",
    "marginal-hits-interval-1000k": "-",
}

df = pd.read_csv("synth_static_202_different_intervals_miss_ratios_256.csv")
df = df[df["request_id"] >= 2.9e6]
fig, ax = plt.subplots(figsize=(13, 5))

legend_handles = []
for strategy in strategy_order:
    df_strat = df[df["rebalance_strategy"] == strategy]
    if df_strat.empty:
        continue
    color = strategy_colors[strategy]
    marker = strategy_markers[strategy]
    linestyle = strategy_linestyles[strategy]
    # Sort by request_id
    df_strat = df_strat.sort_values("request_id")
    x = df_strat["request_id"] / 1e6
    y = df_strat["miss_ratio"]
    # Label: Disabled or Marginal-Hits (interval xxk)
    if strategy == "disabled":
        label = r"$\mathit{Disabled}$"
    else:
        interval = strategy_labels[strategy]
        label = rf"$\mathit{{Marginal\text{{-}}Hits}}$ (interval {interval})"
    # Scatter and line for all strategies
    sc = ax.scatter(x, y, color=color, marker=marker, s=3, alpha=0.8, label=label)
    ln, = ax.plot(x, y, color=color, linestyle=linestyle, linewidth=2, alpha=0.8)
    # Legend handle
    legend_handles.append(
        plt.Line2D([0], [0], marker=marker, color=color,
                   markerfacecolor=color, markeredgecolor=color,
                   markersize=11, linestyle="-", label=label)
    )

ax.set_xlabel("Request ID (Million)")
ax.set_ylabel("Miss Ratio")
ax.set_title("Miss Ratio Over Time")
ax.grid(True, linestyle="--", alpha=0.3)
ax.legend(
    handles=legend_handles,
    loc="center left",
    bbox_to_anchor=(1.01, 0.5),
    frameon=False,
    title="Rebalance Strategy"
)
plt.tight_layout(rect=[0, 0, 0.78, 1])
plt.savefig("../../figures/synth_static_202_different_intervals_miss_ratios_256.pdf", bbox_inches="tight")
plt.close(fig)