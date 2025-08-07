import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from scipy import stats
import os

def plot_overhead_analysis(output_dir='.'):
    """
    Plot overhead analysis showing rebalance cycle percentage by allocator and strategy.
    Creates bar plots with mean and error bars for each WSR value.
    """
    
    # Read the data
    csv_path = '../data/overhead/meta_2022_overhead.csv'
    print(f"Reading data from {csv_path}")
    
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        return
    
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} rows")
    
    # Filter out disabled strategy
    df = df[df['rebalance_strategy'] != 'disabled']
    print(f"After filtering out disabled strategy: {len(df)} rows")
    
    # Define strategy labels and colors
    strategy_labels = {
        "tail-age": r"$\mathit{Tail\text{-}Age}$",
        "eviction-rate": r"$\mathit{Eviction\text{-}Rate}$",
        "hits": r"$\mathit{Hits\text{-}Per\text{-}Slab}$",
        "lama": r"$\mathit{LAMA}$",
        "marginal-hits": r"$\mathit{Marginal\text{-}Hits}$",
        "marginal-hits-tuned": r"$\mathit{Marginal\text{-}Hits\text{-}Tuned}$"
    }
    
    # Enforce order for rebalance strategies 
    strategy_order = ["tail-age", "eviction-rate", "hits", "lama", "marginal-hits", "marginal-hits-tuned"]
    
    strategy_colors = {
        "tail-age": "#AB63FA", 
        "eviction-rate": "#FFA15A",
        "hits": "#00CC96",
        "lama": "#8B4513",  # Chocolate brown color
        "marginal-hits": "#EF553B",
        "marginal-hits-tuned": "#2E8B57"
    }
    
    # Define allocator order and labels
    allocator_order = ['LRU', 'TwoQ', 'TinyLFU']
    allocator_labels = ['LRU', 'TwoQ', 'TinyLFU']
    
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
        'grid.alpha': 0.3,
        'figure.figsize': (14, 8)
    })
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Create plots for both WSR values
    wsr_values = [0.1, 0.01]
    
    for wsr in wsr_values:
        # Filter data for current WSR
        wsr_data = df[df['wsr'] == wsr].copy()
        print(f"\nProcessing WSR = {wsr}")
        print(f"Data points for WSR {wsr}: {len(wsr_data)}")
        
        if len(wsr_data) == 0:
            print(f"No data found for WSR = {wsr}")
            continue
        
        # Create figure
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Calculate statistics for each allocator-strategy combination
        stats_data = []
        for allocator in allocator_order:
            for strategy in strategy_order:
                # Skip LAMA for non-LRU allocators
                if strategy == 'lama' and allocator != 'LRU':
                    continue
                    
                subset = wsr_data[
                    (wsr_data['allocator'] == allocator) & 
                    (wsr_data['rebalance_strategy'] == strategy)
                ]
                
                if len(subset) > 0:
                    mean_val = subset['rebalance_cycle_pct'].mean()
                    std_val = subset['rebalance_cycle_pct'].std() if len(subset) > 1 else 0
                    sem_val = subset['rebalance_cycle_pct'].sem() if len(subset) > 1 else 0
                    
                    # Only add if mean value is meaningful (not zero or near-zero)
                    if mean_val > 0.005:  # Skip values less than 0.5% (0.005 in decimal)
                        stats_data.append({
                            'allocator': allocator,
                            'strategy': strategy,
                            'mean': mean_val,
                            'std': std_val,
                            'sem': sem_val,
                            'count': len(subset)
                        })
        
        stats_df = pd.DataFrame(stats_data)
        
        # Create bar plot with dynamic positioning per allocator
        x_positions = np.arange(len(allocator_order))
        bar_width = 0.13
        
        # Get all unique strategies that have data
        all_strategies_with_data = sorted(stats_df['strategy'].unique(), 
                                        key=lambda x: strategy_order.index(x))
        
        # Plot bars for each allocator separately to handle different strategy sets
        legend_added = set()
        
        for allocator_idx, allocator in enumerate(allocator_order):
            # Get strategies that have data for this specific allocator
            allocator_strategies = stats_df[stats_df['allocator'] == allocator]['strategy'].tolist()
            allocator_strategies = sorted(allocator_strategies, key=lambda x: strategy_order.index(x))
            
            if not allocator_strategies:
                continue
                
            # Calculate positions for this allocator's bars
            n_bars = len(allocator_strategies)
            start_offset = -(n_bars - 1) * bar_width / 2
            
            for i, strategy in enumerate(allocator_strategies):
                position = x_positions[allocator_idx] + start_offset + i * bar_width
                
                # Get data for this specific combination
                row = stats_df[(stats_df['allocator'] == allocator) & 
                              (stats_df['strategy'] == strategy)].iloc[0]
                
                # Add label only once per strategy for legend
                label = strategy_labels.get(strategy, strategy) if strategy not in legend_added else ""
                if strategy not in legend_added:
                    legend_added.add(strategy)
                
                ax.bar(position, row['mean'], bar_width,
                      label=label,
                      color=strategy_colors.get(strategy, '#808080'),
                      yerr=row['sem'], capsize=4,
                      edgecolor='black', linewidth=0.5)
        
        # Customize the plot
        ax.set_xlabel('Eviction Policy')
        ax.set_ylabel('Rebalancing CPU Cycles Relative to\nRequest Serving CPU Cycles (%)')
        ax.set_xticks(x_positions)
        ax.set_xticklabels(allocator_labels)
        
        # Add dashed vertical lines to separate different eviction policies
        for i in range(len(allocator_order) - 1):
            separator_x = x_positions[i] + 0.5
            ax.axvline(x=separator_x, color='gray', linestyle='--', alpha=0.6, linewidth=1)
        
        # Add grid
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_axisbelow(True)
        
        # Position legend at the top
        ax.legend(bbox_to_anchor=(0.5, 1.02), loc='lower center', ncol=3, frameon=True, shadow=True, 
                              framealpha=0.9, edgecolor='black')
        
        # Format y-axis as percentage
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y*100:.1f}'))
        
        # Tight layout
        plt.tight_layout()
        
        # Save the plot
        wsr_str = f"{wsr:.2f}".replace('.', '_')
        output_file = os.path.join(output_dir, f'overhead_analysis_wsr_{wsr_str}.pdf')
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Plot saved to {output_file}")
        
        # Print summary statistics
        print(f"\n=== Summary Statistics for WSR = {wsr} ===")
        print(f"Total combinations in stats_df: {len(stats_df)}")
        
        all_strategies_with_data = sorted(stats_df['strategy'].unique(), 
                                        key=lambda x: strategy_order.index(x))
        
        for strategy in all_strategies_with_data:
            strategy_stats = stats_df[stats_df['strategy'] == strategy]
            print(f"\n{strategy_labels.get(strategy, strategy)}:")
            for _, row in strategy_stats.iterrows():
                print(f"  {row['allocator']}: mean={row['mean']*100:.2f}%, std={row['std']*100:.2f}%, n={row['count']}")
                
        # Debug: Show which combinations have data
        print(f"\n=== Debug: Data combinations ===")
        for _, row in stats_df.iterrows():
            print(f"  {row['strategy']} + {row['allocator']}: {row['mean']*100:.3f}%")
        
        plt.show()

