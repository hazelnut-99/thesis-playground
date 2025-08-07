import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from pathlib import Path

def plot_miss_ratio_reduction(trace_name):
    """
    Plot miss_ratio_reduction_from_lru_disabled for a given trace_name.
    Creates three separate figures, one for each allocator (LRU, LRU2Q, TINYLFU).
    
    Parameters:
    trace_name (str): The trace name to filter the data
    """
    
    # Read the data
    data_path = Path("../data/end-to-end/report_complete_processed.csv")
    df = pd.read_csv(data_path)
    
    # Filter by trace_name
    df_filtered = df[df['trace_name'] == trace_name].copy()
    
    if df_filtered.empty:
        print(f"No data found for trace_name: {trace_name}")
        return
    
    # Convert wsr to percentage
    df_filtered['wsr_percent'] = df_filtered['wsr'] * 100
    
    # Define strategy order for consistent plotting
    strategy_order = ["disabled", "tail-age", "eviction-rate", "hits", "lama", "marginal-hits", "marginal-hits-tuned"]
    
    # Define strategy labels and colors
    strategy_labels = {
        "disabled": r"$\mathit{Disabled}$",
        "tail-age": r"$\mathit{Tail\text{-}Age}$",
        "eviction-rate": r"$\mathit{Eviction\text{-}Rate}$",
        "hits": r"$\mathit{Hits\text{-}Per\text{-}Slab}$",
        "lama": r"$\mathit{LAMA}$",
        "marginal-hits": r"$\mathit{Marginal\text{-}Hits}$",
        "marginal-hits-tuned": r"$\mathit{Marginal\text{-}Hits\text{-}Tuned}$"
    }
    
    strategy_colors = {
        "disabled": "#636EFA",
        "tail-age": "#AB63FA", 
        "eviction-rate": "#FFA15A",
        "hits": "#00CC96",
        "lama": "#8C564B",  # Changed to light green to be distinct
        "marginal-hits": "#EF553B",
        "marginal-hits-tuned": "#2E8B57"
    }
    
    # Define line styles for variety
    strategy_linestyles = {
        "disabled": '-',
        "tail-age": '--',
        "eviction-rate": '-.',
        "hits": ':',
        "lama": (0, (3, 1, 1, 1)),
        "marginal-hits": '--',
        "marginal-hits-tuned": '-'
    }
    
    # Define marker styles
    strategy_markers = {
        "disabled": 'o',
        "tail-age": 's',
        "eviction-rate": '^',
        "hits": 'D',
        "lama": 'v',
        "marginal-hits": 'p',
        "marginal-hits-tuned": 'H'  # Changed from '*' to 'H' (hexagon) for better visibility
    }
    
    # Define allocator order and labels
    allocator_order = ['LRU', 'LRU2Q', 'TINYLFU']
    allocator_labels = ['LRU', 'TwoQ', 'TinyLFU']
    
    # Set up matplotlib for publication quality
    plt.rcParams.update({
        'font.size': 26,           # Increased from 20
        'axes.titlesize': 30,      # Increased from 24
        'axes.labelsize': 28,      # Increased from 22
        'xtick.labelsize': 26,     # Increased from 20
        'ytick.labelsize': 26,     # Increased from 20
        'legend.fontsize': 20,     # Increased from 18
        'figure.titlesize': 28,    # Increased from 26
        'figure.dpi': 300,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'axes.linewidth': 1.2,
        'grid.linewidth': 0.8,
        'grid.alpha': 0.3
    })
    
    # Calculate global y-axis range for miss_ratio across all allocators
    all_miss_ratios = []
    for allocator in allocator_order:
        allocator_data = df_filtered[df_filtered['allocator'] == allocator]
        if not allocator_data.empty:
            all_miss_ratios.extend(allocator_data['miss_ratio'].values)
    
    if all_miss_ratios:
        y_min = min(all_miss_ratios)
        y_max = max(all_miss_ratios)
        # Add some padding (5% on each side)
        y_range = y_max - y_min
        y_min_padded = max(0, y_min - 0.05 * y_range)
        y_max_padded = y_max + 0.05 * y_range
    else:
        y_min_padded, y_max_padded = 0, 1
    
    # Create three separate figures
    for i, (allocator, allocator_label) in enumerate(zip(allocator_order, allocator_labels)):
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Filter data for this allocator
        allocator_data = df_filtered[df_filtered['allocator'] == allocator]
        
        if allocator_data.empty:
            print(f"No data found for allocator: {allocator}")
            continue
        
        # Get unique strategies in this data and order them
        available_strategies = allocator_data['rebalance_strategy'].unique()
        strategies = [s for s in strategy_order if s in available_strategies]
        
        # Plot each strategy in the defined order
        for strategy in strategies:
            strategy_data = allocator_data[allocator_data['rebalance_strategy'] == strategy]
            
            if strategy_data.empty:
                continue
            
            # Sort by wsr_percent for proper line plotting
            strategy_data = strategy_data.sort_values('wsr_percent')
            
            # Get styling
            color = strategy_colors.get(strategy, '#000000')
            label = strategy_labels.get(strategy, strategy)
            linestyle = strategy_linestyles.get(strategy, '-')
            marker = strategy_markers.get(strategy, 'o')
            
            # Plot the line
            ax.plot(strategy_data['wsr_percent'], 
                   strategy_data['miss_ratio'],
                   color=color, 
                   label=label,
                   linestyle=linestyle,
                   marker=marker,
                   markersize=12,
                   linewidth=2.5,
                   markerfacecolor=color,
                   markeredgecolor='white',
                   markeredgewidth=1)
        
        # Customize the plot
        ax.set_xlabel('Cache Size (% of Working Set)')
        ax.set_ylabel('Miss Ratio')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best', frameon=True, fancybox=True, shadow=True)
        
        # Set reasonable axis limits
        ax.set_xlim(left=0)
        ax.set_ylim(y_min_padded, y_max_padded)
        
        # Set x-axis ticks with step size of 10
        ax.set_xticks(np.arange(0, 50, 10))
        
        # Tight layout
        plt.tight_layout()
        
        # Save the figure
        output_path = f"miss_ratio_{trace_name}_{allocator}.pdf"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        
        # Show the plot
        plt.show()
        
        print(f"Saved plot for {allocator_label}: {output_path}")

