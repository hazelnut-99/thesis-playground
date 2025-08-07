import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl

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

class_colors = {
    0: "#636EFA",  # blue
    1: "#EF553B",  # red
    2: "#00CC96",  # green
    3: "#FFA15A",  # orange
    4: "#AB63FA",  # purple
}
class_labels = {
    0: "Class 0: 256-byte",
    1: "Class 1: 512-byte",
    2: "Class 2: 1024-byte",
    3: "Class 3: 2048-byte",
    4: "Class 4: 4096-byte",
}
strategy_labels = {
    "disabled": r"$\mathit{Disabled}$",
    "tail-age": r"$\mathit{LRU\text{-}Tail\text{-}Age}$",
    "eviction-rate": r"$\mathit{Eviction\text{-}Rate}$",
    "hits": r"$\mathit{Hits\text{-}Per\text{-}Slab}$",
    "marginal-hits": r"$\mathit{Marginal\text{-}Hits}$",
    "optimal": r"$\mathit{Optimal}$"
}

df = pd.read_csv("synth_static_202_stats_detail.csv")
df = df[df["slab_count"] == 256]

def plot_figure(strategy, key_a, ylabel_a, key_b, ylabel_b, filename, title_a=None, title_b=None, y_a_ticks=None, aggregate_window=1):
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.5), sharey=False)
    vline_x = 2.9
    vline_request_id = int(vline_x * 1e6)
    star_map = {0: 89, 1: 26, 2: 97, 3: 28, 4: 16}

    # Subfigure a
    ax = axs[0]
    df_a = df[
        (df["rebalance_strategy"] == strategy) &
        (df["key"] == key_a) &
        (df["request_id"] >= vline_request_id)
    ]
    
    # Aggregate neighboring points if aggregate_window is specified
    if aggregate_window is not None and aggregate_window > 1:
        aggregated_rows = []
        for class_id in df_a["class_id"].unique():
            class_data = df_a[df_a["class_id"] == class_id].sort_values("request_id").reset_index(drop=True)
            
            # Group consecutive points within the aggregate_window
            for i in range(0, len(class_data), aggregate_window):
                window_data = class_data.iloc[i:i+aggregate_window]
                if len(window_data) > 0:
                    aggregated_row = {
                        "rebalance_strategy": strategy,
                        "key": key_a,
                        "class_id": class_id,
                        "request_id": window_data["request_id"].mean(),
                        "value": window_data["value"].mean(),
                        "slab_count": window_data["slab_count"].iloc[0]
                    }
                    aggregated_rows.append(aggregated_row)
        
        df_a = pd.DataFrame(aggregated_rows)
    
    print(f"Plotting {key_a} for strategy {strategy} with {len(df_a)} data points")
    for class_id, group in df_a.groupby("class_id"):
        group_sorted = group.sort_values("request_id")
        x = group_sorted["request_id"] / 1e6
        y = group_sorted["value"]
        ax.plot(x, y, label=class_labels[class_id], color=class_colors[class_id], linewidth=2)
    ax.set_xlabel("Request ID (Million)")
    ax.set_ylabel(ylabel_a)
    if y_a_ticks is not None:
        ax.set_yticks(y_a_ticks)
    if title_a:
        ax.set_title(title_a)
    
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.text(-0.08, 1.12, "(1)", transform=ax.transAxes, fontsize=15, fontweight='bold', va='top', ha='left')

    # Subfigure b (add star markers)
    ax = axs[1]
    df_b = df[
        (df["rebalance_strategy"] == strategy) &
        (df["key"] == key_b) &
        (df["request_id"] >= vline_request_id)
    ]
    max_request_id = df_b["request_id"].max() if not df_b.empty else vline_request_id
    star_x = max_request_id / 1e6 + 2
    for class_id, group in df_b.groupby("class_id"):
        group_sorted = group.sort_values("request_id")
        x = group_sorted["request_id"] / 1e6
        y = group_sorted["value"]
        ax.plot(x, y, label=class_labels[class_id], color=class_colors[class_id], linewidth=2)
        # Add star marker
        ax.plot(star_x, star_map[class_id], marker="*", color=class_colors[class_id], markersize=8, linestyle="None", zorder=5)
    ax.set_xlabel("Request ID (Million)")
    ax.set_ylabel(ylabel_b)
    if title_b:
        ax.set_title(title_b)
    
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.text(-0.08, 1.12, "(2)", transform=ax.transAxes, fontsize=15, fontweight='bold', va='top', ha='left')

    handles, labels = axs[0].get_legend_handles_labels()
    fig.legend(
        handles, labels,
        loc="center left",
        bbox_to_anchor=(1.01, 0.5),
        ncol=1,
        frameon=False,
        title="Allocation Class"
    )
    plt.tight_layout(rect=[0, 0.04, 1, 0.97])
    plt.savefig(filename, bbox_inches="tight")
    plt.close(fig)

# (1) tail-age
plot_figure(
    strategy="tail-age",
    key_a="tail_age",
    ylabel_a="Tail Age (s)",
    key_b="num_slabs",
    ylabel_b="Number of Slabs",
    filename="synth_static_202_stats_detail_tail_age.pdf",
    aggregate_window=2
)

# (2) eviction-rate
plot_figure(
    strategy="eviction-rate",
    key_a="evictions",
    ylabel_a="Number of Evictions",
    key_b="num_slabs",
    ylabel_b="Number of Slabs",
    filename="synth_static_202_stats_detail_eviction_rate.pdf",
    aggregate_window=2
)

# (3) hits
plot_figure(
    strategy="hits",
    key_a="hits_per_slab",
    ylabel_a="Average Hits Per Slab",
    key_b="num_slabs",
    ylabel_b="Number of Slabs",
    filename="synth_static_202_stats_detail_hits.pdf",
    aggregate_window=2
)

# (4) marginal-hits
plot_figure(
    strategy="marginal-hits",
    key_a="tail_hits",
    ylabel_a="Tail Hits",
    key_b="num_slabs",
    ylabel_b="Number of Slabs",
    filename="synth_static_202_stats_detail_marginal_hits.pdf",
    aggregate_window=2
)