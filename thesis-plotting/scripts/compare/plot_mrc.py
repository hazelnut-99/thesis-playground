import os
import pandas as pd
import matplotlib.pyplot as plt

def process_trace(trace_name):
    base_dir = f"/mydata/hongshu/traces/thesis/subtraces/{trace_name}/chunk_0"
    miss_ratios_path = os.path.join(base_dir, "miss_ratios.csv")
    miss_ratio_df = pd.read_csv(miss_ratios_path) 
    miss_ratio_df['class_size'] = miss_ratio_df['subtrace_name'].map(lambda x: int(x.split('.')[0].split('_')[-1]))
    return miss_ratio_df

# Only one trace to plot
trace_name = "synth_static_202"
subplot_title = "workload_3"

# Modern color palette
color_list = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692', '#B6E880']

fig, ax = plt.subplots(figsize=(8, 6))

miss_ratio_df = process_trace(trace_name)

# Sort class_sizes numerically
class_sizes = sorted(miss_ratio_df['class_size'].unique())
for class_size in class_sizes:
    if not ((miss_ratio_df['class_size'] == class_size) & (miss_ratio_df['slab_cnt'] == 0)).any():
        miss_ratio_df = pd.concat([
            miss_ratio_df,
            pd.DataFrame([{
                'class_size': class_size,
                'slab_cnt': 0,
                'miss_ratio': 1,
                'subtrace_name': ''  # or any placeholder if needed
            }])
        ], ignore_index=True)
color_map = {cs: color_list[i % len(color_list)] for i, cs in enumerate(class_sizes)}
legend_labels = []

for i, class_size in enumerate(class_sizes):
    sub_df = miss_ratio_df[miss_ratio_df['class_size'] == class_size]
    sub_df = sub_df.sort_values('slab_cnt')
    legend_label = f'Class {i}: {class_size}-byte'
    ax.plot(
        sub_df['slab_cnt'], sub_df['miss_ratio'],
        label=legend_label,
        color=color_map[class_size],
        linewidth=3,
        marker='o',
        markersize=3,
        alpha=0.9
    )
    ax.scatter(
        sub_df['slab_cnt'], sub_df['miss_ratio'],
        color=color_map[class_size],
        s=5,
        alpha=0.9
    )
    legend_labels.append((class_size, legend_label))
ax.set_xlim(left = 0, right=128)
ax.set_xlabel("Number of Slabs", fontsize=22)
ax.set_ylabel("Miss Ratio", fontsize=22)
ax.tick_params(axis='both', which='major', labelsize=20)
ax.grid(True, linestyle='--', alpha=0.3)

# Sort legend by class_size numerical order
handles, labels = ax.get_legend_handles_labels()
sorted_legend = sorted(zip(class_sizes, handles, labels), key=lambda x: x[0])
handles = [h for _, h, _ in sorted_legend]
labels = [l for _, _, l in sorted_legend]
ax.legend(handles, labels, title="Allocation Class", fontsize=18, title_fontsize=20, loc='best')

plt.suptitle("Miss Ratio Curve", fontsize=32)
plt.tight_layout(rect=[0, 0, 1, 0.96])

plt.savefig("../../figures/synth_static_202_mrc.pdf", dpi=300, bbox_inches='tight')
plt.show()