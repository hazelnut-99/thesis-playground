import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Set publication quality parameters
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 16
plt.rcParams['axes.labelsize'] = 18
plt.rcParams['axes.titlesize'] = 20
plt.rcParams['xtick.labelsize'] = 16
plt.rcParams['ytick.labelsize'] = 16
plt.rcParams['legend.fontsize'] = 14

# Define strategy labels and colors (with better contrast)
strategy_labels = {
    "disabled": r"$\mathit{Disabled}$",
    "tail-age": r"$\mathit{LRU\text{-}Tail\text{-}Age}$",
    "free-mem": r"$\mathit{Free\text{-}Memory}$",
    "hits": r"$\mathit{Hits\text{-}Per\text{-}Slab}$",
    "marginal-hits": r"$\mathit{Marginal\text{-}Hits}$",
    "marginal-hits-tuned": r"$\mathit{Marginal\text{-}Hits\text{-}Tuned}$"
}

strategy_colors = {
    "disabled": "#636EFA",
    "tail-age": "#AB63FA",
    "free-mem": "#FFA15A",
    "hits": "#00CC96",
    "marginal-hits": "#EF553B",
    "marginal-hits-tuned": "#2E8B57"  # SeaGreen - much better contrast
}

# Define markers for different strategies
strategy_markers = {
    "disabled": "o",
    "tail-age": "s",
    "free-mem": "^",
    "hits": "D",
    "marginal-hits": "v",
    "marginal-hits-tuned": "P"  # Plus (filled) marker
}

# Load data
# Create a dummy CSV for demonstration purposes if 'miss_ratios_synthetic.csv' is not found
try:
    df = pd.read_csv('miss_ratios_synthetic.csv')
except FileNotFoundError:
    print("Generating dummy data because 'miss_ratios_synthetic.csv' was not found.")
    data = []
    traces = ["synth_static_202", "synth_dynamic_400"]
    allocators = ['LRU', 'LRU2Q', 'TINYLFU']
    strategies = list(strategy_labels.keys())
    wsr_values = np.linspace(10, 100, 10)
    for trace in traces:
        for allocator in allocators:
            for strategy in strategies:
                for wsr in wsr_values:
                    miss_ratio = 1 - (wsr / 100) * (0.5 + np.random.rand() * 0.4) - (strategies.index(strategy) * 0.05)
                    n_rebalanced = np.random.randint(0, 50) * (1 if strategy != "disabled" else 0)
                    data.append({
                        'trace_name': trace,
                        'allocator': allocator,
                        'rebalance_strategy': strategy,
                        'wsr': wsr,
                        'miss_ratio': max(0, miss_ratio),
                        'n_rebalanced_slabs': n_rebalanced
                    })
    df = pd.DataFrame(data)


