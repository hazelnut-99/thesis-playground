import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def plot_num_slabs_over_time(csv_file, version="complete", output_file=None):
    """
    Plot number of slabs allocated over time for different classes.
    
    Parameters:
    - csv_file: Path to CSV file with columns: allSlabsAllocated, request_id, class_id, num_slab
    - version: "fcfs_only" for slide 1 (initial phase), "zoomed" for slide 2 (up to 10M requests), "complete" for slide 3 (full timeline)
    - output_file: Path for output PDF (optional, defaults based on version)
    """
    
    # Read the CSV file
    df = pd.read_csv(csv_file)
    
    # Convert request_id to millions
    df['request_id'] = df['request_id'] / 1_000_000
    
    # Filter out data after 40 million requests (40 in converted scale)
    df = df[df['request_id'] <= 40]
    
    # Filter data based on version
    if version == "fcfs_only":
        # Show only the initial FCFS phase (allSlabsAllocated = False)
        df_plot = df[df['allSlabsAllocated'] == False]
    elif version == "zoomed":
        # Show data up to 10 million requests (10 in converted scale)
        df_plot = df[df['request_id'] <= 10].copy()
    else:  # complete version
        # Show full timeline
        df_plot = df.copy()
    
    # Find the transition point where allSlabsAllocated becomes True (for the vertical line)
    transition_point = df[df['allSlabsAllocated'] == True]['request_id'].min()
    
    # For consistent axis limits, always use the full dataset range
    df_full = df.copy()  # Keep full dataset for axis calculations
    
    # Optimal allocation targets for each class
    optimal_targets = {0: 62, 1: 18, 2: 84, 3: 20, 4: 12}
    
    # Set up colors, labels, and markers
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
    class_markers = {
        0: 'o',  # circle
        1: 's',  # square
        2: '^',  # triangle up
        3: 'D',  # diamond
        4: 'v',  # triangle down
    }
    
    # Set up matplotlib for publication quality
    plt.style.use('default')  # Use default style as base
    plt.rcParams.update({
        'font.size': 24,           # Much bigger font (was 20, +4)
        'axes.titlesize': 28,      # (was 24, +4)
        'axes.labelsize': 26,      # (was 22, +4)
        'xtick.labelsize': 22,     # (was 18, +4)
        'ytick.labelsize': 22,     # (was 18, +4)
        'legend.fontsize': 22,     # (was 18, +4)
        'figure.titlesize': 30,    # (was 26, +4)
        'lines.linewidth': 3,      # Thicker lines
        'lines.markersize': 8,     
        'figure.dpi': 300,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'axes.linewidth': 1.5,     
        'grid.linewidth': 1.0,     
        'grid.alpha': 0.3
    })
    
    # Create figure and axis - wider figure for better timeline visibility
    fig, ax = plt.subplots(figsize=(16, 7))  # Made wider (was 12, 7)
    
    # Plot data for each class
    unique_classes = sorted(df_plot['class_id'].unique())
    
    for class_id in unique_classes:
        class_data = df_plot[df_plot['class_id'] == class_id].sort_values('request_id')
        
        if class_data.empty:
            continue
            
        color = class_colors.get(class_id, f'C{class_id}')
        label = class_labels.get(class_id, f'Class {class_id}')
        marker = class_markers.get(class_id, 'o')  # Default to circle if not found
        
        # Plot line + scatter with different markers
        ax.plot(class_data['request_id'], class_data['num_slab'], 
               color=color, label=label, linewidth=2, alpha=1)
        ax.scatter(class_data['request_id'], class_data['num_slab'], 
                  color=color, s=15, alpha=1, zorder=5, marker=marker, linewidth=1)
    
    # For all versions, add optimal targets as stars on the right
    if version in ["complete", "fcfs_only", "zoomed"]:
        # Get the rightmost x position for placing stars
        x_max = df_full['request_id'].max()
        x_star_position = x_max + (x_max - df_full['request_id'].min()) * 0.05  # Slightly to the right
        
        for class_id in unique_classes:
            if class_id in optimal_targets:
                color = class_colors.get(class_id, f'C{class_id}')
                optimal_value = optimal_targets[class_id]
                
                # Add star marker for optimal target
                ax.scatter(x_star_position, optimal_value, 
                          color=color, s=200, marker='*', 
                          zorder=10, alpha=0.9)
    
    # Add vertical dashed line at transition point for both versions
    if not pd.isna(transition_point):
        ax.axvline(x=transition_point, color='red', linestyle='--', alpha=0.7, linewidth=2,
                  ymin=0, ymax=1.1, clip_on=False)  # Extend 10% above y-axis limit
    
    # Customize the plot
    ax.set_xlabel('Logical Time (# requests, million)')
    ax.set_ylabel('Number of Slabs Allocated')
    ax.grid(True, alpha=0.3, linestyle='-', linewidth=1.0)
    
    # Customize legend - moved to top outside figure
    legend = ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.35), 
                      ncol=3, frameon=True, fancybox=True, shadow=True, edgecolor='black')
    legend.get_frame().set_facecolor('white')
    legend.get_frame().set_linewidth(1)
    
    # Set axis limits with some padding - use full dataset for consistent ranges
    x_min, x_max = df_full['request_id'].min(), df_full['request_id'].max()
    x_padding = (x_max - x_min) * 0.02
    
    # For both versions, extend x-axis to accommodate stars
    x_star_position = x_max + (x_max - x_min) * 0.05
    ax.set_xlim(x_min - x_padding, x_star_position + x_padding)
    
    # Use full dataset for y-axis range to ensure consistency
    y_min, y_max = df_full['num_slab'].min(), df_full['num_slab'].max()
    
    # For all versions, consider optimal targets in y-axis range
    all_y_values = list(df_full['num_slab']) + list(optimal_targets.values())
    y_min, y_max = min(all_y_values), max(all_y_values)
    
    y_padding = (y_max - y_min) * 0.05
    ax.set_ylim(max(0, y_min - y_padding), y_max + y_padding)
    
    # Add optimal allocation label after axis limits are set (for consistent positioning)
    if version in ["complete", "fcfs_only", "zoomed"]:
        x_max = df_full['request_id'].max()
        x_star_position = x_max + (x_max - df_full['request_id'].min()) * 0.05
        # Now that y-axis limits are set, use them for consistent label positioning
        ax.text(x_star_position, ax.get_ylim()[1] * 1.05, 'Optimal\nAllocation', 
                ha='center', va='top', fontsize=20, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgray', alpha=0.7))
    
    # Make the plot look modern
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_linewidth(1.5)
    ax.spines['bottom'].set_linewidth(1.5)
    
    # Tight layout with extra space for legend
    plt.tight_layout()
    plt.subplots_adjust(top=0.85)  # Make room for legend at top
    
    # Save to PDF
    if output_file is None:
        if version == "fcfs_only":
            output_file = csv_file.replace('.csv', '_slide1.pdf')
        elif version == "zoomed":
            output_file = csv_file.replace('.csv', '_slide2.pdf')
        else:  # complete
            output_file = csv_file.replace('.csv', '_slide3.pdf')
    
    plt.savefig(output_file, format='pdf', dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    
    # Show the plot
    plt.show()
    
    print(f"Plot saved to: {output_file}")

# Example usage:
if __name__ == "__main__":
    # Generate all three versions for presentation
    csv_file = "static_202_marginal_hits_num_slabs_flattened.csv"
    
    print("Generating FCFS-only version (slide 1)...")
    plot_num_slabs_over_time(csv_file, version="fcfs_only")
    
    print("\nGenerating zoomed version up to 10M requests (slide 2)...")
    plot_num_slabs_over_time(csv_file, version="zoomed")
    
    print("\nGenerating complete version with optimal targets (slide 3)...")
    plot_num_slabs_over_time(csv_file, version="complete")
    
    # Other example files (commented out)
    #plot_num_slabs_over_time("static_202_marginal_hits_tuned_num_slabs_flattened.csv", version="fcfs_only")
    #plot_num_slabs_over_time("static_202_marginal_hits_tuned_num_slabs_flattened.csv", version="zoomed")
    #plot_num_slabs_over_time("static_202_marginal_hits_tuned_num_slabs_flattened.csv", version="complete")
    #plot_num_slabs_over_time("dynamic_400_marginal_hits_num_slabs_flattened.csv", version="fcfs_only")
    #plot_num_slabs_over_time("dynamic_400_marginal_hits_num_slabs_flattened.csv", version="zoomed")
    #plot_num_slabs_over_time("dynamic_400_marginal_hits_num_slabs_flattened.csv", version="complete")