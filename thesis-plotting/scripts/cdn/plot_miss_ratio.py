"""
Scatter plot visualization for CDN cache performance analysis.
Creates three aligned subplots (one per allocator) with:
- X-axis: Rebalance strategy
- Y-axis: Miss ratio reduction (aligned across subplots)
- Color: High contrast colors for trace categories and names
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

def create_cdn_miss_ratio_scatter(csv_file, output_dir):
    """
    Create three-panel scatter plot showing miss ratio reduction by allocator.
    
    Args:
        csv_file: Path to the CSV file
        output_dir: Directory to save the plot
    """
    
    # Read the CSV file
    df = pd.read_csv(csv_file)
    
    # Create trace_category column
    df['trace_category'] = df['trace_name'].apply(
        lambda x: 'Meta' if x.startswith('meta') else 'Wiki' if x.startswith('wiki') else 'Other'
    )
    
    print(f"Available strategies: {df['rebalance_strategy'].unique()}")
    print(f"Trace categories: {df['trace_category'].value_counts().to_dict()}")
    
    # Set up the plotting style for publication quality
    plt.rcParams.update({
        'font.size': 14,
        'axes.titlesize': 16,
        'axes.labelsize': 14,
        'xtick.labelsize': 12,
        'ytick.labelsize': 12,
        'legend.fontsize': 10,
        'figure.titlesize': 18,
        'figure.dpi': 300,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight'
    })
    
    # Define allocator order and labels
    allocator_order = ['LRU', 'LRU2Q', 'TINYLFU']
    allocator_labels = ['LRU', 'TwoQ', 'TinyLFU']
    
    # Get unique strategies and enforce specific order
    strategy_order = ["disabled", "tail-age", "free-mem", "hits", "marginal-hits", "marginal-hits-tuned"]
    available_strategies = df['rebalance_strategy'].unique()
    strategies = [s for s in strategy_order if s in available_strategies]
    
    # Add any missing strategies not in the predefined order
    for s in available_strategies:
        if s not in strategies:
            strategies.append(s)
    
    # Strategy labels with LaTeX formatting
    strategy_labels = {
        "disabled": r"$\mathit{Disabled}$",
        "tail-age": r"$\mathit{LRU\text{-}Tail\text{-}Age}$",
        "free-mem": r"$\mathit{Free\text{-}Memory}$",
        "hits": r"$\mathit{Hits\text{-}Per\text{-}Slab}$",
        "marginal-hits": r"$\mathit{Marginal\text{-}Hits}$",
        "marginal-hits-tuned": r"$\mathit{Marginal\text{-}Hits\text{-}Tuned}$"
    }
    
    # Define high contrast colors for each trace category and trace name
    # Get unique trace names per category
    meta_traces = sorted(df[df['trace_category'] == 'Meta']['trace_name'].unique())
    wiki_traces = sorted(df[df['trace_category'] == 'Wiki']['trace_name'].unique())
    
    # Color scheme based on trace category with intensity for trace names
    # Meta (KV) - Orange circles, Meta (CDN) - Red diamonds, Tencent - Blue triangles, Wiki - Green squares
    color_map = {}
    shape_map = {}
    
    # Define color palettes for each category (light to dark) with higher contrast
    meta_cdn_colors = ['#FFB3B3', '#FF6666', '#CC0000']  # Light red to dark red (3 shades)
    meta_kv_colors = ['#FFCC99', '#FF9933']              # Light orange to dark orange (2 shades) 
    tencent_colors = ['#90EE90', '#006400']                 # Light green to dark green (higher contrast)
    wiki_colors = ['#B3D9FF', '#3399FF', '#0066CC']     # Light blue to dark blue (3 shades)
    
    # Assign colors and shapes based on trace names and categories
    meta_cdn_traces = []
    meta_kv_traces = []
    
    for trace in meta_traces:
        if 'kv' in trace.lower() or 'key' in trace.lower():
            meta_kv_traces.append(trace)
            shape_map[trace] = 'o'        # Circle
        else:
            meta_cdn_traces.append(trace)
            shape_map[trace] = 'D'        # Diamond
    
    # Assign colors with intensity (light to dark)
    for i, trace in enumerate(sorted(meta_cdn_traces)):
        color_map[trace] = meta_cdn_colors[i % len(meta_cdn_colors)]
    
    for i, trace in enumerate(sorted(meta_kv_traces)):
        color_map[trace] = meta_kv_colors[i % len(meta_kv_colors)]
    
    for i, trace in enumerate(sorted(wiki_traces)):
        color_map[trace] = wiki_colors[i % len(wiki_colors)]
        shape_map[trace] = 's'            # Square
    
    # Handle any Tencent traces (if they exist)
    tencent_traces = [t for t in df['trace_name'].unique() if 'tencent' in t.lower()]
    for i, trace in enumerate(sorted(tencent_traces)):
        color_map[trace] = tencent_colors[i % len(tencent_colors)]
        shape_map[trace] = '^'            # Triangle up
    
    # Find global y-axis limits for alignment
    y_min = df['miss_ratio_reduction_from_lru_disabled'].min()
    y_max = df['miss_ratio_reduction_from_lru_disabled'].max()
    y_margin = (y_max - y_min) * 0.1
    y_limits = (y_min - y_margin, y_max + y_margin)
    
    # Create figure with three subplots (more compact)
    fig, axes = plt.subplots(1, 3, figsize=(15, 6), sharey=True)
    
    for idx, allocator in enumerate(allocator_order):
        ax = axes[idx]
        
        # Filter data for this allocator
        allocator_data = df[df['allocator'] == allocator]
        
        if allocator_data.empty:
            ax.set_title(f'{allocator_labels[idx]} (No Data)')
            continue
        
        # Plot data for each strategy
        for i, strategy in enumerate(strategies):
            strategy_data = allocator_data[allocator_data['rebalance_strategy'] == strategy]
            
            if strategy_data.empty:
                continue
            
            # Add smaller jitter to x-position for visibility (more compact)
            x_positions = np.full(len(strategy_data), i) + np.random.normal(0, 0.05, len(strategy_data))
            
            # Plot each trace
            for _, row in strategy_data.iterrows():
                trace_name = row['trace_name']
                trace_category = row['trace_category']
                y_value = row['miss_ratio_reduction_from_lru_disabled']
                
                color = color_map.get(trace_name, 'gray')
                marker = shape_map.get(trace_name, 'o')  # Use shape from mapping
                
                ax.scatter(x_positions[list(strategy_data.index).index(row.name)], y_value,
                          c=color, marker=marker, s=80, alpha=0.8, linewidth=0.8)
        
        # Customize subplot
        ax.set_title(f'{allocator_labels[idx]}')
        ax.set_xlabel('Rebalance Strategy')
        if idx == 0:  # Only leftmost plot gets y-label
            ax.set_ylabel('Miss Ratio Reduction\nover LRU + Disabled')
        
        # Set x-axis with LaTeX labels
        ax.set_xticks(range(len(strategies)))
        ax.set_xticklabels([strategy_labels.get(s, s.replace('-', '-')) for s in strategies], 
                          rotation=45, ha='right')
        ax.set_xlim(-0.5, len(strategies) - 0.5)
        
        # Set aligned y-axis
        ax.set_ylim(y_limits)
        
        # Add grid
        ax.grid(True, alpha=0.3)
        
        # Add horizontal line at y=0 for reference
        ax.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    
    # Create legends
    # Legend for trace categories (shapes and colors combined)
    legend_elements = []
    
    # Add all traces with their specific colors and shapes
    all_traces = meta_cdn_traces + meta_kv_traces + wiki_traces + tencent_traces
    for trace in all_traces:
        if trace in color_map and trace in shape_map:
            # Determine category label
            if trace in meta_cdn_traces:
                category_label = 'Meta (CDN)'
            elif trace in meta_kv_traces:
                category_label = 'Meta (KV)'
            elif trace in wiki_traces:
                category_label = 'Wiki'
            else:
                category_label = 'Tencent'
            
            legend_elements.append(
                plt.Line2D([0], [0], marker=shape_map[trace], color='w', 
                          markerfacecolor=color_map[trace], markersize=10,
                          markeredgecolor='black', markeredgewidth=0.8,
                          label=f'{category_label}: {trace}')
            )
    
    # Add legend at the top of the figure
    fig.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 1.05),
               ncol=3)
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.82)  # Make room for top legend
    
    # Save the plot
    output_path = os.path.join(output_dir, 'cdn_miss_ratio_scatter_by_allocator.pdf')
    plt.savefig(output_path, format='pdf', dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"Plot saved to: {output_path}")
    
    # Print some statistics
    print(f"\nData summary:")
    print(f"Total data points: {len(df)}")
    print(f"Meta traces: {meta_traces}")
    print(f"Wiki traces: {wiki_traces}")
    print(f"Strategies: {strategies}")

if __name__ == "__main__":
    # File paths
    csv_file = "report_cdn_digest.csv"
    output_dir = "."
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create the plot
    create_cdn_miss_ratio_scatter(csv_file, output_dir)

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
import os

def create_cdn_miss_ratio_scatter(csv_file, output_dir):
    """
    Create scatter plot showing miss ratio reduction with multiple visual encodings.
    
    Args:
        csv_file: Path to the CSV file
        output_dir: Directory to save the plot
    """
    
    # Read the CSV file
    df = pd.read_csv(csv_file)
    
    # Create trace_category column
    df['trace_category'] = df['trace_name'].apply(
        lambda x: 'Meta' if x.startswith('meta') else 'Wiki' if x.startswith('wiki') else 'Other'
    )
    
    # Keep all strategies including 'disabled'
    print(f"Available strategies: {df['rebalance_strategy'].unique()}")
    
    # Set up the plotting style for publication quality
    plt.rcParams.update({
        'font.size': 16,
        'axes.titlesize': 18,
        'axes.labelsize': 16,
        'xtick.labelsize': 14,
        'ytick.labelsize': 14,
        'legend.fontsize': 12,
        'figure.titlesize': 20,
        'figure.dpi': 300,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight'
    })
    
    # Define allocator order and labels
    allocator_order = ['LRU', 'LRU2Q', 'TINYLFU']
    allocator_labels = ['LRU', 'TwoQ', 'TinyLFU']
    
    # Define rebalance strategies and their visual properties
    strategies = df['rebalance_strategy'].unique()
    strategy_shapes = {
        'disabled': 'X',              # X mark
        'tail-age': 'o',              # circle
        'free-mem': 's',              # square  
        'hits': '^',                  # triangle up
        'marginal-hits': 'D',         # diamond
        'marginal-hits-tuned': 'v'    # triangle down
    }
    
    # Define colors for trace categories
    meta_colors = ['#E3F2FD', '#BBDEFB', '#90CAF9', '#64B5F6', '#42A5F5', '#2196F3', '#1E88E5', '#1976D2']
    wiki_colors = ['#FFEBEE', '#FFCDD2', '#EF9A9A', '#E57373', '#EF5350', '#F44336', '#E53935', '#D32F2F']
    
    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(14, 8))
    
    # Process each combination
    x_positions = []
    y_values = []
    colors = []
    shapes = []
    labels = []
    
    for i, allocator in enumerate(allocator_order):
        if allocator not in df['allocator'].values:
            continue
            
        allocator_data = df[df['allocator'] == allocator]
        
        for j, strategy in enumerate(strategies):
            if strategy not in allocator_data['rebalance_strategy'].values:
                continue
                
            strategy_data = allocator_data[allocator_data['rebalance_strategy'] == strategy]
            
            # Add jitter for strategy separation within allocator
            strategy_offset = (j - len(strategies)/2) * 0.12
            
            for _, row in strategy_data.iterrows():
                # X position: allocator + strategy offset + small random jitter
                x_pos = i + strategy_offset + np.random.normal(0, 0.02)
                x_positions.append(x_pos)
                
                # Y value
                y_values.append(row['miss_ratio_reduction_from_lru_disabled'])
                
                # Color based on trace category and name
                trace_category = row['trace_category']
                trace_name = row['trace_name']
                
                # Get unique trace names within category for color intensity
                if trace_category == 'Meta':
                    category_traces = sorted(df[df['trace_category'] == 'Meta']['trace_name'].unique())
                    color_idx = category_traces.index(trace_name) % len(meta_colors)
                    colors.append(meta_colors[color_idx])
                elif trace_category == 'Wiki':
                    category_traces = sorted(df[df['trace_category'] == 'Wiki']['trace_name'].unique())
                    color_idx = category_traces.index(trace_name) % len(wiki_colors)
                    colors.append(wiki_colors[color_idx])
                else:
                    colors.append('gray')
                
                # Shape based on strategy
                shapes.append(strategy_shapes.get(strategy, 'o'))
                
                # Label for legend
                labels.append(f"{trace_category}-{strategy}")
    
    # Create scatter plot
    for i in range(len(x_positions)):
        ax.scatter(x_positions[i], y_values[i], 
                  c=colors[i], marker=shapes[i], s=60, 
                  alpha=0.7, edgecolors='black', linewidth=0.5)
    
    # Customize the plot
    ax.set_xlabel('Allocator')
    ax.set_ylabel('Miss Ratio Reduction from LRU-Disabled')
    ax.set_title('CDN Cache Performance: Miss Ratio Reduction by Configuration')
    
    # Set x-axis
    ax.set_xticks(range(len(allocator_order)))
    ax.set_xticklabels(allocator_labels)
    ax.set_xlim(-0.5, len(allocator_order) - 0.5)
    
    # Add grid
    ax.grid(True, alpha=0.3)
    
    # Add horizontal line at y=0 for reference
    ax.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    
    # Create custom legends
    # Legend for trace categories (colors)
    meta_patch = plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#2196F3', 
                           markersize=8, label='Meta traces')
    wiki_patch = plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#F44336', 
                           markersize=8, label='Wiki traces')
    
    # Legend for strategies (shapes)
    strategy_patches = []
    for strategy in sorted(strategies):  # Sort for consistent order
        if strategy in strategy_shapes:
            patch = plt.Line2D([0], [0], marker=strategy_shapes[strategy], color='w', 
                             markerfacecolor='gray', markersize=8, 
                             label=strategy.replace('-', '-'))
            strategy_patches.append(patch)
    
    # Add legends
    legend1 = ax.legend(handles=[meta_patch, wiki_patch], 
                       loc='upper left', title='Trace Category')
    ax.add_artist(legend1)
    
    legend2 = ax.legend(handles=strategy_patches, 
                       loc='upper right', title='Rebalance Strategy')
    
    plt.tight_layout()
    
    # Save the plot
    output_path = os.path.join(output_dir, 'cdn_miss_ratio_scatter.pdf')
    plt.savefig(output_path, format='pdf', dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"Plot saved to: {output_path}")
    
    # Print some statistics
    print(f"\nData summary:")
    print(f"Total data points: {len(df)}")
    print(f"Trace categories: {df['trace_category'].value_counts().to_dict()}")
    print(f"Unique traces: {df['trace_name'].nunique()}")
    print(f"Strategies: {list(strategies)}")

if __name__ == "__main__":
    # File paths
    csv_file = "report_cdn_digest.csv"
    output_dir = "."
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create the plot
    create_cdn_miss_ratio_scatter(csv_file, output_dir)