import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def plot_threshold_over_time(csv_file, output_file=None):
    """
    Plot threshold over time as a step function with increase/decrease markers.
    
    Parameters:
    - csv_file: Path to CSV file with columns: request_id, effective_move_rate, threshold, window_size, diff, victim_class_id, receiver_class_id
    - output_file: Path for output PDF (optional, defaults to same name as input with .pdf extension)
    """
    
    # Read the CSV file
    df = pd.read_csv(csv_file)
    
    # Convert request_id to millions
    df['request_id'] = df['request_id'] / 1_000_000
    
    # Sort by request_id
    df_sorted = df.sort_values('request_id').reset_index(drop=True)
    
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
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Create step function data
    x_step = []
    y_step = []
    
    # Add initial point
    x_step.append(df_sorted['request_id'].iloc[0])
    y_step.append(df_sorted['threshold'].iloc[0])
    
    # Create step function points
    for i in range(len(df_sorted)):
        current_x = df_sorted['request_id'].iloc[i]
        current_y = df_sorted['threshold'].iloc[i]
        
        # Add horizontal line to current point
        x_step.append(current_x)
        y_step.append(current_y)
        
        # If not the last point, add vertical jump to next threshold
        if i < len(df_sorted) - 1:
            next_y = df_sorted['threshold'].iloc[i + 1]
            if next_y != current_y:  # Only add if threshold changes
                x_step.append(current_x)
                y_step.append(next_y)
    
    # Extend the last horizontal line to the end
    if len(df_sorted) > 1:
        x_step.append(df_sorted['request_id'].iloc[-1])
        y_step.append(df_sorted['threshold'].iloc[-1])
    
    # Plot the step function
    ax.plot(x_step, y_step, color='#636EFA', linewidth=3, alpha=0.9)
    
    # Add markers for increases and decreases
    increase_x = []
    increase_y = []
    decrease_x = []
    decrease_y = []
    
    for i in range(1, len(df_sorted)):
        current_threshold = df_sorted['threshold'].iloc[i]
        previous_threshold = df_sorted['threshold'].iloc[i-1]
        current_x = df_sorted['request_id'].iloc[i]
        
        if current_threshold > previous_threshold:
            increase_x.append(current_x)
            increase_y.append(current_threshold)
        elif current_threshold < previous_threshold:
            decrease_x.append(current_x)
            decrease_y.append(current_threshold)
    
    # Plot increase markers (triangles up)
    if increase_x:
        ax.scatter(increase_x, increase_y, color='#00CC96', s=200, marker='^', 
                  zorder=5, linewidth=2, label='Additive Increase')
    
    # Plot decrease markers (triangles down)
    if decrease_x:
        ax.scatter(decrease_x, decrease_y, color='#EF553B', s=200, marker='v', 
                  zorder=5, linewidth=2, label='Multiplicative Decrease')
    
    # Customize the plot
    ax.set_xlabel('Logical Time (# requests, million)')
    ax.set_ylabel('Threshold')
    ax.grid(True, alpha=0.3, linestyle='-', linewidth=1.0)
    
    # Add legend if there are markers
    if increase_x or decrease_x:
        legend = ax.legend(loc='upper right', frameon=True, fancybox=True, shadow=True, 
                          framealpha=0.9, edgecolor='black')
        legend.get_frame().set_facecolor('white')
        legend.get_frame().set_linewidth(1)
    
    # Set axis limits with some padding
    x_min, x_max = df_sorted['request_id'].min(), df_sorted['request_id'].max()
    x_padding = (x_max - x_min) * 0.02
    ax.set_xlim(x_min - x_padding, x_max + x_padding)
    
    y_min, y_max = df_sorted['threshold'].min(), df_sorted['threshold'].max()
    y_padding = (y_max - y_min) * 0.05 if y_max != y_min else 0.1
    ax.set_ylim(max(0, y_min - y_padding), y_max + y_padding)
    
    # Make the plot look modern
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_linewidth(1.5)
    ax.spines['bottom'].set_linewidth(1.5)
    
    # Tight layout
    plt.tight_layout()
    
    # Save to PDF
    if output_file is None:
        output_file = csv_file.replace('.csv', '_threshold_plot.pdf')
    
    plt.savefig(output_file, format='pdf', dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    
    # Show the plot
    plt.show()
    
    print(f"Plot saved to: {output_file}")

# Example usage:
if __name__ == "__main__":
    # Example usage
    plot_threshold_over_time("dynamic_400_marginal_hits_tuned_mh_threshold.csv")
    plot_threshold_over_time("static_202_marginal_hits_tuned_mh_threshold.csv")
    
    # Or with custom output file
    # plot_threshold_over_time("data.csv", "custom_output.pdf")