def plot_overhead_cycles(output_dir='.'):
    """
    Plot overhead analysis showing pool_rebalancer_cpu_cycles by allocator and strategy.
    Creates bar plots with mean and error bars for each WSR value.
    """
    
    # Read the data
    csv_path = '../data/overhead/meta_2022_overhead.csv'
    print(f"Reading data from {csv_path}")
    
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        return
    
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} rows")
    
    # Filter out disabled strategy
    df = df[df['rebalance_strategy'] != 'disabled']
    print(f"After filtering out disabled strategy: {len(df)} rows")
    
    # Define strategy labels and colors
    strategy_labels = {
        "tail-age": r"$\mathit{Tail\text{-}Age}$",
        "eviction-rate": r"$\mathit{Eviction\text{-}Rate}$",
        "hits": r"$\mathit{Hits\text{-}Per\text{-}Slab}$",
        "lama": r"$\mathit{LAMA}$",
        "marginal-hits": r"$\mathit{Marginal\text{-}Hits}$",
        "marginal-hits-tuned": r"$\mathit{Marginal\text{-}Hits\text{-}Tuned}$"
    }
    
    # Enforce order for rebalance strategies 
    strategy_order = ["tail-age", "eviction-rate", "hits", "lama", "marginal-hits", "marginal-hits-tuned"]
    
    strategy_colors = {
        "tail-age": "#AB63FA", 
        "eviction-rate": "#FFA15A",
        "hits": "#00CC96",
        "lama": "#8B4513",  # Chocolate brown color
        "marginal-hits": "#EF553B",
        "marginal-hits-tuned": "#2E8B57"
    }
    
    # Define allocator order and labels
    allocator_order = ['LRU', 'TwoQ', 'TinyLFU']
    allocator_labels = ['LRU', 'TwoQ', 'TinyLFU']
    
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
        'grid.alpha': 0.3,
        'figure.figsize': (14, 8)
    })
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Create plots for both WSR values
    wsr_values = [0.1, 0.01]
    
    for wsr in wsr_values:
        # Filter data for current WSR
        wsr_data = df[df['wsr'] == wsr].copy()
        print(f"\nProcessing WSR = {wsr}")
        print(f"Data points for WSR {wsr}: {len(wsr_data)}")
        
        if len(wsr_data) == 0:
            print(f"No data found for WSR = {wsr}")
            continue
        
        # Create figure
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Calculate statistics for each allocator-strategy combination
        stats_data = []
        for allocator in allocator_order:
            for strategy in strategy_order:
                # Skip LAMA for non-LRU allocators
                if strategy == 'lama' and allocator != 'LRU':
                    continue
                    
                subset = wsr_data[
                    (wsr_data['allocator'] == allocator) & 
                    (wsr_data['rebalance_strategy'] == strategy)
                ]
                
                if len(subset) > 0:
                    mean_val = subset['pool_rebalancer_cpu_cycles'].mean()
                    std_val = subset['pool_rebalancer_cpu_cycles'].std() if len(subset) > 1 else 0
                    sem_val = subset['pool_rebalancer_cpu_cycles'].sem() if len(subset) > 1 else 0
                    
                    # Only add if mean value is meaningful (not zero or near-zero)
                    if mean_val > 1000:  # Skip values less than 1000 cycles
                        stats_data.append({
                            'allocator': allocator,
                            'strategy': strategy,
                            'mean': mean_val,
                            'std': std_val,
                            'sem': sem_val,
                            'count': len(subset)
                        })
        
        stats_df = pd.DataFrame(stats_data)
        
        # Create bar plot with dynamic positioning per allocator
        x_positions = np.arange(len(allocator_order))
        bar_width = 0.13
        
        # Get all unique strategies that have data
        all_strategies_with_data = sorted(stats_df['strategy'].unique(), 
                                        key=lambda x: strategy_order.index(x))
        
        # Plot bars for each allocator separately to handle different strategy sets
        legend_added = set()
        
        for allocator_idx, allocator in enumerate(allocator_order):
            # Get strategies that have data for this specific allocator
            allocator_strategies = stats_df[stats_df['allocator'] == allocator]['strategy'].tolist()
            allocator_strategies = sorted(allocator_strategies, key=lambda x: strategy_order.index(x))
            
            if not allocator_strategies:
                continue
                
            # Calculate positions for this allocator's bars
            n_bars = len(allocator_strategies)
            start_offset = -(n_bars - 1) * bar_width / 2
            
            for i, strategy in enumerate(allocator_strategies):
                position = x_positions[allocator_idx] + start_offset + i * bar_width
                
                # Get data for this specific combination
                row = stats_df[(stats_df['allocator'] == allocator) & 
                              (stats_df['strategy'] == strategy)].iloc[0]
                
                # Add label only once per strategy for legend
                label = strategy_labels.get(strategy, strategy) if strategy not in legend_added else ""
                if strategy not in legend_added:
                    legend_added.add(strategy)
                
                ax.bar(position, row['mean'], bar_width,
                      label=label,
                      color=strategy_colors.get(strategy, '#808080'),
                      yerr=row['sem'], capsize=4,
                      edgecolor='black', linewidth=0.5)
        
        # Customize the plot
        ax.set_xlabel('Eviction Policy')
        ax.set_ylabel('Pool Rebalancer CPU Cycles')
        ax.set_xticks(x_positions)
        ax.set_xticklabels(allocator_labels)
        
        # Add dashed vertical lines to separate different eviction policies
        for i in range(len(allocator_order) - 1):
            separator_x = x_positions[i] + 0.5
            ax.axvline(x=separator_x, color='gray', linestyle='--', alpha=0.6, linewidth=1)
        
        # Add grid
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_axisbelow(True)
        
        # Position legend at the top
        ax.legend(bbox_to_anchor=(0.5, 1.02), loc='lower center', ncol=3, frameon=True, shadow=True, 
                              framealpha=0.9, edgecolor='black')
        
        # Format y-axis with scientific notation for large numbers
        ax.ticklabel_format(style='scientific', axis='y', scilimits=(0,0))
        
        # Tight layout
        plt.tight_layout()
        
        # Save the plot
        wsr_str = f"{wsr:.2f}".replace('.', '_')
        output_file = os.path.join(output_dir, f'overhead_cycles_wsr_{wsr_str}.pdf')
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Plot saved to {output_file}")
        
        # Print summary statistics
        print(f"\n=== Summary Statistics for WSR = {wsr} ===")
        print(f"Total combinations in stats_df: {len(stats_df)}")
        
        all_strategies_with_data = sorted(stats_df['strategy'].unique(), 
                                        key=lambda x: strategy_order.index(x))
        
        for strategy in all_strategies_with_data:
            strategy_stats = stats_df[stats_df['strategy'] == strategy]
            print(f"\n{strategy_labels.get(strategy, strategy)}:")
            for _, row in strategy_stats.iterrows():
                print(f"  {row['allocator']}: mean={row['mean']:.0f} cycles, std={row['std']:.0f} cycles, n={row['count']}")
                
        # Debug: Show which combinations have data
        print(f"\n=== Debug: Data combinations ===")
        for _, row in stats_df.iterrows():
            print(f"  {row['strategy']} + {row['allocator']}: {row['mean']:.0f} cycles")
        
        plt.show()

