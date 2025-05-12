import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pandas as pd

from data_collection.viz_util import InteractiveLineChart

report_path = "outcome/report.csv"

df = pd.read_csv(report_path)
numeric_cols = [col for col in df.columns if col.startswith('_')]
x_axis_cols = ['ws_ratio']
categorical_columns = ['allocFactor', 'poolRebalanceIntervalSec', 'rebalanceStrategy', 'trace_name', 'allocator', 'moveOnSlabRelease']

chart = InteractiveLineChart('Strategy-independent Parameters', report_path, 
                             numeric_cols, categorical_columns, x_axis_cols)
chart.run()
