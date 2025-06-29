import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl

mpl.rcParams.update({
    "font.size": 16,
    "axes.titlesize": 18,
    "axes.labelsize": 16,
    "legend.fontsize": 13,
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

interval_strategies = [
    "marginal-hits-interval-1k",
    "marginal-hits-interval-10k",
    "marginal-hits-interval-100k",
    "marginal-hits-interval-500k",
    "marginal-hits-interval-1000k"
]
interval_labels = {
    "marginal-hits-interval-1k": "1k",
    "marginal-hits-interval-10k": "10k",
    "marginal-hits-interval-100k": "100k",
    "marginal-hits-interval-500k": "500k",
    "marginal-hits-interval-1000k": "1000k",
}
interval_colors = {
    "marginal-hits-interval-1k": "#EF553B",      # red (changed, was blue)
    "marginal-hits-interval-10k": "#00CC96",     # green
    "marginal-hits-interval-100k": "#FFA15A",    # orange
    "marginal-hits-interval-500k": "#AB63FA",    # purple
    "marginal-hits-interval-1000k": "#19D3F3",   # cyan
    "disabled": "#636EFA",                       # blue, if you ever add disabled
}


df = pd.read_csv("synth_static_202_256_different_intervals_distance_to_optimal.csv")

# ...existing code...

fig, ax = plt.subplots(figsize=(13, 5))  # Wider figure

legend_handles = []
for strategy in interval_strategies:
    df_strat = df[df["rebalance_strategy"] == strategy]
    if df_strat.empty:
        continue
    color = interval_colors.get(strategy, "#333333")
    sc = ax.scatter(
        df_strat["request_id"] / 1e6,
        df_strat["distance_to_optimal_allocation"],
        color=color,
        label=interval_labels[strategy],
        s=5,
        alpha=0.8
    )
    legend_handles.append(
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=color, markersize=16, label=interval_labels[strategy])
    )

ax.set_xlabel("Request ID (Million)")
ax.set_ylabel("Distance to Optimal Allocation")
ax.set_title("Distance to Optimal Allocation Over Time")
ax.grid(True, linestyle="--", alpha=0.3)
ax.legend(
    handles=legend_handles,
    loc="center left",
    bbox_to_anchor=(1.01, 0.5),
    frameon=False,
    title="Rebalance Interval"
)
plt.tight_layout(rect=[0, 0, 0.78, 1])
plt.savefig("../../figures/synth_static_202_256_different_intervals_distance_to_optimal.pdf", bbox_inches="tight")
plt.close(fig)