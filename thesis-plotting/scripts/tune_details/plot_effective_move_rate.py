import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def plot_effective_move_rate(csv_file, output_file=None):
    """
    Plot effective move rate over time.
    
    Parameters:
    - csv_file: Path to CSV file with columns: request_id, effective_move_rate
    - output_file: Path for output PDF (optional, defaults to same name as input with .pdf extension)
    """
    
    # Read the CSV file
    df = pd.read_csv(csv_file)
    
    # Convert request_id to millions
    df['request_id'] = df['request_id'] / 1_000_000
    
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
    
    # Sort data by request_id
    df_sorted = df.sort_values('request_id')
    
    # Plot line + scatter
    ax.plot(df_sorted['request_id'], df_sorted['effective_move_rate'], 
           color='#636EFA', linewidth=1, alpha=0.8)
    ax.scatter(df_sorted['request_id'], df_sorted['effective_move_rate'], 
              color='#636EFA', s=10, alpha=1, zorder=5, marker='o', 
               linewidth=1)
    
    # Customize the plot
    ax.set_xlabel('Logical Time (# requests, million)')
    ax.set_ylabel('Effective Move Rate')
    ax.grid(True, alpha=0.3, linestyle='-', linewidth=1.0)
    
    # Set axis limits with some padding
    x_min, x_max = df['request_id'].min(), df['request_id'].max()
    x_padding = (x_max - x_min) * 0.02
    ax.set_xlim(x_min - x_padding, x_max + x_padding)
    
    y_min, y_max = df['effective_move_rate'].min(), df['effective_move_rate'].max()
    y_padding = (y_max - y_min) * 0.05
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
        output_file = csv_file.replace('.csv', '_effective_move_rate_plot.pdf')
    
    plt.savefig(output_file, format='pdf', dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    
    # Show the plot
    plt.show()
    
    print(f"Plot saved to: {output_file}")

# Example usage:
if __name__ == "__main__":
    # Example usage
    plot_effective_move_rate("dynamic_400_marginal_hits_effective_move_rates.csv")
    plot_effective_move_rate("static_202_marginal_hits_effective_move_rates.csv")
    plot_effective_move_rate("dynamic_400_marginal_hits_tuned_effective_move_rates.csv")
    plot_effective_move_rate("static_202_marginal_hits_tuned_effective_move_rates.csv")
    
    # Or with custom output file
    # plot_effective_move_rate("data.csv", "custom_output.pdf")