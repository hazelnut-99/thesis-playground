import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def create_twitter_prod_impact_plots(csv_file):
    """
    Create stacked bar plots showing the impact distribution of rebalance strategies.
    Each bar shows the percentage of cases with positive vs negative miss ratio reduction.
    """
    
    # Read the CSV file
    df = pd.read_csv(csv_file)
    df = df[(df['trace_name'].str.startswith('twitter')) & (df['tag'] != 'warm-cold') & 
            (df['rebalance_strategy'] != 'lama') & (df['rebalance_strategy'] != 'disabled') & 
            df['miss_ratio_reduction_from_disabled'].notna()]
    
    # Define strategy labels and colors (same as boxplot)
    strategy_labels = {
        "tail-age": r"$\mathit{Tail\text{-}Age}$",
        "eviction-rate": r"$\mathit{Eviction\text{-}Rate}$",
        "hits": r"$\mathit{Hits\text{-}Per\text{-}Slab}$",
        "marginal-hits": r"$\mathit{Marginal\text{-}Hits}$",
        "marginal-hits-tuned": r"$\mathit{Marginal\text{-}Hits\text{-}Tuned}$"
    }
    
    strategy_colors = {
        "tail-age": "#AB63FA", 
        "eviction-rate": "#FFA15A",
        "hits": "#00CC96",
        "marginal-hits": "#EF553B",
        "marginal-hits-tuned": "#2E8B57"
    }
    
    # Define allocator order and labels
    allocator_order = ['LRU', 'LRU2Q', 'TINYLFU']
    allocator_labels = ['LRU', 'TwoQ', 'TinyLFU']
    
    # Set up matplotlib for publication quality (same as boxplot)
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
    
    # Create plots for both WSR values
    wsr_values = [0.1, 0.01]
    
    for wsr in wsr_values:
        # Filter data for current WSR
        wsr_data = df[df['wsr'] == wsr].copy()
        
        if wsr_data.empty:
            print(f"No data found for WSR = {wsr}")
            continue
        
        # Create figure
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Prepare data for stacked bars
        bar_data = []
        bar_labels = []
        bar_colors = []
        positions = []
        
        pos = 0
        strategy_order = ["tail-age", "eviction-rate", "hits", "marginal-hits", "marginal-hits-tuned"]
        
        for i, allocator in enumerate(allocator_order):
            allocator_data = wsr_data[wsr_data['allocator'] == allocator]
            
            if allocator_data.empty:
                print(f"WSR {wsr}: No data for {allocator}")
                continue
            
            # Add vertical separator line (except before first allocator)
            if i > 0:
                ax.axvline(x=pos - 0.5, color='gray', linestyle='--', alpha=0.5, linewidth=1)
            
            bars_added = 0
            for strategy in strategy_order:
                strategy_data = allocator_data[allocator_data['rebalance_strategy'] == strategy]
                
                if not strategy_data.empty:
                    values = strategy_data['miss_ratio_reduction_from_disabled'].values
                    
                    # Calculate percentages
                    total_count = len(values)
                    positive_count = np.sum(values >= 0)
                    negative_count = total_count - positive_count
                    
                    positive_pct = (positive_count / total_count) * 100
                    negative_pct = (negative_count / total_count) * 100
                    
                    print(f"WSR {wsr}, {allocator}, {strategy}: {positive_pct:.1f}% positive, {negative_pct:.1f}% negative")
                    
                    # Store data for this bar
                    bar_data.append((positive_pct, negative_pct))
                    bar_labels.append(f"{allocator_labels[i]}")
                    bar_colors.append(strategy_colors[strategy])
                    positions.append(pos)
                    pos += 1
                    bars_added += 1
            
            # Add spacing between allocators
            pos += 0.5
        
        # Create stacked bars
        if bar_data:
            positive_data = [data[0] for data in bar_data]
            negative_data = [data[1] for data in bar_data]
            
            # Create stacked bars
            bars_positive = ax.bar(positions, positive_data, width=0.8, 
                                 color=bar_colors, alpha=1, edgecolor='black', 
                                 linewidth=1, label='Improvement')
            
            bars_negative = ax.bar(positions, negative_data, width=0.8, 
                                 bottom=positive_data, color=bar_colors, alpha=1, 
                                 edgecolor='black', linewidth=1, hatch='///', 
                                 label='Degradation')
        
        # Set x-axis labels (same logic as boxplot)
        allocator_positions = []
        allocator_display_labels = []
        
        pos_idx = 0
        for i, allocator in enumerate(allocator_order):
            allocator_data = wsr_data[wsr_data['allocator'] == allocator]
            if allocator_data.empty:
                continue
                
            start_pos = pos_idx
            strategy_count = 0
            for strategy in strategy_order:
                strategy_data = allocator_data[allocator_data['rebalance_strategy'] == strategy]
                if not strategy_data.empty:
                    strategy_count += 1
                    pos_idx += 1
            
            if strategy_count > 0:
                center_pos = np.mean(positions[start_pos:start_pos + strategy_count])
                allocator_positions.append(center_pos)
                allocator_display_labels.append(allocator_labels[i])
        
        # Set x-axis ticks and labels
        ax.set_xticks(allocator_positions)
        ax.set_xticklabels(allocator_display_labels)
        
        # Customize the plot
        ax.set_xlabel('Eviction Policy')
        ax.set_ylabel('Performance Impact Distribution (%)')
        ax.set_ylim(0, 100)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Create legend with strategy colors and impact patterns
        legend_elements = []
        strategies_in_data = set(wsr_data['rebalance_strategy'].unique())
        
        # Add strategy color legend
        for strategy in strategy_order:
            if strategy in strategies_in_data:
                legend_elements.append(plt.Rectangle((0,0),1,1, 
                                     facecolor=strategy_colors[strategy], 
                                     alpha=1, edgecolor='black',
                                     label=strategy_labels[strategy]))
        
        # Add separator and impact pattern legend
        if legend_elements:
            # Add strategy legend first
            legend1 = ax.legend(handles=legend_elements, 
                              bbox_to_anchor=(0.5, 1.25), loc='center',
                              ncol=3, frameon=True, fancybox=True, shadow=True, 
                              framealpha=0.9, edgecolor='black', title='Rebalance Strategy')
            legend1.get_frame().set_facecolor('white')
            
            # Add impact pattern legend
            impact_elements = [
                plt.Rectangle((0,0),1,1, facecolor='gray', alpha=1, edgecolor='black', 
                            label='Improvement (≥0%)'),
                plt.Rectangle((0,0),1,1, facecolor='gray', alpha=1, edgecolor='black', 
                            hatch='///', label='Degradation (<0%)')
            ]
            
            legend2 = ax.legend(handles=impact_elements, 
                              bbox_to_anchor=(0.5, 1.15), loc='center',
                              ncol=2, frameon=True, fancybox=True, shadow=True, 
                              framealpha=0.9, edgecolor='black', title='Impact Type')
            legend2.get_frame().set_facecolor('white')
            
            # Add the first legend back
            ax.add_artist(legend1)
        
        # Style the plot
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_linewidth(1.2)
        ax.spines['bottom'].set_linewidth(1.2)
        
        # Adjust layout to accommodate legends
        plt.tight_layout()
        plt.subplots_adjust(top=0.8)  # Make room for legends at top
        
        # Save to PDF
        output_file = f'twitter_prod_impact_wsr_{wsr:.2f}.pdf'
        plt.savefig(output_file, format='pdf', dpi=300, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        
        plt.show()
        print(f"Plot saved to: {output_file}")

# Example usage
if __name__ == "__main__":
    create_twitter_prod_impact_plots("../data/end-to-end/report_complete_processed.csv")