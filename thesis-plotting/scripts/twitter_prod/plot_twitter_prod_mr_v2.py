import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def create_twitter_prod_boxplots(csv_file):
    """
    Create box plots for Twitter production data showing m        # Create legend with matching saturation (alpha=1)
        legend_elements = []
        # Use consistent strategy order for legend (include LAMA)
        legend_strategy_order = ["disabled", "tail-age", "eviction-rate", "hits", "lama", "marginal-hits", "marginal-hits-tuned"]
        strategies_in_data = set(wsr_data['rebalance_strategy'].unique())
        
        # Only include strategies that exist in the data
        for strategy in legend_strategy_order:o reduction.
    """
    
    # Read the CSV file
    df = pd.read_csv(csv_file)
    df = df[(df['trace_name'].str.startswith('twitter')) & (df['tag'] != 'warm-cold') & 
            df['miss_ratio_reduction_from_lru_disabled'].notna()]
    
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
    
    # Define allocator order and labels
    allocator_order = ['LRU', 'LRU2Q', 'TINYLFU']
    allocator_labels = ['LRU', 'TwoQ', 'TinyLFU']
    
    # Set up matplotlib for publication quality
    plt.rcParams.update({
        'font.size': 20,           # Increased from 18
        'axes.titlesize': 24,      # Increased from 20
        'axes.labelsize': 22,      # Increased from 18
        'xtick.labelsize': 20,     # Increased from 16  
        'ytick.labelsize': 20,     # Increased from 16
        'legend.fontsize': 18,     # Increased from 16
        'figure.titlesize': 26,    # Increased from 22
        'figure.dpi': 300,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'axes.linewidth': 1.2,
        'grid.linewidth': 0.8,
        'grid.alpha': 0.3
    })
    
    # Create plots for both WSR values
    wsr_values = [0.1, 0.01]
    
    for wsr in wsr_values:
        # Filter data for current WSR
        wsr_data = df[df['wsr'] == wsr].copy()
        
        if wsr_data.empty:
            print(f"No data found for WSR = {wsr}")
            continue
        
        # Create figure - slightly narrower and taller for better proportions
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Prepare data for box plots
        box_data = []
        box_labels = []
        box_colors = []
        positions = []
        mean_values = []  # Store mean values for triangle markers
        
        pos = 0
        # Define strategy order - LAMA only for LRU, others for all allocators
        strategy_order_lru = ["disabled", "tail-age", "eviction-rate", "hits", "lama", "marginal-hits", "marginal-hits-tuned"]
        strategy_order_other = ["disabled", "tail-age", "eviction-rate", "hits", "marginal-hits", "marginal-hits-tuned"]
        
        for i, allocator in enumerate(allocator_order):
            allocator_data = wsr_data[wsr_data['allocator'] == allocator]
            
            if allocator_data.empty:
                print(f"WSR {wsr}: No data for {allocator}")
                continue
            
            print(f"WSR {wsr}, {allocator}: {len(allocator_data)} rows, strategies: {list(allocator_data['rebalance_strategy'].unique())}")
            
            # Add vertical separator line (except before first allocator)
            if i > 0:
                ax.axvline(x=pos - 0.5, color='gray', linestyle='--', alpha=0.5, linewidth=1)  # Increased spacing to avoid box overlap
            
            boxes_added = 0
            # Use different strategy order based on allocator
            current_strategy_order = strategy_order_lru if allocator == 'LRU' else strategy_order_other
            
            for strategy in current_strategy_order:
                strategy_data = allocator_data[allocator_data['rebalance_strategy'] == strategy]
                
                if not strategy_data.empty:
                    values = strategy_data['miss_ratio_reduction_from_lru_disabled'].values
                    print(f"  {strategy} values: min={values.min():.6f}, max={values.max():.6f}, mean={values.mean():.6f}")
                    
                    # Check for NaN values
                    if np.any(np.isnan(values)):
                        print(f"  WARNING: {strategy} has NaN values!")
                        continue
                    
                    box_data.append(values)
                    box_labels.append(f"{allocator_labels[i]}")
                    box_colors.append(strategy_colors[strategy])
                    positions.append(pos)
                    mean_values.append(values.mean())  # Store mean for triangle marker
                    pos += 1
                    boxes_added += 1
                    print(f"  Added box for {strategy}: {len(values)} values")
                else:
                    print(f"  No data for {strategy}")
            
            print(f"  Total boxes added for {allocator}: {boxes_added}")
            
            # Add larger spacing between allocators
            pos += 0.5  # Increased from 0.25
        
        # Create box plots with tighter spacing - academic style without outliers
        bp = ax.boxplot(box_data, positions=positions, patch_artist=True, 
                       widths=0.8, showfliers=False)  # Hide outliers for clean academic look
        
        # Color the boxes with full saturation (alpha=1)
        for patch, color in zip(bp['boxes'], box_colors):
            patch.set_facecolor(color)
            patch.set_alpha(1)  # Full saturation to match legend
            patch.set_edgecolor('black')
            patch.set_linewidth(1)
        
        # Add inverted triangle markers for mean values with outstanding color
        for i, (pos, mean_val, color) in enumerate(zip(positions, mean_values, box_colors)):
            ax.scatter(pos, mean_val, marker='v', s=110, color='red', 
                      edgecolors='black', linewidth=1.5, zorder=10)
        
        # Style other box plot elements
        for element in ['whiskers', 'fliers', 'medians', 'caps']:
            plt.setp(bp[element], color='black', linewidth=1.2)
        
        # Set x-axis labels - simplified approach
        allocator_positions = []
        allocator_display_labels = []
        
        # Calculate center position for each allocator that has data
        pos_idx = 0
        for i, allocator in enumerate(allocator_order):
            allocator_data = wsr_data[wsr_data['allocator'] == allocator]
            if allocator_data.empty:
                continue
                
            # Find positions for this allocator
            start_pos = pos_idx
            strategy_count = 0
            # Use different strategy order based on allocator
            current_strategy_order = strategy_order_lru if allocator == 'LRU' else strategy_order_other
            
            for strategy in current_strategy_order:
                strategy_data = allocator_data[allocator_data['rebalance_strategy'] == strategy]
                if not strategy_data.empty:
                    strategy_count += 1
                    pos_idx += 1
            
            if strategy_count > 0:
                # Calculate center position for this allocator's boxes
                center_pos = np.mean(positions[start_pos:start_pos + strategy_count])
                allocator_positions.append(center_pos)
                allocator_display_labels.append(allocator_labels[i])
        
        # Set x-axis ticks and labels
        ax.set_xticks(allocator_positions)
        ax.set_xticklabels(allocator_display_labels)
        
        # Customize the plot
        ax.set_xlabel('Eviction Policy')
        ax.set_ylabel('Miss Ratio Reduction\nover LRU + disabled')
        ax.grid(True, alpha=0.3, axis='y')
        
        # Create legend with matching saturation (alpha=1)
        legend_elements = []
        # Use consistent strategy order for legend (include LAMA)
        legend_strategy_order = ["disabled", "tail-age", "eviction-rate", "hits", "lama", "marginal-hits", "marginal-hits-tuned"]
        strategies_in_data = set(wsr_data['rebalance_strategy'].unique())
        
        # Only include strategies that exist in the data
        for strategy in legend_strategy_order:
            if strategy in strategies_in_data:
                legend_elements.append(plt.Rectangle((0,0),1,1, 
                                     facecolor=strategy_colors[strategy], 
                                     alpha=1, edgecolor='black',  # Match box alpha
                                     label=strategy_labels[strategy]))
        
        if legend_elements:
            # Create legend with 2 rows, 3 columns outside the plot area at the top
            legend = ax.legend(handles=legend_elements, 
                              bbox_to_anchor=(0.5, 1.15), loc='center',
                              ncol=3, frameon=True, fancybox=True, shadow=True, 
                              framealpha=0.9, edgecolor='black')
            legend.get_frame().set_facecolor('white')
        
        # Style the plot
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_linewidth(1.2)
        ax.spines['bottom'].set_linewidth(1.2)
        
        # Adjust layout to accommodate legend outside plot area
        plt.tight_layout()
        plt.subplots_adjust(top=0.85)  # Make room for legend at top
        
        # Save to PDF
        output_file = f'twitter_prod_boxplot_wsr_{wsr:.2f}_v2.pdf'
        plt.savefig(output_file, format='pdf', dpi=300, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        
        plt.show()
        print(f"Plot saved to: {output_file}")

# Example usage
if __name__ == "__main__":
    create_twitter_prod_boxplots("../data/end-to-end/report_complete_processed.csv")