def plot_rebalanced_slabs(trace_name):
    """
    Plot rebalanced_slabs for a given trace_name.
    Creates three separate figures, one for each allocator (LRU, LRU2Q, TINYLFU).
    
    Parameters:
    trace_name (str): The trace name to filter the data
    """
    
    # Read the data
    data_path = Path("../data/end-to-end/report_complete_processed.csv")
    df = pd.read_csv(data_path)
    
    # Filter by trace_name
    df_filtered = df[df['trace_name'] == trace_name].copy()
    
    if df_filtered.empty:
        print(f"No data found for trace_name: {trace_name}")
        return
    
    # Convert wsr to percentage
    df_filtered['wsr_percent'] = df_filtered['wsr'] * 100
    
    # Define strategy order for consistent plotting
    strategy_order = ["disabled", "tail-age", "eviction-rate", "hits", "lama", "marginal-hits", "marginal-hits-tuned"]
    
    # Define strategy labels and colors
    strategy_labels = {
        "disabled": r"$\mathit{Disabled}$",
        "tail-age": r"$\mathit{Tail\text{-}Age}$",
        "eviction-rate": r"$\mathit{Eviction\text{-}Rate}$",
        "hits": r"$\mathit{Hits\text{-}Per\text{-}Slab}$",
        "lama": r"$\mathit{LAMA}$",
        "marginal-hits": r"$\mathit{Marginal\text{-}Hits}$",
        "marginal-hits-tuned": r"$\mathit{Marginal\text{-}Hits\text{-}Tuned}$"
    }
    
    strategy_colors = {
        "disabled": "#636EFA",
        "tail-age": "#AB63FA", 
        "eviction-rate": "#FFA15A",
        "hits": "#00CC96",
        "lama": "#8C564B",
        "marginal-hits": "#EF553B",
        "marginal-hits-tuned": "#2E8B57"
    }
    
    # Define line styles for variety
    strategy_linestyles = {
        "disabled": '-',
        "tail-age": '--',
        "eviction-rate": '-.',
        "hits": ':',
        "lama": (0, (3, 1, 1, 1)),
        "marginal-hits": '--',
        "marginal-hits-tuned": '-'
    }
    
    # Define marker styles
    strategy_markers = {
        "disabled": 'o',
        "tail-age": 's',
        "eviction-rate": '^',
        "hits": 'D',
        "lama": 'v',
        "marginal-hits": 'p',
        "marginal-hits-tuned": 'H'
    }
    
    # Define allocator order and labels
    allocator_order = ['LRU', 'LRU2Q', 'TINYLFU']
    allocator_labels = ['LRU', 'TwoQ', 'TinyLFU']
    
    # Set up matplotlib for publication quality
    plt.rcParams.update({
        'font.size': 26,           # Increased from 20
        'axes.titlesize': 30,      # Increased from 24
        'axes.labelsize': 28,      # Increased from 22
        'xtick.labelsize': 26,     # Increased from 20
        'ytick.labelsize': 26,     # Increased from 20
        'legend.fontsize': 20,     # Increased from 18
        'figure.titlesize': 28,    # Increased from 26
        'figure.dpi': 300,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'axes.linewidth': 1.2,
        'grid.linewidth': 0.8,
        'grid.alpha': 0.3
    })
    
    # Calculate global y-axis range for rebalanced_slabs across all allocators
    all_rebalanced_slabs = []
    for allocator in allocator_order:
        allocator_data = df_filtered[df_filtered['allocator'] == allocator]
        if not allocator_data.empty:
            all_rebalanced_slabs.extend(allocator_data['rebalanced_slabs'].values)
    
    if all_rebalanced_slabs:
        y_min = min(all_rebalanced_slabs)
        y_max = max(all_rebalanced_slabs)
        # Add some padding (5% on each side)
        y_range = y_max - y_min
        y_min_padded = max(0, y_min - 0.05 * y_range)
        y_max_padded = y_max + 0.05 * y_range
    else:
        y_min_padded, y_max_padded = 0, 100
    
    # Create three separate figures
    for i, (allocator, allocator_label) in enumerate(zip(allocator_order, allocator_labels)):
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Filter data for this allocator
        allocator_data = df_filtered[df_filtered['allocator'] == allocator]
        
        if allocator_data.empty:
            print(f"No data found for allocator: {allocator}")
            continue
        
        # Get unique strategies in this data and order them
        available_strategies = allocator_data['rebalance_strategy'].unique()
        strategies = [s for s in strategy_order if s in available_strategies]
        
        # Plot each strategy in the defined order
        for strategy in strategies:
            strategy_data = allocator_data[allocator_data['rebalance_strategy'] == strategy]
            
            if strategy_data.empty:
                continue
            
            # Sort by wsr_percent for proper line plotting
            strategy_data = strategy_data.sort_values('wsr_percent')
            
            # Get styling
            color = strategy_colors.get(strategy, '#000000')
            label = strategy_labels.get(strategy, strategy)
            linestyle = strategy_linestyles.get(strategy, '-')
            marker = strategy_markers.get(strategy, 'o')
            
            # Plot the line
            ax.plot(strategy_data['wsr_percent'], 
                   strategy_data['rebalanced_slabs'],
                   color=color, 
                   label=label,
                   linestyle=linestyle,
                   marker=marker,
                   markersize=12,
                   linewidth=2.5,
                   markerfacecolor=color,
                   markeredgecolor='white',
                   markeredgewidth=1)
        
        # Customize the plot
        ax.set_xlabel('Cache Size (% of Working Set)')
        ax.set_ylabel('Number of Rebalanced Slabs')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best', frameon=True, fancybox=True, shadow=True)
        
        # Set reasonable axis limits
        ax.set_xlim(left=0)
        ax.set_ylim(y_min_padded, y_max_padded)
        
        # Set x-axis ticks with step size of 10
        ax.set_xticks(np.arange(0, 50, 10))
        
        # Tight layout
        plt.tight_layout()
        
        # Save the figure
        output_path = f"rebalanced_slabs_{trace_name}_{allocator}.pdf"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        
        # Show the plot
        plt.show()
        
        print(f"Saved plot for {allocator_label}: {output_path}")

# Example usage
if __name__ == "__main__":
    # Example: plot for meta_202210_kv trace
    plot_miss_ratio_reduction("meta_202210_kv")
    plot_miss_ratio_reduction("meta_202401_kv")
    plot_miss_ratio_reduction("meta_memcache_2024_kv")
    
    # Plot rebalanced slabs
    plot_rebalanced_slabs("meta_202210_kv")
    plot_rebalanced_slabs("meta_202401_kv")
    plot_rebalanced_slabs("meta_memcache_2024_kv")