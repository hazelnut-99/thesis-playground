
import os, sys
import re
import numpy as np
import matplotlib.pyplot as plt
import copy
import numpy.ma as ma
from matplotlib.ticker import FuncFormatter

from typing import List, Dict, Tuple


clusters = ["cluster50", "cluster19", "cluster2", "cluster20"]
file_paths = {
    cluster: f"/mydata/hongshu/thesis-playground/bash/outcome/{cluster}.oracleGeneral.zst.sizeWindow_w300_req"
    for cluster in clusters
}

def _load_size_heatmap_data(datapath) -> Tuple[np.ndarray, int, float, int]:
    """load size heatmap plot data from C++ computation

    Args:
        datapath (str): the path of size heatmap data file

    Returns:
        Tuple[np.ndarray, int, float, int]: plot_data, time_window, log_base, size_base

    """

    ifile = open(datapath)
    data_line = ifile.readline()
    desc_line = ifile.readline()
    m = re.search(
        r"# (object_size): \w\w\w_cnt \(time window (?P<tw>\d+), log_base (?P<logb>\d+\.?\d*), size_base (?P<sizeb>\d+)\)",
        desc_line,
    )
    assert m is not None, (
        "the input file might not be size heatmap data file, desc line "
        + desc_line
        + " data "
        + datapath
    )

    time_window = int(m.group("tw"))
    log_base = float(m.group("logb"))
    size_base = int(m.group("sizeb"))
    size_distribution_over_time = []

    for line in ifile:
        # if "obj_cnt" in line:
        #     curr_data = size_distribution_by_obj_over_time
        # elif not line.strip():
        #     continue
        # else:
        count_list = line.strip("\n,").split(",")
        size_distribution_over_time.append(count_list)

    ifile.close()

    dim = max([len(l) for l in size_distribution_over_time])
    plot_data = np.zeros((len(size_distribution_over_time), dim))

    for idx, l in enumerate(size_distribution_over_time):
        l = np.array(l, dtype=np.float64)
        l = l / np.sum(l)
        plot_data[idx][: len(l)] = l

    return plot_data.T, time_window, log_base, size_base

def plot_all_clusters(clusters: List[str], output_file: str):
    """
    Plot heatmaps for all clusters in a 2x2 grid with labels (a), (b), (c), (d) and save to a file.

    Args:
        clusters (List[str]): List of cluster names.
        output_file (str): Path to save the output plot.
    """
    # Adjust figure size to make plots slightly smaller
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))  # Reduced figure size
    labels = ['(a)', '(b)', '(c)', '(d)']

    # Increase font size globally
    plt.rcParams.update({'font.size': 14})  # Set global font size to 14

    for idx, cluster in enumerate(clusters):
        ax = axes[idx // 2, idx % 2]
        file_path = file_paths[cluster]
        plot_data, time_window, log_base, size_base = _load_size_heatmap_data(file_path)

        # Plot heatmap
        cmap = copy.copy(plt.cm.jet)
        cmap.set_bad(color="white", alpha=1.0)
        img = ax.imshow(plot_data, origin="lower", cmap=cmap, aspect="auto")

        # Add colorbar
        cb = fig.colorbar(img, ax=ax, orientation="vertical")
        

        # Format axes
        ax.xaxis.set_major_formatter(
            FuncFormatter(lambda x, pos: "{:.0f}".format(x * time_window / 3600))
        )
        ax.yaxis.set_major_formatter(
            FuncFormatter(lambda x, pos: "{:.0f}".format(log_base**x * size_base))
        )
        ax.set_xlabel("Time (hour)", fontsize=14)  # Adjust x-axis label font size
        ax.set_ylabel("Request size (Byte)", fontsize=14)  # Adjust y-axis label font size

        # Add subplot label
        ax.text(
            -0.1, 1.1, labels[idx], transform=ax.transAxes, fontsize=16, fontweight="bold", va="top"
        )

        

    plt.tight_layout()
    plt.savefig(output_file, dpi=300)  # Save the plot to a file
    plt.close(fig)  # Close the figure to free memory

# Call the function to plot all clusters and save to a file
output_file = "../figures/obj_size_heatmap.pdf"
plot_all_clusters(clusters, output_file)