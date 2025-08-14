
import pandas as pd
import numpy as np
import time
import argparse
import os
import sys

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

# --- Geometry Calculation Functions ---

def _dist_point_to_segment(p, a, b):
    """Calculates the minimum distance from a point p to a line segment [a, b]."""
    p, a, b = np.array(p), np.array(a), np.array(b)
    if np.array_equal(a, b):
        return np.linalg.norm(p - a)
    
    seg_vec = b - a
    p_vec = p - a
    seg_len_sq = np.dot(seg_vec, seg_vec)
    
    t = np.dot(p_vec, seg_vec) / seg_len_sq
    t = np.clip(t, 0, 1)
    
    closest_point = a + t * seg_vec
    return np.linalg.norm(p - closest_point)

def _dist_signed_point_to_rect(p, rect_center, rect_w, rect_h):
    """Calculates the signed distance from a point to an axis-aligned rectangle."""
    p, rect_center = np.array(p), np.array(rect_center)
    half_w, half_h = rect_w / 2, rect_h / 2
    
    delta = np.abs(p - rect_center) - np.array([half_w, half_h])
    
    if delta[0] <= 0 and delta[1] <= 0:
        return np.max(delta)  # Negative distance, indicates penetration
    
    # Clamp negative components to 0 to calculate external distance
    dist_vec = np.maximum(delta, 0)
    return np.linalg.norm(dist_vec)

def _calculate_distance(tp_shape, tp_params, pad_shape, pad_params):
    """Dispatcher to calculate distance between two geometric shapes."""
    
    # Case 1: Testpoint is a Rectangle
    if tp_shape == 'RECT':
        tp_c, tp_w, tp_h = tp_params
        if pad_shape == 'RECT':
            pad_c, pad_w, pad_h = pad_params
            dx = abs(tp_c[0] - pad_c[0])
            dy = abs(tp_c[1] - pad_c[1])
            gap_x = dx - (tp_w / 2 + pad_w / 2)
            gap_y = dy - (tp_h / 2 + pad_h / 2)
            if gap_x <= 0 and gap_y <= 0: return max(gap_x, gap_y)
            if gap_x > 0 and gap_y <= 0: return gap_x
            if gap_x <= 0 and gap_y > 0: return gap_y
            return np.sqrt(gap_x**2 + gap_y**2)
        
        elif pad_shape == 'CIRCLE':
            pad_c, pad_r = pad_params
            dist_to_center = _dist_signed_point_to_rect(pad_c, tp_c, tp_w, tp_h)
            return dist_to_center - pad_r

    # Case 2: Testpoint is a Circle
    elif tp_shape == 'CIRCLE':
        tp_c, tp_r = tp_params
        if pad_shape == 'RECT':
            pad_c, pad_w, pad_h = pad_params
            dist_to_center = _dist_signed_point_to_rect(tp_c, pad_c, pad_w, pad_h)
            return dist_to_center - tp_r
        
        elif pad_shape == 'CIRCLE':
            pad_c, pad_r = pad_params
            return np.linalg.norm(np.array(tp_c) - np.array(pad_c)) - (tp_r + pad_r)

    # Case 3: Testpoint is a Line
    elif tp_shape == 'LINE':
        tp_a, tp_b = tp_params
        if pad_shape == 'RECT':
            pad_c, pad_w, pad_h = pad_params
            dist_a = _dist_signed_point_to_rect(tp_a, pad_c, pad_w, pad_h)
            dist_b = _dist_signed_point_to_rect(tp_b, pad_c, pad_w, pad_h)
            if min(dist_a, dist_b) < 0: return min(dist_a, dist_b)
            
            rc1 = pad_c + np.array([-pad_w/2, -pad_h/2])
            rc2 = pad_c + np.array([+pad_w/2, -pad_h/2])
            rc3 = pad_c + np.array([+pad_w/2, +pad_h/2])
            rc4 = pad_c + np.array([-pad_w/2, +pad_h/2])
            
            dist_c1 = _dist_point_to_segment(rc1, tp_a, tp_b)
            dist_c2 = _dist_point_to_segment(rc2, tp_a, tp_b)
            dist_c3 = _dist_point_to_segment(rc3, tp_a, tp_b)
            dist_c4 = _dist_point_to_segment(rc4, tp_a, tp_b)
            return min(dist_a, dist_b, dist_c1, dist_c2, dist_c3, dist_c4)

        elif pad_shape == 'CIRCLE':
            pad_c, pad_r = pad_params
            dist_center_to_seg = _dist_point_to_segment(pad_c, tp_a, tp_b)
            return dist_center_to_seg - pad_r
            
    return float('inf') # Should not be reached