def plot_overhead_vs_cycles(output_dir='.'):
    """
    Plot overhead analysis showing rebalance cycle percentage vs pool_rebalancer_cpu_cycles.
    Creates scatter plots with different colors for each strategy-allocator combination.
    """
    
    # Read the data
    csv_path = '../data/overhead/meta_2022_overhead.csv'
    print(f"Reading data from {csv_path}")
    
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        return
    
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} rows")
    
    # Filter out disabled strategy
    df = df[df['rebalance_strategy'] != 'disabled']
    print(f"After filtering out disabled strategy: {len(df)} rows")
    
    # Define strategy labels and colors
    strategy_labels = {
        "tail-age": r"$\mathit{Tail\text{-}Age}$",
        "eviction-rate": r"$\mathit{Eviction\text{-}Rate}$",
        "hits": r"$\mathit{Hits\text{-}Per\text{-}Slab}$",
        "lama": r"$\mathit{LAMA}$",
        "marginal-hits": r"$\mathit{Marginal\text{-}Hits}$",
        "marginal-hits-tuned": r"$\mathit{Marginal\text{-}Hits\text{-}Tuned}$"
    }
    
    # Enforce order for rebalance strategies 
    strategy_order = ["tail-age", "eviction-rate", "hits", "lama", "marginal-hits", "marginal-hits-tuned"]
    
    strategy_colors = {
        "tail-age": "#AB63FA", 
        "eviction-rate": "#FFA15A",
        "hits": "#00CC96",
        "lama": "#8B4513",  # Chocolate brown color
        "marginal-hits": "#EF553B",
        "marginal-hits-tuned": "#2E8B57"
    }
    
    # Define allocator order and labels
    allocator_order = ['LRU', 'TwoQ', 'TinyLFU']
    allocator_labels = ['LRU', 'TwoQ', 'TinyLFU']
    
    # Define markers for allocators
    allocator_markers = {
        'LRU': 'o',
        'TwoQ': 's', 
        'TinyLFU': '^'
    }
    
    # Set up matplotlib for publication quality
    plt.rcParams.update({
        'font.size': 20,           
        'axes.titlesize': 24,      
        'axes.labelsize': 22,      
        'xtick.labelsize': 20,     
        'ytick.labelsize': 20,     
        'legend.fontsize': 16,     
        'figure.titlesize': 26,    
        'figure.dpi': 300,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'axes.linewidth': 1.2,
        'grid.linewidth': 0.8,
        'grid.alpha': 0.3,
        'figure.figsize': (14, 8)
    })
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Create plots for both WSR values
    wsr_values = [0.1, 0.01]
    
    for wsr in wsr_values:
        # Filter data for current WSR
        wsr_data = df[df['wsr'] == wsr].copy()
        print(f"\nProcessing WSR = {wsr}")
        print(f"Data points for WSR {wsr}: {len(wsr_data)}")
        
        if len(wsr_data) == 0:
            print(f"No data found for WSR = {wsr}")
            continue
        
        # Create figure
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Plot points for each strategy-allocator combination
        for strategy in strategy_order:
            if strategy not in wsr_data['rebalance_strategy'].values:
                continue
                
            for allocator in allocator_order:
                # Skip LAMA for non-LRU allocators
                if strategy == 'lama' and allocator != 'LRU':
                    continue
                    
                subset = wsr_data[
                    (wsr_data['allocator'] == allocator) & 
                    (wsr_data['rebalance_strategy'] == strategy)
                ]
                
                if len(subset) > 0:
                    # Filter out near-zero values for better visualization
                    subset = subset[subset['rebalance_cycle_pct'] > 0.005]  # Skip values less than 0.5%
                    
                    if len(subset) > 0:
                        x_values = subset['pool_rebalancer_cpu_cycles']
                        y_values = subset['rebalance_cycle_pct']
                        
                        ax.scatter(x_values, y_values,
                                 color=strategy_colors.get(strategy, '#808080'),
                                 marker=allocator_markers[allocator],
                                 s=80, alpha=0.7,
                                 edgecolors='black', linewidth=0.5,
                                 label=f"{strategy_labels.get(strategy, strategy)} + {allocator}")
        
        # Customize the plot
        ax.set_xlabel('Pool Rebalancer CPU Cycles')
        ax.set_ylabel('Rebalancing CPU Cycles Relative to\nRequest Serving CPU Cycles (%)')
        
        # Add grid
        ax.grid(True, alpha=0.3)
        ax.set_axisbelow(True)
        
        # Format y-axis as percentage
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y*100:.1f}'))
        
        # Format x-axis with scientific notation for large numbers
        ax.ticklabel_format(style='scientific', axis='x', scilimits=(0,0))
        
        # Create legend with strategy and allocator information
        handles, labels = ax.get_legend_handles_labels()
        if handles:
            # Position legend outside the plot area
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', frameon=True, shadow=True, 
                     framealpha=0.9, edgecolor='black')
        
        # Tight layout
        plt.tight_layout()
        
        # Save the plot
        wsr_str = f"{wsr:.2f}".replace('.', '_')
        output_file = os.path.join(output_dir, f'overhead_vs_cycles_wsr_{wsr_str}.pdf')
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Plot saved to {output_file}")
        
        # Print summary statistics
        print(f"\n=== Summary Statistics for WSR = {wsr} ===")
        
        for strategy in strategy_order:
            if strategy not in wsr_data['rebalance_strategy'].values:
                continue
                
            print(f"\n{strategy_labels.get(strategy, strategy)}:")
            
            for allocator in allocator_order:
                # Skip LAMA for non-LRU allocators
                if strategy == 'lama' and allocator != 'LRU':
                    continue
                    
                subset = wsr_data[
                    (wsr_data['allocator'] == allocator) & 
                    (wsr_data['rebalance_strategy'] == strategy) &
                    (wsr_data['rebalance_cycle_pct'] > 0.005)
                ]
                
                if len(subset) > 0:
                    cpu_cycles_mean = subset['pool_rebalancer_cpu_cycles'].mean()
                    cpu_cycles_std = subset['pool_rebalancer_cpu_cycles'].std()
                    pct_mean = subset['rebalance_cycle_pct'].mean()
                    pct_std = subset['rebalance_cycle_pct'].std()
                    
                    print(f"  {allocator}: CPU cycles: {cpu_cycles_mean:.0f}±{cpu_cycles_std:.0f}, "
                          f"Percentage: {pct_mean*100:.2f}±{pct_std*100:.2f}%, n={len(subset)}")
        
        plt.show()

if __name__ == "__main__":
    plot_overhead_analysis()
    print("\n" + "="*60)
    print("Generating overhead cycles plots...")
    plot_overhead_cycles()
    print("\n" + "="*60)
    print("Generating overhead vs cycles scatter plots...")
    plot_overhead_vs_cycles()