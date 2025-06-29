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
    "free-mem": r"$\mathit{Free\text{-}Memory}$",
    "hits": r"$\mathit{Hits\text{-}Per\text{-}Slab}$",
    "marginal-hits": r"$\mathit{Marginal\text{-}Hits}$",
    "optimal": r"$\mathit{Optimal}$"
}

df = pd.read_csv("synth_static_202_stats_detail.csv")
df = df[df["slab_count"] == 256]

def plot_figure(strategy, key_a, ylabel_a, key_b, ylabel_b, filename, title_a=None, title_b=None, y_a_ticks=None):
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
    ax.axvline(x=vline_x, color="#444444", linestyle="--", linewidth=1.5, alpha=0.8)
    
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
    ax.axvline(x=vline_x, color="#444444", linestyle="--", linewidth=1.5, alpha=0.8)
    
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
    filename="../../figures/synth_static_202_stats_detail_tail_age.pdf"
)

# (2) free-mem
plot_figure(
    strategy="free-mem",
    key_a="free_slabs",
    ylabel_a="Number of Free Slabs",
    key_b="num_slabs",
    ylabel_b="Number of Slabs",
    filename="../../figures/synth_static_202_stats_detail_free_mem.pdf",
    y_a_ticks=[-1, 0, 1]
)

# (3) hits
plot_figure(
    strategy="hits",
    key_a="hits_per_slab",
    ylabel_a="Average Hits Per Slab",
    key_b="num_slabs",
    ylabel_b="Number of Slabs",
    filename="../../figures/synth_static_202_stats_detail_hits.pdf"
)

# (4) marginal-hits
plot_figure(
    strategy="marginal-hits",
    key_a="marginal_hits",
    ylabel_a="Tail Hits",
    key_b="num_slabs",
    ylabel_b="Number of Slabs",
    filename="../../figures/synth_static_202_stats_detail_marginal_hits.pdf"
)