# --- Main Logic Function ---

def judge_tp_pad_pin_positions():
    """
    Judges the position of test points against component pads to find overlaps,
    respecting layer constraints.
    """
    try:
        tp_df = get_test_point_list()
        pad_df = get_pad_list()
    except Exception as e:
        print(f"Error while getting data from source functions: {e}")
        return pd.DataFrame()

    if tp_df.empty or pad_df.empty:
        print("Warning: One of the source DataFrames is empty. No analysis performed.")
        return pd.DataFrame(columns=['testpoint_id', 'pad_id', 'layer', 'distance'])

    # --- Layer-based Filtering ---
    tp_top = tp_df[tp_df['layer'] == 'SOLDERMASK_TOP'].copy()
    tp_bottom = tp_df[tp_df['layer'] == 'SOLDERMASK_BOTTOM'].copy()
    
    pad_top = pad_df[pad_df['layer'] == 'TOP'].copy()
    pad_bottom = pad_df[pad_df['layer'] == 'BOTTOM'].copy()

    results = []
    
    # --- Process TOP and BOTTOM layers separately ---
    for layer_name, tp_layer_df, pad_layer_df in [('TOP', tp_top, pad_top), ('BOTTOM', tp_bottom, pad_bottom)]:
        if tp_layer_df.empty or pad_layer_df.empty:
            continue

        for _, tp_row in tp_layer_df.iterrows():
            # Per requirements, testpoints are always circles
            tp_shape = 'CIRCLE'
            tp_params = ((tp_row['x'], tp_row['y']), tp_row['width'] / 2) # width is diameter

            for _, pad_row in pad_layer_df.iterrows():
                pad_shape_name = pad_row['PAD_SHAPE_NAME']
                
                # Determine pad shape based on PAD_SHAPE_NAME
                if pad_shape_name == 'CIRCLE':
                    pad_shape = 'CIRCLE'
                    pad_params = ((pad_row['x'], pad_row['y']), pad_row['width'] / 2)
                elif pad_shape_name == 'FIG_SHAPE SHAPE1_5X2_4':
                    pad_shape = 'LINE'
                    pad_params = ((pad_row['x'], pad_row['y']), (pad_row['width'], pad_row['height']))
                else:
                    pad_shape = 'RECT'
                    pad_params = ((pad_row['x'], pad_row['y']), pad_row['width'], pad_row['height'])

                distance = _calculate_distance(tp_shape, tp_params, pad_shape, pad_params)

                if distance < 0:
                    results.append({
                        'testpoint_id': tp_row['testpoint_id'],
                        'pad_id': pad_row['pad_id'],
                        'layer': layer_name,
                        'distance': distance
                    })

    if not results:
        return pd.DataFrame(columns=['testpoint_id', 'pad_id', 'layer', 'distance'])

    judge_tp_pad_pin_positions_re = pd.DataFrame(results)
    return judge_tp_pad_pin_positions_re

# --- Script Execution Block ---

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="查找测试点 (TP) 与元器件焊盘 (Pad) 之间的重叠。  ")
    parser.add_argument('-f', '--full', action='store_true', help="完整显示所有行和列。")
    args = parser.parse_args()

    start_time = time.time()
    # To handle potential encoding issues with emojis in Windows terminals
    title = "criteria_35_4 - 测试点、元器件覆盖性判断"
    
    result_df = judge_tp_pad_pin_positions()

    if result_df is not None and not result_df.empty:
        print("==================================================")
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
    elif result_df is not None:
         print("==================================================")
         print(f" {title}")
         print("==================================================")
         print("\nNo overlaps found between test points and pads.\n")


    end_time = time.time()
    if result_df is not None:
        print(f"Total script runtime: {end_time - start_time:.2f} seconds\n")
