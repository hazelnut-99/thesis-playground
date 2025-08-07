
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 12

# Define the data
time_hours = 168  # 0 to 167
class_ids = 5  # 0, 1, 2, 3, 4 (5 classes total)

# Create the data matrix
data = np.zeros((class_ids, time_hours))

# Phase 1: hours 0-83 (first half, inclusive)
phase1_values = [1/6, 1/6, 1/6, 1/6, 2/6]
# Phase 2: hours 84-167 (second half)
phase2_values = [1/6, 1/6, 2/6, 1/6, 1/6]

# Fill the data matrix
for class_id in range(class_ids):
    # Phase 1: hours 0-83 (inclusive)
    data[class_id, :84] = phase1_values[class_id]
    # Phase 2: hours 84-167 (inclusive)
    data[class_id, 84:] = phase2_values[class_id]

# Flip the data vertically so class 0 is at bottom, class 4 at top
data = np.flipud(data)

# Create the heatmap
fig, ax = plt.subplots(figsize=(12, 6))

# Create heatmap with blue-red colormap similar to the provided figure
im = ax.imshow(data, cmap='RdYlBu_r', aspect='auto', interpolation='nearest')

# Set labels and ticks
ax.set_xlabel('Time (hour)', fontsize=20)
ax.set_ylabel('Class Id', fontsize=20)

# Set x-axis ticks
x_ticks = np.arange(0, 168, 42)  # At 0, 42, 84, 126
x_ticks = np.append(x_ticks, 167)
ax.set_xticks(x_ticks)
ax.set_xticklabels(x_ticks)

# Set y-axis ticks (flipped order: 4 at top, 0 at bottom)
ax.set_yticks(range(class_ids))
ax.set_yticklabels([4, 3, 2, 1, 0])  # Class IDs from 4 (top) to 0 (bottom)

# Add vertical line to separate phases
ax.axvline(x=83.5, color='black', linestyle='--', linewidth=2, alpha=0.7)

# Add horizontal lines to separate class IDs
for i in range(1, class_ids):
    ax.axhline(y=i-0.5, color='white', linewidth=1.5, alpha=0.8)


# Add phase labels at the top
ax.text(42, -0.7, 'Phase 1', ha='center', va='bottom', fontsize=24, style='italic')
ax.text(126, -0.7, 'Phase 2', ha='center', va='bottom', fontsize=24, style='italic')
# Add colorbar with larger font
cbar = plt.colorbar(im, ax=ax, shrink=0.8)
cbar.ax.tick_params(labelsize=14)

# Increase tick label sizes
ax.tick_params(axis='both', which='major', labelsize=14)

# Increase axis label sizes
ax.set_xlabel('Time (hour)', fontsize=24)
ax.set_ylabel('Class Id', fontsize=24)

# Adjust layout
plt.tight_layout()

# Save as PDF with high quality
plt.savefig('../../figures/dynamic_workload_heatmap.pdf', dpi=300, bbox_inches='tight', 
            facecolor='white', edgecolor='none')

# Show the plot
plt.show()