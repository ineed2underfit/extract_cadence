import pandas as pd
import numpy as np
import time
import argparse
import os
import sys

# --- Pre-computation and Helper Functions ---

# Add the script's directory to the Python path to ensure sibling modules can be imported
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

try:
    # Import the data-gathering functions from sibling scripts
    from criteria_37_2 import get_test_point_list
    from criteria_37_3 import get_component_list
except ImportError as e:
    print(f"Fatal Error: Could not import necessary functions.")
    print(f"Details: {e}")
    print("Please ensure 'criteria_37_2.py' and 'criteria_37_3.py' exist in the criteria_37 directory.")
    sys.exit(1)

# --- Geometry Calculation Functions ---

def _dist_signed_point_to_rect(p, rect_min, rect_max):
    """Calculates the signed distance from a point to an axis-aligned rectangle."""
    p = np.array(p)
    rect_min = np.array(rect_min)
    rect_max = np.array(rect_max)
    
    # Calculate the center and half-size of the rectangle
    rect_center = (rect_min + rect_max) / 2
    rect_half = (rect_max - rect_min) / 2
    
    delta = np.abs(p - rect_center) - rect_half
    
    if delta[0] <= 0 and delta[1] <= 0:
        return np.max(delta)  # Negative distance, indicates penetration
    
    # Clamp negative components to 0 to calculate external distance
    dist_vec = np.maximum(delta, 0)
    return np.linalg.norm(dist_vec)

def _calculate_distance(tp_shape, tp_params, component_shape, component_params):
    """Dispatcher to calculate distance between two geometric shapes."""
    
    # Case 1: Testpoint is a Circle (always according to criteria_37_2.py)
    if tp_shape == 'CIRCLE':
        tp_c, tp_r = tp_params
        if component_shape == 'RECT' or component_shape == 'OTHER':  # Treat all non-LINE shapes as RECT
            component_min, component_max = component_params
            dist_to_center = _dist_signed_point_to_rect(tp_c, component_min, component_max)
            return dist_to_center - tp_r
        elif component_shape == 'LINE':
            # For LINE, we'll simplify by checking distance to the bounding box
            # This is a simplification, but should work for most practical purposes
            component_min, component_max = component_params
            dist_to_center = _dist_signed_point_to_rect(tp_c, component_min, component_max)
            return dist_to_center - tp_r
            
    return float('inf')  # Should not be reached for valid inputs

# --- Main Logic Function ---

def judge_tp_component_coverage():
    """
    Judges the coverage of test points against component boundaries to find overlaps,
    respecting layer constraints.
    """
    try:
        tp_df = get_test_point_list()
        component_df = get_component_list()
    except Exception as e:
        print(f"Error while getting data from source functions: {e}")
        return pd.DataFrame()

    if tp_df.empty or component_df.empty:
        print("Warning: One of the source DataFrames is empty. No analysis performed.")
        return pd.DataFrame(columns=['testpoint_id', 'component_id', 'layer', 'distance'])

    # --- Layer-based Filtering ---
    # Map TP layers to standard layer names
    tp_df['standard_layer'] = tp_df['layer'].map({
        'SOLDERMASK_TOP': 'TOP',
        'SOLDERMASK_BOTTOM': 'BOTTOM'
    })
    
    # Map component layers to standard layer names
    component_df['standard_layer'] = component_df['layer'].map({
        'PLACE_BOUND_TOP': 'TOP',
        'PLACE_BOUND_BOTTOM': 'BOTTOM'
    })
    
    # Filter valid layers
    tp_filtered = tp_df.dropna(subset=['standard_layer'])
    component_filtered = component_df.dropna(subset=['standard_layer'])
    
    tp_top = tp_filtered[tp_filtered['standard_layer'] == 'TOP'].copy()
    tp_bottom = tp_filtered[tp_filtered['standard_layer'] == 'BOTTOM'].copy()
    
    component_top = component_filtered[component_filtered['standard_layer'] == 'TOP'].copy()
    component_bottom = component_filtered[component_filtered['standard_layer'] == 'BOTTOM'].copy()

    results = []
    
    # --- Process TOP and BOTTOM layers separately ---
    for layer_name, tp_layer_df, component_layer_df in [('TOP', tp_top, component_top), ('BOTTOM', tp_bottom, component_bottom)]:
        if tp_layer_df.empty or component_layer_df.empty:
            continue

        for _, tp_row in tp_layer_df.iterrows():
            # Per requirements, testpoints are always circles
            tp_shape = 'CIRCLE'
            # x, y are center coordinates; width is diameter, so radius is width/2
            tp_params = ((tp_row['x'], tp_row['y']), tp_row['width'] / 2)

            for _, component_row in component_layer_df.iterrows():
                # Skip if testpoint_id and component_id are the same
                if tp_row['testpoint_id'] == component_row['component_id']:
                    continue
                    
                component_shape_name = component_row['shape_name']
                
                # Determine component shape based on shape_name
                if component_shape_name == 'LINE':
                    component_shape = 'LINE'
                else:
                    component_shape = 'OTHER'  # Treat as rectangle
                    
                # For component, min_x, max_x, min_y, max_y define the bounding box
                component_params = ((component_row['min_x'], component_row['min_y']), 
                                   (component_row['max_x'], component_row['max_y']))

                distance = _calculate_distance(tp_shape, tp_params, component_shape, component_params)

                # Only include results with overlap (distance < 0)
                if distance < 0:
                    results.append({
                        'testpoint_id': tp_row['testpoint_id'],
                        'component_id': component_row['component_id'],
                        'layer': layer_name,  # Use standard layer name (TOP/BOTTOM)
                        'distance': distance
                    })

    if not results:
        return pd.DataFrame(columns=['testpoint_id', 'component_id', 'layer', 'distance'])

    judge_tp_component_coverage_re = pd.DataFrame(results)
    # Keep the original order, don't sort by index
    return judge_tp_component_coverage_re

# --- Script Execution Block ---

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="查找测试点 (TP) 与元器件边界之间的重叠。")
    parser.add_argument('-f', '--full', action='store_true', help="完整显示所有行和列。")
    args = parser.parse_args()

    start_time = time.time()
    # To handle potential encoding issues with emojis in Windows terminals
    title = "🔍 criteria_37_4 - Judge TP/Component Coverage Overlaps"
    
    result_df = judge_tp_component_coverage()

    if result_df is not None and not result_df.empty:
        print("\n==================================================")
        print(f" {title}")
        if args.full:
            print(" Mode: Full Mode (--full)")
            print("==================================================")
            with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 1000):
                print(result_df)
            print(f"\n[{result_df.shape[0]} rows x {result_df.shape[1]} columns]")
        else:
            print(" Mode: Default (use -f or --full to show all)")
            print("==================================================")
            print(result_df)
            print(f"\n[{result_df.shape[0]} rows x {result_df.shape[1]} columns]")
    elif result_df is not None:
         print("\n==================================================")
         print(f" {title}")
         print("==================================================")
         print("\nNo overlaps found between test points and components.")


    end_time = time.time()
    if result_df is not None:
        print(f"Total script runtime: {end_time - start_time:.2f} seconds\n")