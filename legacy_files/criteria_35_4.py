
import pandas as pd
import numpy as np
import time
import argparse
import os
import sys
from shapely.geometry import Point, LineString, Polygon
from rtree import index

# --- Pre-computation and Helper Functions ---

# Add the script's directory to the Python path to ensure sibling modules can be imported
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)

try:
    # Import the data-gathering functions from sibling scripts
    from criteria_35_1 import get_test_point_list
    from criteria_35_2 import get_component_pads_info as get_pad_list
except ImportError as e:
    print(f"Fatal Error: Could not import necessary functions.")
    print(f"Details: {e}")
    print("Please ensure 'criteria_35_1.py' and 'criteria_35_2.py' exist in the same directory.")
    sys.exit(1)

# --- Geometry Calculation Functions (Optimized with Shapely) ---

def _create_tp_shape(row):
    """Creates a shapely geometry object from a test point data row based on specified rules."""
    shape_type = row.get('shape_type', 'RECT')
    x, y, width, height = row['x'], row['y'], row['width'], row['height']

    if shape_type == 'CIRCLE':
        return Point(x, y).buffer(width / 2.0, cap_style=1) # cap_style=1 for a round buffer
    elif shape_type == 'LINE':
        return LineString([(x, y), (width, height)]) # width is x2, height is y2
    else: # RECT and other types are treated as rectangles centered at x, y
        half_w, half_h = width / 2.0, height / 2.0
        return Polygon([
            (x - half_w, y - half_h), (x + half_w, y - half_h),
            (x + half_w, y + half_h), (x - half_w, y + half_h)
        ])

def _create_pad_shape(row):
    """Creates a shapely geometry object from a pad/pin data row based on specified rules."""
    shape_type = row.get('PAD_STACK_NAME', 'RECT')
    x, y, width, height = row['x'], row['y'], row['width'], row['height']

    if shape_type == 'CIRCLE':
        return Point(x, y).buffer(width / 2.0, cap_style=1)
    else: # RECT and other types
        half_w, half_h = width / 2.0, height / 2.0
        return Polygon([
            (x - half_w, y - half_h), (x + half_w, y - half_h),
            (x + half_w, y + half_h), (x - half_w, y + half_h)
        ])

def judge_tp_pad_pin_positions():
    """Determines if test points overlap with component pads/pins using spatial indexing for performance."""
    try:
        tp_df = get_test_point_list()
        pad_df = get_pad_list()
    except Exception as e:
        print(f"Error while getting data from source functions: {e}")
        return pd.DataFrame()

    if tp_df.empty or pad_df.empty:
        print("Warning: One or both DataFrames are empty. No analysis performed.")
        return pd.DataFrame(columns=['testpoint_id', 'pad_id', 'distance'])

    # Create shapely objects for pads and build a spatial index
    pad_shapes = [(_create_pad_shape(row), row['component_id']) for _, row in pad_df.iterrows()]
    idx = index.Index()
    for i, (shape, _) in enumerate(pad_shapes):
        idx.insert(i, shape.bounds)

    results = []
    # Iterate through each test point
    for _, tp_row in tp_df.iterrows():
        tp_shape = _create_tp_shape(tp_row)
        tp_id = tp_row['testpoint_id']
        
        # Use the spatial index to find candidate pads that might intersect
        candidate_indices = list(idx.intersection(tp_shape.bounds))
        
        for i in candidate_indices:
            pad_shape, pad_id = pad_shapes[i]
            
            # Perform precise intersection check
            if tp_shape.intersects(pad_shape):
                # Per requirement, distance is negative for overlap
                # We use a fixed -1.0 to signify overlap, as shapely's distance is 0 for intersects.
                results.append({
                    'testpoint_id': tp_id,
                    'pad_id': pad_id,
                    'distance': -1.0
                })

    if not results:
        return pd.DataFrame(columns=['testpoint_id', 'pad_id', 'distance'])

    judge_tp_pad_pin_positions_re = pd.DataFrame(results)
    return judge_tp_pad_pin_positions_re

# --- Script Execution Block ---

if __name__ == '__main__':
    # --- Argument Parsing (imitating criteria_35_3.py) ---
    title = "criteria_35_4 - Judge TP/Pad Position Overlaps"
    parser = argparse.ArgumentParser(description=title)
    parser.add_argument('-f', '--full', action='store_true', help="Full display mode, shows all rows and columns.")
    args = parser.parse_args()

    # --- Main Execution ---
    # To handle potential encoding issues with emojis in Windows terminals
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except TypeError:
        # In some environments (like older Python versions), this might not be available.
        pass

    start_time = time.time()
    result_df = judge_tp_pad_pin_positions()

    # --- Filtering and Printing Results ---
    if result_df is not None:
        # Requirement: Filter out rows where testpoint_id is the same as pad_id
        original_count = len(result_df)
        result_df = result_df[result_df['testpoint_id'] != result_df['pad_id']].copy()
        filtered_count = original_count - len(result_df)

        print("==================================================")
        print(f" {title}")
        if args.full:
            print(" Mode: Full Mode (-f)")
            print("==================================================")
            with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 1000):
                print(result_df)
        else:
            print(" Mode: Default (use -f to show all)")
            print("==================================================")
            print(result_df)

        print("==================================================")
        print(f"Found {len(result_df)} overlaps.")
        if filtered_count > 0:
            print(f"Filtered out {filtered_count} self-overlap records.")

        if result_df.empty and filtered_count == 0:
            print("No overlaps found between different test points and pads.")

    else:
        print("Error: The analysis function did not return a DataFrame.")

    end_time = time.time()
    print(f"Total script runtime: {end_time - start_time:.2f} seconds")
