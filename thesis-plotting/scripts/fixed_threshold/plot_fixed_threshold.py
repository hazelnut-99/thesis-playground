import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

# Set up matplotlib for publication quality
mpl.rcParams.update({
    "font.size": 18,
    "axes.titlesize": 20,
    "axes.labelsize": 18,
    "legend.fontsize": 15,
    "xtick.labelsize": 15,
    "ytick.labelsize": 15,
    "figure.titlesize": 25,
    "figure.dpi": 300,
})

def load_and_filter_data():
    """Load both CSV files and filter for meta_202210_kv trace"""
    # Load adaptive threshold data (report_complete_processed.csv)
    adaptive_df = pd.read_csv('../data/end-to-end/report_complete_processed.csv')
    adaptive_filtered = adaptive_df[
        (adaptive_df['trace_name'] == 'meta_202210_kv') & 
        (adaptive_df['rebalance_strategy'] == 'marginal-hits')
    ].copy()
    adaptive_filtered['threshold_type'] = 'Adaptive'
    adaptive_filtered['threshold_value'] = 'Adaptive'
    
    # Load fixed threshold data (report_fixed_thresh_processed.csv)
    fixed_df = pd.read_csv('../data/end-to-end/report_fixed_thresh_processed.csv')
    fixed_filtered = fixed_df[
        (fixed_df['trace_name'] == 'meta_202210_kv') & 
        (fixed_df['rebalance_strategy'] == 'marginal-hits-tuned')
    ].copy()
    fixed_filtered['threshold_type'] = 'Fixed'
    fixed_filtered['threshold_value'] = fixed_filtered['mhMinDiff'].astype(str)
    
    # Combine both datasets
    combined_df = pd.concat([adaptive_filtered, fixed_filtered], ignore_index=True)
    
    return combined_df

def create_threshold_comparison_plots():
    """Create bar plots comparing adaptive and fixed thresholds for different WSR values"""
    df = load_and_filter_data()
    
    # Get unique allocators and WSR values
    allocators = sorted(df['allocator'].unique())
    wsr_values = sorted(df['wsr'].unique())
    
    # Better color scheme with adaptive being distinct
    adaptive_color = '#E74C3C'  # Red for adaptive - distinct and prominent
    
    # Generate distinct colors for fixed thresholds using a better palette
    fixed_thresholds = sorted([int(x) for x in df[df['threshold_type'] == 'Fixed']['threshold_value'].unique()])
    n_fixed = len(fixed_thresholds)
    
    # Use distinct colors that are easily distinguishable
    fixed_colors = [
        '#3498DB',  # Blue
        '#2ECC71',  # Green
        '#F39C12',  # Orange
        '#9B59B6',  # Purple
        '#1ABC9C',  # Teal
        '#34495E',  # Dark gray
        '#E67E22',  # Dark orange
        '#95A5A6',  # Light gray
        '#8E44AD'   # Dark purple
    ]
    # Repeat colors if we have more thresholds than colors
    fixed_colors = fixed_colors * ((n_fixed // len(fixed_colors)) + 1)
    
    # Create individual plots for each WSR value
    for wsr_idx, wsr in enumerate(wsr_values):
        fig, ax = plt.subplots(1, 1, figsize=(10, 6))
        
        # Filter data for this WSR
        wsr_data = df[df['wsr'] == wsr].copy()
        
        # Prepare data for bar plot
        x_positions = np.arange(len(allocators))
        bar_width = 0.8 / (1 + n_fixed)  # Adaptive + fixed thresholds
        
        # Plot adaptive threshold bars
        adaptive_values = []
        for allocator in allocators:
            adaptive_data = wsr_data[
                (wsr_data['allocator'] == allocator) & 
                (wsr_data['threshold_type'] == 'Adaptive')
            ]
            if not adaptive_data.empty:
                adaptive_values.append(adaptive_data['miss_ratio'].iloc[0])
            else:
                adaptive_values.append(0)
        
        ax.bar(x_positions, adaptive_values, bar_width, 
               label='Adaptive', color=adaptive_color, alpha=0.9, edgecolor='black', linewidth=0.5)
        
        # Plot fixed threshold bars
        for i, threshold in enumerate(fixed_thresholds):
            fixed_values = []
            for allocator in allocators:
                fixed_data = wsr_data[
                    (wsr_data['allocator'] == allocator) & 
                    (wsr_data['threshold_type'] == 'Fixed') &
                    (wsr_data['threshold_value'] == str(threshold))
                ]
                if not fixed_data.empty:
                    fixed_values.append(fixed_data['miss_ratio'].iloc[0])
                else:
                    fixed_values.append(0)
            
            offset = (i + 1) * bar_width
            ax.bar(x_positions + offset, fixed_values, bar_width,
                   label=f'Fixed: {threshold}', color=fixed_colors[i], alpha=0.8, 
                   edgecolor='black', linewidth=0.5)
        
        # Formatting
        ax.set_xlabel('Allocator')
        ax.set_ylabel('Miss Ratio')
        ax.set_title(f'Threshold Comparison (WSR = {wsr:.4f})')
        ax.set_xticks(x_positions + bar_width * n_fixed / 2)
        ax.set_xticklabels(allocators)
        ax.grid(True, alpha=0.3, axis='y')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        plt.tight_layout()
        
        # Save individual plot
        output_path = f'fixed_threshold_wsr_{wsr:.4f}.pdf'
        plt.savefig(output_path, bbox_inches='tight')
        plt.close()
        
        print(f"Plot saved to: {output_path}")
    
    print(f"\nCreated {len(wsr_values)} individual plots, one for each WSR value.")
    
    # Print summary statistics
    print("\n=== Data Summary ===")
    print(f"Total data points: {len(df)}")
    print(f"Allocators: {allocators}")
    print(f"WSR values: {wsr_values}")
    print(f"Fixed thresholds: {fixed_thresholds}")
    print(f"Miss ratio range: {df['miss_ratio'].min():.4f} - {df['miss_ratio'].max():.4f}")

if __name__ == "__main__":
    create_threshold_comparison_plots()