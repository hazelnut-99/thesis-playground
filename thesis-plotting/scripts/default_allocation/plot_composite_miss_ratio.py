import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl

mpl.rcParams.update({
    "font.size": 18,
    "axes.titlesize": 20,
    "axes.labelsize": 18,
    "legend.fontsize": 15,
    "xtick.labelsize": 15,
    "ytick.labelsize": 15,
    "figure.titlesize": 25,
    "figure.dpi": 300,
})

def process_trace(trace_name):
    base_dir = f"/nfs/hongshu/traces/thesis/subtraces/{trace_name}/chunk_0"
    miss_ratios_path = os.path.join(base_dir, "miss_ratios.csv")
    miss_ratio_df = pd.read_csv(miss_ratios_path) 
    miss_ratio_df['class_size'] = miss_ratio_df['subtrace_name'].map(lambda x: int(x.split('.')[0].split('_')[-1]))
    return miss_ratio_df

# Trace info: (trace_name, subplot_title)
trace_info = [
    ("synth_thesis_static_100", "workload_1"),
    ("synth_thesis_static_103", "workload_2"),
]

color_class0 = "#636EFA"  # Modern blue
color_class1 = "#EF553B"  # Modern red
color_composite = "#00CC96"  # Modern green
color_optimal = "#FFA15A"    # Orange for optimal allocation
color_default = "black" 
panel_labels = ['(a)', '(b)']

max_slabs = 128

fig, axes = plt.subplots(1, 2, figsize=(16, 6), sharey=False)
for idx, (trace_name, subplot_title) in enumerate(trace_info):
    ax_left = axes[idx]
    miss_ratio_df = process_trace(trace_name)
    class_sizes = sorted(miss_ratio_df['class_size'].unique())
    assert class_sizes == [2048, 4096], "Expected class sizes 2048 and 4096"

    # Prepare data for class 0 (2048) and class 1 (4096)
    df0 = miss_ratio_df[miss_ratio_df['class_size'] == 2048].sort_values('slab_cnt').reset_index(drop=True)
    df1 = miss_ratio_df[miss_ratio_df['class_size'] == 4096].sort_values('slab_cnt').reset_index(drop=True)
    
    # Add (0, 1) point if not present for class 0
    if not (df0['slab_cnt'] == 0).any():
        df0 = pd.concat([pd.DataFrame({'slab_cnt': [0], 'miss_ratio': [1.0]}), df0], ignore_index=True)
    # Add (0, 1) point if not present for class 1
    if not (df1['slab_cnt'] == 0).any():
        df1 = pd.concat([pd.DataFrame({'slab_cnt': [0], 'miss_ratio': [1.0]}), df1], ignore_index=True)

    df0 = df0.sort_values('slab_cnt').reset_index(drop=True)
    df1 = df1.sort_values('slab_cnt').reset_index(drop=True)

    # Compute composite: for each allocation, class 0 gets i slabs, class 1 gets (128-i) slabs
    composite = []
    for i in range(max_slabs + 1):
        mr0 = df0[df0['slab_cnt'] == i]['miss_ratio']
        mr1 = df1[df1['slab_cnt'] == (max_slabs - i)]['miss_ratio']
        if not mr0.empty and not mr1.empty:
            composite.append((mr0.values[0] + mr1.values[0]) / 2)
        else:
            composite.append(float('nan'))

    # Find optimal allocation (minimum composite miss ratio)
    composite_arr = pd.Series(composite)
    optimal_idx = composite_arr.idxmin()
    optimal_val = composite_arr.min()

    # Plot class 0 (left y-axis, left-to-right)
    ax_left.plot(df0['slab_cnt'], df0['miss_ratio'], label='Class 0: 2048 bytes', color=color_class0, linewidth=2.5, marker='o', markersize=3)
    ax_left.plot(range(max_slabs + 1), composite, label='Composite', color=color_composite, linewidth=2.5, linestyle=':', marker='s', markersize=3)
    ax_left.set_ylabel("Miss Ratio (Class 0, Composite)", color=color_class0)
    ax_left.set_xlabel("Number of Slabs (Class 0 →)")
    ax_left.tick_params(axis='y', labelcolor=color_class0)
    ax_left.tick_params(axis='x')
    ax_left.set_xlim(0, max_slabs)
    ax_left.set_ylim(0, 1)

    # Plot class 1 (right y-axis, right-to-left)
    ax_right = ax_left.twinx()
    ax_right.plot(max_slabs - df1['slab_cnt'], df1['miss_ratio'], label='Class 1: 4096 bytes', color=color_class1, linewidth=2.5, marker='^', markersize=3)
    ax_right.set_ylabel("Miss Ratio (Class 1)", color=color_class1)
    ax_right.tick_params(axis='y', labelcolor=color_class1)
    ax_right.set_ylim(0, 1)

    # Dual x-axis: bottom for class 0, top for class 1
    ax_top = ax_left.twiny()
    ax_top.set_xlim(ax_left.get_xlim())
    
    # Set same tick positions for both axes
    tick_positions = [0, 32, 64, 96, 128]
    ax_left.set_xticks(tick_positions)
    ax_top.set_xticks(tick_positions)
    ax_top.set_xticklabels([128, 96, 64, 32, 0])  # Class 1 slabs, right-to-left
    ax_top.set_xlabel("Number of Slabs (Class 1 ←)")
    ax_top.tick_params(axis='x')

    # Vertical dashed line at optimal allocation
    ax_left.axvline(optimal_idx, color=color_optimal, linestyle='--', linewidth=2, alpha=0.7, zorder=0)
    ax_left.annotate('Optimal Allocation', xy=(optimal_idx, 0.05), xytext=(optimal_idx+5, 0.45),
                     arrowprops=dict(arrowstyle='->', color=color_optimal), fontsize=18, color=color_optimal)

    # Add vertical dashed line for default allocation
    if idx == 0:
        default_idx = 43
    elif idx == 1:
        default_idx = 21
    ax_left.axvline(default_idx, color=color_default, linestyle='--', linewidth=2, alpha=0.9, zorder=0)
    ax_left.annotate('Default Allocation', xy=(default_idx, 0.15), xytext=(default_idx+5, 0.55),
                     arrowprops=dict(arrowstyle='->', color=color_default), fontsize=18, color=color_default)

    handles_left, labels_left = ax_left.get_legend_handles_labels()
    handles_right, labels_right = ax_right.get_legend_handles_labels()
    legend_dict = dict(zip(labels_left + labels_right, handles_left + handles_right))
    legend_order = [
        'Class 0: 2048 bytes',
        'Class 1: 4096 bytes',
        'Composite'
    ]
    ordered_handles = [legend_dict[lbl] for lbl in legend_order if lbl in legend_dict]
    ordered_labels = [lbl for lbl in legend_order if lbl in legend_dict]
    ax_left.legend(ordered_handles, ordered_labels, loc='best')

    ax_left.set_title(subplot_title, fontstyle='italic', fontsize=24, pad=24)

    # Panel label (a), (b) - keep small
    ax_left.text(-0.08, 1.2, panel_labels[idx], transform=ax_left.transAxes, fontsize=18, va='top', ha='left')

plt.tight_layout()
pdf_name = "../../figures/composite_miss_ratio_dual_panel.pdf"
plt.savefig(pdf_name, bbox_inches='tight')
plt.close(fig)