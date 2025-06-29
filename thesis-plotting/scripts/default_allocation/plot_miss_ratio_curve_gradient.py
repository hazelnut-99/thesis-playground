import os
import pandas as pd
import matplotlib.pyplot as plt

def process_trace_with_marginal_utility(trace_name):
    base_dir = f"/mydata/hongshu/traces/thesis/subtraces/{trace_name}/chunk_0"
    miss_ratios_path = os.path.join(base_dir, "miss_ratios.csv")
    subtrace_stat_path = os.path.join(base_dir, "subtrace_stat.csv")
    miss_ratio_df = pd.read_csv(miss_ratios_path)
    subtrace_stat_df = pd.read_csv(subtrace_stat_path)
    miss_ratio_df['class_size'] = miss_ratio_df['subtrace_name'].map(lambda x: int(x.split('.')[0].split('_')[-1]))
    subtrace_stat_df['class_size'] = subtrace_stat_df['subtrace_name'].map(lambda x: int(x.split('.')[0].split('_')[-1]))

    # Compute total record count for normalization
    total_record_count = subtrace_stat_df['record_count'].sum()

    marginal_utility_dict = {}
    for class_size in sorted(miss_ratio_df['class_size'].unique()):
        class_df = miss_ratio_df[miss_ratio_df['class_size'] == class_size].sort_values('slab_cnt')
        # Get record_count for this class_size from subtrace_stat_df
        record_count = subtrace_stat_df[subtrace_stat_df['class_size'] == class_size]['record_count'].iloc[0]
        record_weight = record_count / total_record_count
        # Build a list of miss_counts, with slab_cnt=0 as record_count
        miss_counts = [1]
        miss_counts += class_df['miss_ratio'].tolist()
        slab_cnts = [0] + class_df['slab_cnt'].tolist()
        # Compute marginal utility: (miss_counts[i-1] - miss_counts[i]) * record_weight
        marginal_utility = []
        for i in range(1, len(miss_counts)):
            marginal_utility.append((miss_counts[i-1] - miss_counts[i]) * record_weight)
        marginal_utility_dict[class_size] = pd.DataFrame({
            'slab_cnt': slab_cnts[1:],
            'marginal_utility': marginal_utility
        })
    return marginal_utility_dict

# Trace info: (trace_name, subplot_title)
trace_info = [
    ("synth_thesis_static_100", "workload_1"),
    ("synth_thesis_static_104", "workload_2")
]

color_list = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692', '#B6E880']
panel_labels = ['(a)', '(b)', '(c)', '(d)']

fig, axes = plt.subplots(1, 2, figsize=(16, 6), sharex=False, sharey=False)
axes = axes.flatten()

for idx, (trace_name, subplot_title) in enumerate(trace_info):
    ax = axes[idx]
    marginal_utility_dict = process_trace_with_marginal_utility(trace_name)
    class_sizes = sorted(marginal_utility_dict.keys())
    color_map = {cs: color_list[i % len(color_list)] for i, cs in enumerate(class_sizes)}

for idx, (trace_name, subplot_title) in enumerate(trace_info):
    ax = axes[idx]
    marginal_utility_dict = process_trace_with_marginal_utility(trace_name)
    class_sizes = sorted(marginal_utility_dict.keys())
    color_map = {cs: color_list[i % len(color_list)] for i, cs in enumerate(class_sizes)}

    for i, class_size in enumerate(class_sizes):
        df_util = marginal_utility_dict[class_size]
        # Limit x axis to 32, drop values larger than 32
        df_util = df_util[df_util['slab_cnt'] <= 64]
        ax.plot(
            df_util['slab_cnt'], df_util['marginal_utility'],
            label=f'Class {i}: {class_size}-byte',
            color=color_map[class_size],
            linewidth=3,
            marker='o',
            markersize=4,
            alpha=0.9
        )

    # Panel label outside the plotting box (top left, outside axes)
    ax.annotate(
        panel_labels[idx],
        xy=(0, 1), xycoords='axes fraction',
        xytext=(-40, 32), textcoords='offset points',
        fontsize=18, fontweight='normal', va='top', ha='left'
    )

    ax.set_title(f"{subplot_title}", fontsize=26, fontstyle='italic', pad=18)
    ax.set_xlabel("Number of Slabs", fontsize=22)
    ax.set_ylabel("Marginal Utility", fontsize=22)
    ax.set_xlim(0, 64)
    ax.tick_params(axis='both', which='major', labelsize=20)
    ax.grid(True, linestyle='--', alpha=0.3)

    # Sort legend by class_size numerical order
    handles, labels = ax.get_legend_handles_labels()
    sorted_legend = sorted(zip(class_sizes, handles, labels), key=lambda x: x[0])
    handles = [h for _, h, _ in sorted_legend]
    labels = [l for _, _, l in sorted_legend]
    ax.legend(handles, labels, title="Allocation Class", fontsize=18, title_fontsize=20, loc='best')
    
plt.suptitle("Normalized Marginal Utility", fontsize=32)
plt.tight_layout(rect=[0, 0, 1, 0.96])

plt.savefig("../../figures/synthetic_single_size_marginal_utility_curve.pdf", dpi=300, bbox_inches='tight')
plt.show()