"""
Plot boxplots showing the improvement from marginal-hits to marginal-hits-tuned strategy.
Three eviction policies on x-axis, tuning improvement on y-axis.
Creates subplots for WSR 0.01 and 0.1, exports to PDF with publication quality.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

def plot_tuned_improvement(df, output_dir):
    """
    Plot boxplots showing miss ratio improvement from marginal-hits to marginal-hits-tuned.
    Creates separate PDF files for each WSR value.
    
    Args:
        df: DataFrame with columns including 'allocator', 'wsr', 'tuned_improvement'
        output_dir: Directory to save the plots
    """
    
    # Filter Twitter production data and remove NaN values from tuned_improvement
    df = df[(df['trace_name'].str.startswith('twitter')) & (df['tag'] != 'warm-cold')]
    df = df.dropna(subset=['tuned_improvement'])  # Remove rows where tuned_improvement is NaN
    
    # Debug: Print data info
    print(f"Total filtered data points: {len(df)}")
    print(f"Available columns: {df.columns.tolist()}")
    print(f"Unique WSR values: {df['wsr'].unique() if 'wsr' in df.columns else 'WSR column not found'}")
    print(f"Unique allocators: {df['allocator'].unique() if 'allocator' in df.columns else 'allocator column not found'}")
    if 'tuned_improvement' in df.columns:
        print(f"tuned_improvement range: {df['tuned_improvement'].min()} to {df['tuned_improvement'].max()}")
        print(f"Non-null tuned_improvement values: {df['tuned_improvement'].notna().sum()}")
    else:
        print("tuned_improvement column not found")
    
    # Set up the plotting style for publication quality
    plt.rcParams.update({
        'font.size': 20,
        'axes.titlesize': 24,
        'axes.labelsize': 22,
        'xtick.labelsize': 20,
        'ytick.labelsize': 20,
        'legend.fontsize': 18,
        'figure.titlesize': 26,
        'figure.dpi': 300,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'axes.linewidth': 1.2,
        'grid.linewidth': 0.8,
        'grid.alpha': 0.3
    })
    
    # Define allocator order and labels (same as in plot_twitter_prod_best.py)
    allocator_order = ['LRU', 'LRU2Q', 'TINYLFU']
    allocator_labels = ['LRU', 'TwoQ', 'TinyLFU']
    
    # Create separate plots for each WSR value
    wsr_values = [0.01, 0.1]
    
    for wsr in wsr_values:
        # Create individual figure for this WSR
        fig, ax = plt.subplots(1, 1, figsize=(9, 6))
        
        df_wsr = df[df['wsr'] == wsr]
        print(f"\nWSR {wsr}: {len(df_wsr)} data points")
        
        # Prepare data for boxplot
        boxplot_data = []
        positions = []
        labels = []
        
        for j, allocator in enumerate(allocator_order):
            allocator_data = df_wsr[df_wsr['allocator'] == allocator]
            if len(allocator_data) > 0:
                data = allocator_data['tuned_improvement'].values
                # Double-check for NaN values
                data = data[~np.isnan(data)]
                if len(data) > 0:
                    print(f"  {allocator}: {len(data)} points, range {data.min():.6f} to {data.max():.6f}, mean: {data.mean():.6f}")
                    boxplot_data.append(data)
                    positions.append(j)
                    labels.append(allocator_labels[j])
                else:
                    print(f"  {allocator}: {len(allocator_data)} total points, but all NaN after filtering")
            else:
                print(f"  {allocator}: No data after WSR filtering")
        
        # Create boxplot
        if boxplot_data:
            bp = ax.boxplot(boxplot_data, positions=positions, patch_artist=True,
                          boxprops=dict(facecolor='lightblue', alpha=0.7),
                          medianprops=dict(color='red', linewidth=2),
                          meanprops=dict(marker='v', markerfacecolor='red', markeredgecolor='red', markersize=8),
                          showmeans=True,
                          showfliers=False,  # Don't show outlier points
                          whis=1.5)         # Whiskers extend to 1.5×IQR (traditional rule)
        else:
            print(f"No data available for WSR {wsr}")
            plt.close(fig)
            continue
        
        # Customize the subplot
        ax.set_xlabel('Eviction Policy')
        ax.set_ylabel('Miss Ratio Reduction\nover ' + r'$\mathit{Marginal\text{-}Hits}$')
        ax.set_xticks(range(len(allocator_order)))
        ax.set_xticklabels(allocator_labels)
        ax.grid(True, alpha=0.3)
        
        # Add horizontal line at y=0 for reference
        ax.axhline(y=0, color='black', linestyle='--', alpha=0.5, linewidth=1)
        
        plt.tight_layout()
        
        # Save individual plot
        output_path = os.path.join(output_dir, f'twitter_prod_tuned_improvement_wsr_{wsr}.pdf')
        plt.savefig(output_path, format='pdf', dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"Plot saved to: {output_path}")

if __name__ == "__main__":
    # Load data (adjust path as needed)
    data_path = "twitter_full_digest.csv"  # Update this path
    df = pd.read_csv(data_path)
    
    # Set output directory
    output_dir = "/nfs/hongshu/thesis-playground/thesis-plotting/scripts/twitter_prod"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create the plot
    plot_tuned_improvement(df, output_dir)