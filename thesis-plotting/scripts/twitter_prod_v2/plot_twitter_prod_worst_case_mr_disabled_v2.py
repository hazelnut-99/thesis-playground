import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def create_twitter_prod_worst_case_mr_barplots(csv_file):
    """
    Create bar plots for Twitter production data showing worst-case miss ratio reduction from disabled.
    """
    
    # Read the CSV file
    df = pd.read_csv(csv_file)
    df = df[(df['trace_name'].str.startswith('twitter')) & (df['tag'] != 'warm-cold') & df['miss_ratio_reduction_from_disabled'].notna()]
    df = df[df['rebalance_strategy'] != 'disabled']
    # Define strategy labels and colors
    strategy_labels = {
        #"disabled": r"$\mathit{Disabled}$",
        "tail-age": r"$\mathit{Tail\text{-}Age}$",
        "eviction-rate": r"$\mathit{Eviction\text{-}Rate}$",
        "hits": r"$\mathit{Hits\text{-}Per\text{-}Slab}$",
        "lama": r"$\mathit{LAMA}$",
        "marginal-hits": r"$\mathit{Marginal\text{-}Hits}$",
        "marginal-hits-tuned": r"$\mathit{Marginal\text{-}Hits\text{-}Tuned}$"
    }
    
    strategy_colors = {
        #"disabled": "#636EFA",
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
        
        # Prepare data for bar plots
        bar_data = []
        bar_labels = []
        bar_colors = []
        positions = []
        
        pos = 0
        # LAMA only exists for LRU, other strategies for all allocators
        strategy_order_lru = list(strategy_labels.keys())
        strategy_order_other = [s for s in strategy_labels.keys() if s != 'lama']
        
        for i, allocator in enumerate(allocator_order):
            allocator_data = wsr_data[wsr_data['allocator'] == allocator]
            
            if allocator_data.empty:
                print(f"WSR {wsr}: No data for {allocator}")
                continue
            
            print(f"WSR {wsr}, {allocator}: {len(allocator_data)} rows, strategies: {list(allocator_data['rebalance_strategy'].unique())}")
            
            # Add vertical separator line (except before first allocator)
            if i > 0:
                ax.axvline(x=pos - 0.5, color='gray', linestyle='--', alpha=0.5, linewidth=1)
            
            bars_added = 0
            # Use different strategy order based on allocator
            current_strategy_order = strategy_order_lru if allocator == 'LRU' else strategy_order_other
            for strategy in current_strategy_order:
                strategy_data = allocator_data[allocator_data['rebalance_strategy'] == strategy]
                
                if not strategy_data.empty:
                    values = strategy_data['miss_ratio_reduction_from_disabled'].values
                    
                    # Check for NaN values
                    if np.any(np.isnan(values)):
                        print(f"  WARNING: {strategy} has NaN values!")
                        continue
                    
                    # Calculate worst case (minimum value, which is most negative = worst performance)
                    worst_case = values.min()
                    
                    print(f"  {strategy}: worst case miss ratio reduction = {worst_case:.6f}")
                    
                    bar_data.append(worst_case)
                    bar_labels.append(f"{allocator_labels[i]}")
                    bar_colors.append(strategy_colors[strategy])
                    positions.append(pos)
                    pos += 1
                    bars_added += 1
                    print(f"  Added bar for {strategy}")
                else:
                    print(f"  No data for {strategy}")
            
            print(f"  Total bars added for {allocator}: {bars_added}")
            
            # Add larger spacing between allocators
            pos += 0.5
        
        # Create bar plots
        bars = ax.bar(positions, bar_data, color=bar_colors, alpha=1, 
                     edgecolor='black', linewidth=1, width=0.8)
        
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
            current_strategy_order = strategy_order_lru if allocator == 'LRU' else strategy_order_other
            for strategy in current_strategy_order:
                strategy_data = allocator_data[allocator_data['rebalance_strategy'] == strategy]
                if not strategy_data.empty:
                    strategy_count += 1
                    pos_idx += 1
            
            if strategy_count > 0:
                # Calculate center position for this allocator's bars
                center_pos = np.mean(positions[start_pos:start_pos + strategy_count])
                allocator_positions.append(center_pos)
                allocator_display_labels.append(allocator_labels[i])
        
        # Set x-axis ticks and labels
        ax.set_xticks(allocator_positions)
        ax.set_xticklabels(allocator_display_labels)
        
        # Customize the plot
        ax.set_xlabel('Eviction Policy')
        ax.set_ylabel('Worst-Case Miss Ratio Reduction\nover Disabled')
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add a horizontal line at y=0 for reference
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.3, linewidth=1)
        
        # Create legend with matching saturation (alpha=1)
        legend_elements = []
        legend_strategy_order = list(strategy_labels.keys())
        for strategy in legend_strategy_order:
            if strategy in wsr_data['rebalance_strategy'].values:
                legend_elements.append(plt.Rectangle((0,0),1,1, 
                                     facecolor=strategy_colors[strategy], 
                                     alpha=1, edgecolor='black',
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
        output_file = f'twitter_prod_worst_case_mr_reduction_disabled_wsr_{wsr:.2f}.pdf'
        plt.savefig(output_file, format='pdf', dpi=300, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        
        plt.show()
        print(f"Plot saved to: {output_file}")

# Example usage
if __name__ == "__main__":
    create_twitter_prod_worst_case_mr_barplots("../data/end-to-end/report_complete_processed.csv")
