import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def create_twitter_prod_best_strategy_barplots(csv_file):
    """
    Create stacked bar plots showing the ratio of winning rebalance strategies 
    for Twitter production data grouped by trace and eviction policy.
    """
    
    # Read the CSV file
    df = pd.read_csv(csv_file)
    df = df[(df['trace_name'].str.startswith('twitter')) & (df['tag'] != 'warm-cold')]
    
    # Define all strategies we expect
    all_strategies = ["disabled", "tail-age", "free-mem", "hits", "marginal-hits", "marginal-hits-tuned"]
    
    # Define strategy labels and colors (same as before)
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
        "marginal-hits-tuned": "#2E8B57"
    }
    
    # Define allocator order and labels
    allocator_order = ['LRU', 'LRU2Q', 'TINYLFU']
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
        
        # Filter traces that have all strategies for all allocators
        complete_traces = []
        for trace in wsr_data['trace_name'].unique():
            trace_data = wsr_data[wsr_data['trace_name'] == trace]
            
            # Check if this trace has all strategies for all allocators
            has_all_strategies = True
            for allocator in allocator_order:
                allocator_data = trace_data[trace_data['allocator'] == allocator]
                available_strategies = set(allocator_data['rebalance_strategy'].unique())
                if not set(all_strategies).issubset(available_strategies):
                    has_all_strategies = False
                    break
            
            if has_all_strategies:
                complete_traces.append(trace)
        
        print(f"WSR {wsr}: Found {len(complete_traces)} complete traces out of {len(wsr_data['trace_name'].unique())} total traces")
        
        # Filter to only complete traces
        wsr_data = wsr_data[wsr_data['trace_name'].isin(complete_traces)]
        
        if wsr_data.empty:
            print(f"No complete traces found for WSR = {wsr}")
            continue
        
        # Find best strategy for each trace-allocator combination with tie handling
        best_strategies = []
        total_ties = 0
        
        for trace in complete_traces:
            for allocator in allocator_order:
                trace_alloc_data = wsr_data[(wsr_data['trace_name'] == trace) & 
                                          (wsr_data['allocator'] == allocator)]
                
                if not trace_alloc_data.empty:
                    # Find minimum miss ratio
                    min_miss_ratio = trace_alloc_data['miss_ratio'].min()
                    
                    # Find all strategies that achieved this minimum
                    tied_strategies = trace_alloc_data[trace_alloc_data['miss_ratio'] == min_miss_ratio]['rebalance_strategy'].values
                    
                    # Calculate win weight (1.0 divided among tied strategies)
                    win_weight = 1.0 / len(tied_strategies)
                    
                    # Track ties for statistics
                    if len(tied_strategies) > 1:
                        total_ties += 1
                    
                    # Add fractional wins for each tied strategy
                    for strategy in tied_strategies:
                        best_strategies.append({
                            'trace_name': trace,
                            'allocator': allocator,
                            'best_strategy': strategy,
                            'win_weight': win_weight
                        })
        
        print(f"WSR {wsr}: Found {total_ties} ties out of {len(complete_traces) * len(allocator_order)} total comparisons")
        
        # Convert to DataFrame
        best_df = pd.DataFrame(best_strategies)
        
        # Calculate ratios for each allocator with weighted wins
        ratio_data = []
        positions = []
        
        for i, allocator in enumerate(allocator_order):
            # Filter data for this allocator
            allocator_data = [entry for entry in best_strategies if entry['allocator'] == allocator]
            
            if len(allocator_data) == 0:
                continue
            
            # Calculate total weighted wins for each strategy
            strategy_weights = {}
            for strategy in all_strategies:
                strategy_weights[strategy] = sum(entry['win_weight'] for entry in allocator_data 
                                               if entry['best_strategy'] == strategy)
            
            # Calculate total weight (should equal number of traces for this allocator)
            total_weight = sum(strategy_weights.values())
            
            # Calculate ratios
            ratios = {}
            for strategy in all_strategies:
                ratios[strategy] = strategy_weights[strategy] / total_weight if total_weight > 0 else 0
            
            ratio_data.append(ratios)
            positions.append(i)
        
        # Create figure - slightly wider and shorter layout
        fig, ax = plt.subplots(figsize=(9, 5))
        
        # Create horizontal stacked bars
        left = np.zeros(len(positions))
        
        for strategy in all_strategies:
            if strategy in strategy_colors:
                widths = [ratio_data[i][strategy] for i in range(len(ratio_data))]
                
                # Only plot if there are non-zero values
                if any(w > 0 for w in widths):
                    bars = ax.barh(positions, widths, left=left, 
                                  color=strategy_colors[strategy], 
                                  alpha=1, edgecolor='black', linewidth=0.5,
                                  height=0.6, label=strategy_labels[strategy])  # Narrower bars
                    left += widths
        
        # Add horizontal separator lines
        for i in range(1, len(positions)):
            ax.axhline(y=i - 0.5, color='gray', linestyle='--', alpha=0.5, linewidth=1)
        
        # Customize the plot
        ax.set_ylabel('Eviction Policy')
        ax.set_yticks(positions)
        ax.set_yticklabels([allocator_labels[allocator_order.index(allocator)] 
                           for i, allocator in enumerate(allocator_order) if i in positions])
        ax.set_xlim(0, 1)
        ax.grid(True, alpha=0.3, axis='x')
        
        # Invert y-axis to match reference layout (first allocator at top)
        ax.invert_yaxis()
        
        # Create legend - positioned at top in 2 rows, 3 columns
        legend_elements = []
        for strategy in all_strategies:
            if strategy in strategy_colors:
                legend_elements.append(plt.Rectangle((0,0),1,1, 
                                     facecolor=strategy_colors[strategy], 
                                     alpha=1, edgecolor='black', linewidth=0.5,
                                     label=strategy_labels[strategy]))
        
        if legend_elements:
            legend = ax.legend(handles=legend_elements, 
                              bbox_to_anchor=(0.5, 1.15), loc='center',
                              ncol=3, frameon=True, fancybox=False, shadow=False, 
                              framealpha=1, edgecolor='black', fontsize=16)
            legend.get_frame().set_facecolor('white')
        
        # Style the plot - more compact
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_linewidth(1.2)
        ax.spines['bottom'].set_linewidth(1.2)
        
        # Adjust layout - make room for top legend
        plt.tight_layout()
        plt.subplots_adjust(top=0.85)  # Make room for legend at top
        
        # Save to PDF
        output_file = f'twitter_prod_best_strategy_ratios_wsr_{wsr:.2f}.pdf'
        plt.savefig(output_file, format='pdf', dpi=300, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        
        plt.show()
        print(f"Plot saved to: {output_file}")
        print(f"Used {len(complete_traces)} traces with complete strategy data")
        print(f"Ties handled: {total_ties} cases where multiple strategies tied for best performance")

# Example usage
if __name__ == "__main__":
    create_twitter_prod_best_strategy_barplots("twitter_full_digest.csv")