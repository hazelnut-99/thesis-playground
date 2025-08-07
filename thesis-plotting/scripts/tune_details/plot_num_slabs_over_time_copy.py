import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def plot_num_slabs_over_time(csv_file, output_file=None):
    """
    Plot number of slabs allocated over time for different classes.
    
    Parameters:
    - csv_file: Path to CSV file with columns: allSlabsAllocated, request_id, class_id, num_slab
    - output_file: Path for output PDF (optional, defaults to same name as input with .pdf extension)
    """
    
    # Read the CSV file
    df = pd.read_csv(csv_file)
    df = df[df['allSlabsAllocated'] == True]  # Filter for all slabs allocated
    
    # Convert request_id to millions
    df['request_id'] = df['request_id'] / 1_000_000
    
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
        'font.size': 20,           # Much bigger font
        'axes.titlesize': 24,      
        'axes.labelsize': 22,      
        'xtick.labelsize': 18,     
        'ytick.labelsize': 18,     
        'legend.fontsize': 18,     
        'figure.titlesize': 26,    
        'lines.linewidth': 3,      # Thicker lines
        'lines.markersize': 8,     
        'figure.dpi': 300,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'axes.linewidth': 1.5,     
        'grid.linewidth': 1.0,     
        'grid.alpha': 0.3
    })
    
    # Create figure and axis - smaller figure
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Plot data for each class
    unique_classes = sorted(df['class_id'].unique())
    
    for class_id in unique_classes:
        class_data = df[df['class_id'] == class_id].sort_values('request_id')
        
        color = class_colors.get(class_id, f'C{class_id}')
        label = class_labels.get(class_id, f'Class {class_id}')
        marker = class_markers.get(class_id, 'o')  # Default to circle if not found
        
        # Plot line + scatter with different markers
        ax.plot(class_data['request_id'], class_data['num_slab'], 
               color=color, label=label, linewidth=2, alpha=1)
        ax.scatter(class_data['request_id'], class_data['num_slab'], 
                  color=color, s=5, alpha=1, zorder=5, marker=marker, linewidth=1)
    
    # Customize the plot
    ax.set_xlabel('Logical Time (# requests, million)')
    ax.set_ylabel('Number of Slabs Allocated')
    ax.grid(True, alpha=0.3, linestyle='-', linewidth=1.0)
    
    # Customize legend - moved to top outside figure
    legend = ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.3), 
                      ncol=3, frameon=True, fancybox=True, shadow=True, edgecolor='black')
    legend.get_frame().set_facecolor('white')
    legend.get_frame().set_linewidth(1)
    
    # Set axis limits with some padding
    x_min, x_max = df['request_id'].min(), df['request_id'].max()
    x_padding = (x_max - x_min) * 0.02
    ax.set_xlim(x_min - x_padding, x_max + x_padding)
    
    y_min, y_max = df['num_slab'].min(), df['num_slab'].max()
    y_padding = (y_max - y_min) * 0.05
    ax.set_ylim(max(0, y_min - y_padding), y_max + y_padding)
    
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
        output_file = csv_file.replace('.csv', '_num_slabs_plot_2.pdf')
    
    plt.savefig(output_file, format='pdf', dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    
    # Show the plot
    plt.show()
    
    print(f"Plot saved to: {output_file}")

# Example usage:
if __name__ == "__main__":
    # Example usage
    plot_num_slabs_over_time("static_202_marginal_hits_num_slabs_flattened.csv")
    plot_num_slabs_over_time("static_202_marginal_hits_tuned_num_slabs_flattened.csv")
    # plot_num_slabs_over_time("dynamic_400_marginal_hits_num_slabs_flattened.csv")
    # plot_num_slabs_over_time("dynamic_400_marginal_hits_tuned_num_slabs_flattened.csv")
    
    # Or with custom output file
    # plot_num_slabs_over_time("data.csv", "custom_output.pdf")