def create_figure(trace_name, filename):
    """
    Creates and saves a 3x2 plot for a given trace, with corrected label positioning.
    """
    # Filter data for the specific trace
    trace_data = df[df['trace_name'] == trace_name]
    trace_data['wsr'] = trace_data['wsr'] * 100
    
    # Create figure with subplots
    fig, axes = plt.subplots(3, 2, figsize=(14, 16))
    
    allocators = ['LRU', 'LRU2Q', 'TINYLFU']
    allocator_labels = ['LRU', 'TwoQ', 'TinyLFU']
    subplot_labels = [['(a)', '(b)'], ['(c)', '(d)'], ['(e)', '(f)']]
    
    # Add legend at the top of the figure
    handles, labels = [], []
    for strategy in strategy_labels.keys():
        line = plt.Line2D([0], [0], marker=strategy_markers[strategy], 
                         color=strategy_colors[strategy], label=strategy_labels[strategy],
                         linewidth=2, markersize=8)
        handles.append(line)
        labels.append(strategy_labels[strategy])
    
    fig.legend(handles, labels, loc='upper center', 
               bbox_to_anchor=(0.5, 1.02), ncol=6, fontsize=16)
    
    # --- Main Plotting Loop ---
    for i, (allocator, allocator_label) in enumerate(zip(allocators, allocator_labels)):
        alloc_data = trace_data[trace_data['allocator'] == allocator]
        
        # Left plot: Miss Ratio
        ax_left = axes[i, 0]
        # Move subplot label higher to avoid overlap
        ax_left.text(-0.1, 1.15, subplot_labels[i][0], transform=ax_left.transAxes,
                    fontsize=18, fontweight='bold', ha='left', va='top')
        
        for strategy in strategy_labels.keys():
            strategy_data = alloc_data[alloc_data['rebalance_strategy'] == strategy]
            if not strategy_data.empty:
                ax_left.plot(strategy_data['wsr'], strategy_data['miss_ratio'],
                           marker=strategy_markers[strategy], 
                           color=strategy_colors[strategy],
                           linewidth=2, markersize=8)
        
        ax_left.set_xlabel('Cache Size (X% of Working Set)')
        ax_left.set_ylabel('Miss Ratio')
        ax_left.grid(True, alpha=0.3)
        
        # Right plot: Number of Rebalanced Slabs
        ax_right = axes[i, 1]
        # Move subplot label higher to avoid overlap
        ax_right.text(-0.1, 1.15, subplot_labels[i][1], transform=ax_right.transAxes,
                     fontsize=18, fontweight='bold', ha='left', va='top')
        
        for strategy in strategy_labels.keys():
            strategy_data = alloc_data[alloc_data['rebalance_strategy'] == strategy]
            if not strategy_data.empty:
                ax_right.plot(strategy_data['wsr'], strategy_data['n_rebalanced_slabs'],
                            marker=strategy_markers[strategy],
                            color=strategy_colors[strategy],
                            linewidth=2, markersize=8)
        
        ax_right.set_xlabel('Cache Size (X% of Working Set)')
        ax_right.set_ylabel('Number of Rebalanced Slabs')
        ax_right.grid(True, alpha=0.3)
    
    # --- Layout Adjustment and Labeling ---
    # 1. Apply tight_layout to arrange subplots automatically.
    plt.tight_layout()
    
    # 2. Use subplots_adjust to fine-tune spacing AFTER tight_layout.
    #    We increase `top` to prevent overlap with the legend and `hspace` to create
    #    more vertical space between rows for our allocator labels.
    plt.subplots_adjust(top=0.92, hspace=0.8)
    
    # 3. NOW, add the allocator labels into the newly created space.
    #    This is done in a separate loop AFTER the layout is finalized.
    for i, label in enumerate(allocator_labels):
        # Get the top of the current row of axes in figure coordinates.
        row_top_y = axes[i, 0].get_position().y1
        
        # Get the bottom of the row above (or the top of the figure's subplot area for the first row).
        if i == 0:
            # The space above the first row is between its top and the figure's subplot top margin.
            space_top_y = fig.subplotpars.top
            # Position for 'LRU' label. Needs to be placed higher in its available space.
            label_y_pos = row_top_y + (space_top_y - row_top_y) * 0.75 + 0.05
        else:
            # The space for other rows is between its top and the bottom of the row above it.
            space_top_y = axes[i-1, 0].get_position().y0
            # Position for 'TwoQ' and 'TinyLFU'. Needs to be placed lower in their available space.
            label_y_pos = row_top_y + (space_top_y - row_top_y) * 0.3
        
        fig.text(0.5, label_y_pos, label, ha='center', va='center', 
                 fontsize=22, fontweight='bold')
    
    # Save the figure
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.show()

# --- Create Figures ---
# Note: I added a try/except block to generate dummy data if your CSV is not found.
# This makes the script runnable for anyone.
create_figure("synth_static_202", "synth_static_202_analysis.pdf")
create_figure("synth_dynamic_400", "synth_dynamic_400_analysis.pdf")
