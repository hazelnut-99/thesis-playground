"""
read ../data/end-to-end/report_complete_processed.csv
filter by trace_name startswith twitter_cluster 
allocator = LRU 

wsr = 0.01, group by trace_name, find the row whose rebalanace_strategy is marginal-hits-tuned
find the row whose rebalanace_strategy is lama 
compare their miss_ratio (lower is better)
compute the ratio marginal-hits-tuned is better than lama
compute the ratio lama is better than marginal-hits-tuned

do the same for wsr = 0.1

i want to a barplot for each, make bar horizontal, full length represents 100%
fill them with two color,  one for marginal-hits-tuned, one for lama bar length represents the ratio
give two bars different colors and pattern
export to pdfs, to the current folder
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def create_lama_vs_marginal_hits_comparison():
    """
    Create horizontal bar plots comparing LAMA vs Marginal-Hits-Tuned strategies
    for Twitter cluster traces with LRU allocator.
    """
    
    # Read the CSV file
    df = pd.read_csv("../data/end-to-end/report_complete_processed.csv")
    
    # Filter by trace_name startswith twitter_cluster and allocator = LRU
    filtered_df = df[
        (df['trace_name'].str.startswith('twitter_cluster')) & 
        (df['allocator'] == 'LRU')
    ].copy()
    
    print(f"Total rows after filtering: {len(filtered_df)}")
    print(f"Unique traces: {sorted(filtered_df['trace_name'].unique())}")
    print(f"Available strategies: {sorted(filtered_df['rebalance_strategy'].unique())}")
    
    # Function to analyze a specific WSR
    def analyze_wsr(wsr_value):
        wsr_data = filtered_df[filtered_df['wsr'] == wsr_value].copy()
        
        if wsr_data.empty:
            print(f"No data found for WSR = {wsr_value}")
            return None, None, None
        
        print(f"\nAnalyzing WSR = {wsr_value}")
        print(f"Traces with data: {len(wsr_data['trace_name'].unique())}")
        
        comparisons = []
        
        # Group by trace_name and compare strategies
        for trace_name, group in wsr_data.groupby('trace_name'):
            # Find marginal-hits-tuned row
            marginal_hits_tuned_row = group[group['rebalance_strategy'] == 'marginal-hits-tuned']
            
            # Find lama row
            lama_row = group[group['rebalance_strategy'] == 'lama']
            
            # Only process if both strategies exist for this trace
            if len(marginal_hits_tuned_row) > 0 and len(lama_row) > 0:
                marginal_hits_miss_ratio = marginal_hits_tuned_row['miss_ratio'].iloc[0]
                lama_miss_ratio = lama_row['miss_ratio'].iloc[0]
                
                # Determine which is better (lower miss ratio)
                marginal_hits_better = marginal_hits_miss_ratio < lama_miss_ratio
                
                comparisons.append({
                    'trace_name': trace_name,
                    'marginal_hits_miss_ratio': marginal_hits_miss_ratio,
                    'lama_miss_ratio': lama_miss_ratio,
                    'marginal_hits_better': marginal_hits_better
                })
                
                print(f"  {trace_name}: Marginal-Hits={marginal_hits_miss_ratio:.6f}, "
                      f"LAMA={lama_miss_ratio:.6f}, "
                      f"Better: {'Marginal-Hits' if marginal_hits_better else 'LAMA'}")
        
        if not comparisons:
            print(f"No valid comparisons found for WSR = {wsr_value}")
            return None, None, None
        
        # Calculate ratios
        total_comparisons = len(comparisons)
        marginal_hits_wins = sum(1 for c in comparisons if c['marginal_hits_better'])
        lama_wins = total_comparisons - marginal_hits_wins
        
        marginal_hits_ratio = marginal_hits_wins / total_comparisons
        lama_ratio = lama_wins / total_comparisons
        
        print(f"Results for WSR = {wsr_value}:")
        print(f"  Total comparisons: {total_comparisons}")
        print(f"  Marginal-Hits-Tuned wins: {marginal_hits_wins} ({marginal_hits_ratio:.1%})")
        print(f"  LAMA wins: {lama_wins} ({lama_ratio:.1%})")
        
        return marginal_hits_ratio, lama_ratio, total_comparisons
    
    # Analyze both WSR values
    wsr_001_marginal, wsr_001_lama, wsr_001_total = analyze_wsr(0.01)
    wsr_01_marginal, wsr_01_lama, wsr_01_total = analyze_wsr(0.1)
    
    # Set up matplotlib for publication quality
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
    
    # Define colors and patterns
    marginal_hits_color = '#2E8B57'  # Sea green
    lama_color = '#8C564B'  # Brown
    
    # Create plots for each WSR
    wsr_data_list = [
        (0.01, wsr_001_marginal, wsr_001_lama, wsr_001_total),
        (0.1, wsr_01_marginal, wsr_01_lama, wsr_01_total)
    ]
    
    for wsr, marginal_ratio, lama_ratio, total_comp in wsr_data_list:
        if marginal_ratio is None:
            continue
            
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Create horizontal stacked bar
        bar_height = 0.6
        y_pos = 0
        
        # Plot LAMA portion (left side)
        lama_bar = ax.barh(y_pos, lama_ratio, height=bar_height, 
                          color=lama_color, alpha=0.8, 
                          edgecolor='black', linewidth=2,
                          hatch='///', label=r'$\mathit{LAMA}$ Better')
        
        # Plot Marginal-Hits-Tuned portion (right side)
        marginal_bar = ax.barh(y_pos, marginal_ratio, height=bar_height,
                              left=lama_ratio, color=marginal_hits_color, alpha=0.8,
                              edgecolor='black', linewidth=2,
                              hatch='...', label=r'$\mathit{Marginal\text{-}Hits\text{-}Tuned}$ Better')
        
        # Customize the plot
        ax.set_xlim(0, 1)
        ax.set_ylim(-0.5, 0.5)
        ax.set_xlabel('Proportion of Twitter Cluster Traces')
        ax.set_title(f'Strategy Performance Comparison (WSR = {wsr})\n'
                    f'Total Comparisons: {total_comp} traces')
        
        # Remove y-axis ticks and labels
        ax.set_yticks([])
        
        # Format x-axis as percentage
        ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
        ax.set_xticklabels(['0%', '25%', '50%', '75%', '100%'])
        
        # Add percentage labels on bars
        if lama_ratio > 0.05:  # Only show label if bar is wide enough
            ax.text(lama_ratio/2, y_pos, f'{lama_ratio:.1%}', 
                   ha='center', va='center', fontweight='bold', fontsize=18)
        
        if marginal_ratio > 0.05:  # Only show label if bar is wide enough
            ax.text(lama_ratio + marginal_ratio/2, y_pos, f'{marginal_ratio:.1%}', 
                   ha='center', va='center', fontweight='bold', fontsize=18)
        
        # Add grid
        ax.grid(True, alpha=0.3, axis='x')
        ax.set_axisbelow(True)
        
        # Add legend
        ax.legend(bbox_to_anchor=(0.5, -0.15), loc='upper center', ncol=2,
                 frameon=True, fancybox=True, shadow=True, framealpha=0.9)
        
        # Style the plot
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_linewidth(1.2)
        
        # Adjust layout
        plt.tight_layout()
        plt.subplots_adjust(bottom=0.25)  # Make room for legend
        
        # Save to PDF
        wsr_str = f"{wsr:.2f}".replace('.', '_')
        output_file = f'lama_vs_marginal_hits_comparison_wsr_{wsr_str}.pdf'
        plt.savefig(output_file, format='pdf', dpi=300, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        
        plt.show()
        print(f"Plot saved to: {output_file}")

if __name__ == "__main__":
    create_lama_vs_marginal_hits_comparison()