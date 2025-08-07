"""
Bar plot visualization for synthetic cache performance analysis.
Creates two separate bar plots:
1. Miss ratio by cache size and rebalance strategy
2. Number of rebalanced slabs by cache size and rebalance strategy
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

def create_synthetic_bar_plots(csv_file, output_dir):
    """
    Create two bar plots showing miss ratio and rebalanced slabs.
    
    Args:
        csv_file: Path to the CSV file
        output_dir: Directory to save the plots
    """
    
    # Read the CSV file
    df = pd.read_csv(csv_file)
    
    # Filter by trace_name = synth_static_202 and allocator = LRU
    filtered_df = df[(df['trace_name'] == 'synth_static_202') & (df['allocator'] == 'LRU') & df['wsr'] != 0.01].copy()
    
    if filtered_df.empty:
        print("No data found for trace_name='synth_static_202' and allocator='LRU'")
        return
    
    print(f"Filtered data points: {len(filtered_df)}")
    print(f"Available strategies: {sorted(filtered_df['rebalance_strategy'].unique())}")
    print(f"Available WSR values: {sorted(filtered_df['wsr'].unique())}")
    
    # Set up the plotting style for publication quality
    plt.rcParams.update({
        'font.size': 14,
        'axes.titlesize': 16,
        'axes.labelsize': 14,
        'xtick.labelsize': 12,
        'ytick.labelsize': 12,
        'legend.fontsize': 12,
        'figure.titlesize': 18,
        'figure.dpi': 300,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight'
    })
    
    # Get unique WSR values and sort them numerically
    wsr_values = sorted(filtered_df['wsr'].unique())
    
    # Convert WSR to percentage labels for x-axis (without % symbol)
    wsr_labels = [f'{int(wsr * 100)}' for wsr in wsr_values]
    
    # Keep only specific strategies: disabled, marginal-hits, marginal-hits-tuned
    strategy_order = ["disabled", "marginal-hits", "marginal-hits-tuned"]
    available_strategies = filtered_df['rebalance_strategy'].unique()
    strategies = [s for s in strategy_order if s in available_strategies]
    
    # Filter data to keep only these strategies
    filtered_df = filtered_df[filtered_df['rebalance_strategy'].isin(strategies)].copy()
    
    # Strategy labels with LaTeX formatting (only for the three strategies we're keeping)
    strategy_labels = {
        "disabled": r"$\mathit{Disabled}$",
        "marginal-hits": r"$\mathit{Marginal\text{-}Hits}$",
        "marginal-hits-tuned": r"$\mathit{Marginal\text{-}Hits\text{-}Tuned}$"
    }
    
    # Strategy colors (only for the three strategies we're keeping)
    strategy_colors = {
        "disabled": "#636EFA",
        "marginal-hits": "#EF553B",
        "marginal-hits-tuned": "#2E8B57"
    }
    
    # Ensure we have colors for all strategies (simplified since we only have 3 strategies)
    default_colors = ['#636EFA', '#EF553B', '#2E8B57']
    for i, strategy in enumerate(strategies):
        if strategy not in strategy_colors:
            strategy_colors[strategy] = default_colors[i % len(default_colors)]
    
    # Set up bar width and positions
    bar_width = 0.8 / len(strategies)
    x_positions = np.arange(len(wsr_values))
    
    # Plot 1: Miss Ratio
    fig1, ax1 = plt.subplots(figsize=(9, 5))
    
    for i, strategy in enumerate(strategies):
        strategy_data = filtered_df[filtered_df['rebalance_strategy'] == strategy]
        
        # Get miss ratios for each WSR value
        miss_ratios = []
        for wsr in wsr_values:
            wsr_data = strategy_data[strategy_data['wsr'] == wsr]
            if not wsr_data.empty:
                miss_ratios.append(wsr_data['miss_ratio'].iloc[0])
            else:
                miss_ratios.append(0)  # Default if no data
        
        # Plot bars
        bars = ax1.bar(x_positions + i * bar_width, miss_ratios,
                      bar_width, label=strategy_labels.get(strategy, strategy),
                      color=strategy_colors[strategy],
                      edgecolor='black', linewidth=0.5)
    
    # Customize Plot 1
    ax1.set_xlabel('Cache Size (% of Working Set)')
    ax1.set_ylabel('Miss Ratio')
    ax1.set_xticks(x_positions + bar_width * (len(strategies) - 1) / 2)
    ax1.set_xticklabels(wsr_labels)
    ax1.legend(loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=3)
    ax1.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.85)  # Make room for top legend
    
    # Save Plot 1
    output_path1 = os.path.join(output_dir, 'miss_ratio_by_cache_size.pdf')
    plt.savefig(output_path1, format='pdf', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Plot 2: Number of Rebalanced Slabs (exclude disabled since it never rebalances)
    fig2, ax2 = plt.subplots(figsize=(9, 5))
    
    # Filter out disabled strategy for this plot
    strategies_for_rebalance = [s for s in strategies if s != "disabled"]
    
    for i, strategy in enumerate(strategies_for_rebalance):
        strategy_data = filtered_df[filtered_df['rebalance_strategy'] == strategy]
        
        # Get n_rebalanced_slabs for each WSR value
        n_rebalanced = []
        for wsr in wsr_values:
            wsr_data = strategy_data[strategy_data['wsr'] == wsr]
            if not wsr_data.empty:
                # Handle NaN values
                value = wsr_data['n_rebalanced_slabs'].iloc[0]
                n_rebalanced.append(0 if pd.isna(value) else value)
            else:
                n_rebalanced.append(0)  # Default if no data
        
        # Plot bars (adjust bar width for fewer strategies)
        bar_width_rebalance = 0.8 / len(strategies_for_rebalance)
        bars = ax2.bar(x_positions + i * bar_width_rebalance, n_rebalanced,
                      bar_width_rebalance, label=strategy_labels.get(strategy, strategy),
                      color=strategy_colors[strategy], 
                      edgecolor='black', linewidth=0.5)
    
    # Customize Plot 2
    ax2.set_xlabel('Cache Size (% of Working Set)')
    ax2.set_ylabel('Number of Rebalanced Slabs')
    ax2.set_xticks(x_positions + bar_width_rebalance * (len(strategies_for_rebalance) - 1) / 2)
    ax2.set_xticklabels(wsr_labels)
    ax2.legend(loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=2)  # 2 columns since only 2 strategies
    ax2.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.85)  # Make room for top legend
    
    # Save Plot 2
    output_path2 = os.path.join(output_dir, 'rebalanced_slabs_by_cache_size.pdf')
    plt.savefig(output_path2, format='pdf', dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"Plot 1 saved to: {output_path1}")
    print(f"Plot 2 saved to: {output_path2}")
    
    # Print some statistics
    print(f"\nData summary:")
    print(f"WSR values: {wsr_values}")
    print(f"WSR percentages: {[f'{int(w*100)}%' for w in wsr_values]}")
    print(f"Strategies: {strategies}")
    
    # Show sample data for verification
    print(f"\nSample data:")
    for strategy in strategies[:2]:  # Show first 2 strategies
        strategy_data = filtered_df[filtered_df['rebalance_strategy'] == strategy]
        print(f"\n{strategy}:")
        for wsr in wsr_values[:3]:  # Show first 3 WSR values
            wsr_data = strategy_data[strategy_data['wsr'] == wsr]
            if not wsr_data.empty:
                miss_ratio = wsr_data['miss_ratio'].iloc[0]
                n_rebal = wsr_data['n_rebalanced_slabs'].iloc[0]
                print(f"  WSR {wsr} ({int(wsr*100)}%): miss_ratio={miss_ratio:.4f}, n_rebalanced={n_rebal}")

if __name__ == "__main__":
    # File paths
    csv_file = "miss_ratios_synthetic.csv"
    output_dir = "."
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create the plots
    create_synthetic_bar_plots(csv_file, output_dir)