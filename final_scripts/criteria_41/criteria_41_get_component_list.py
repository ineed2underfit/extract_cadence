
import pandas as pd
import numpy as np
import argparse
import os

def get_component_list():
    """
    Extracts component information from a Cadence design file.

    Reads the 'SYM_NAME' sheet from an Excel file, filters for specific component
    boundaries and shapes, calculates the center position and dimensions for each
    component, and returns the data as a pandas DataFrame.

    The function handles three types of shapes: RECTANGLE, CIRCLE, and LINE.
    For LINEs, it assumes they form a bounding box for the component.

    Returns:
        pandas.DataFrame: A DataFrame named get_component_list_re with the
                          following columns:
                          - component_id (str): The reference designator.
                          - shape_type (str): The graphical shape name.
                          - x_position (float): The x-coordinate of the center.
                          - y_position (float): The y-coordinate of the center.
                          - dimension (str): The dimensions of the shape.
    """
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        excel_path = os.path.join(script_dir, '..', 'parsed_tables_250804.xlsx')
        if not os.path.exists(excel_path):
             excel_path = os.path.join(os.getcwd(), 'final_scripts', 'parsed_tables_250804.xlsx')
        df = pd.read_excel(excel_path, sheet_name='SYM_NAME')
    except FileNotFoundError:
        print(f"Error: Excel file not found.")
        return pd.DataFrame(columns=['component_id', 'shape_type', 'x_position', 'y_position', 'dimension'])

    for col in ['GRAPHIC_DATA_1', 'GRAPHIC_DATA_2', 'GRAPHIC_DATA_3', 'GRAPHIC_DATA_4']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    subclass_filter = df['SUBCLASS'].isin(['PLACE_BOUND_TOP', 'PLACE_BOUND_BOTTOM'])
    shape_filter = df['GRAPHIC_DATA_NAME'].isin(['LINE', 'RECTANGLE', 'CIRCLE'])
    filtered_df = df[subclass_filter & shape_filter].copy()

    if filtered_df.empty:
        return pd.DataFrame(columns=['component_id', 'shape_type', 'x_position', 'y_position', 'dimension'])

    filtered_df['original_index'] = filtered_df.index
    first_indices = filtered_df.groupby(['REFDES', 'SUBCLASS'])['original_index'].min().reset_index()
    first_indices.rename(columns={'original_index': 'sort_key'}, inplace=True)

    processed_data = []
    for group_keys, group_df in filtered_df.groupby(['REFDES', 'SUBCLASS']):
        refdes, subclass = group_keys
        shape_type = group_df['GRAPHIC_DATA_NAME'].iloc[0]

        x_pos, y_pos, dim = np.nan, np.nan, ''

        try:
            if shape_type == 'RECTANGLE':
                row = group_df.iloc[0]
                x1, y1, x2, y2 = row['GRAPHIC_DATA_1'], row['GRAPHIC_DATA_2'], row['GRAPHIC_DATA_3'], row['GRAPHIC_DATA_4']
                if all(pd.notna([x1, y1, x2, y2])):
                    x_min, x_max = min(x1, x2), max(x1, x2)
                    y_min, y_max = min(y1, y2), max(y1, y2)
                    x_pos = (x_min + x_max) / 2
                    y_pos = (y_min + y_max) / 2
                    width = abs(x_max - x_min)
                    height = abs(y_max - y_min)
                    # **FORMATTING: Round dimension string to 3 decimal places**
                    dim = f"{width:.3f} * {height:.3f}"

            elif shape_type == 'CIRCLE':
                row = group_df.iloc[0]
                x_pos = row['GRAPHIC_DATA_1']
                y_pos = row['GRAPHIC_DATA_2']
                diameter = row['GRAPHIC_DATA_3'] if pd.notna(row['GRAPHIC_DATA_3']) else row['GRAPHIC_DATA_4']
                if pd.notna(diameter):
                    # **FORMATTING: Round dimension string to 3 decimal places**
                    dim = f"{float(diameter):.3f}"
                else:
                    dim = ''

            elif shape_type == 'LINE':
                x_coords = pd.concat([group_df['GRAPHIC_DATA_1'], group_df['GRAPHIC_DATA_3']]).dropna()
                y_coords = pd.concat([group_df['GRAPHIC_DATA_2'], group_df['GRAPHIC_DATA_4']]).dropna()
                if not x_coords.empty and not y_coords.empty:
                    x_min, x_max = x_coords.min(), x_coords.max()
                    y_min, y_max = y_coords.min(), y_coords.max()
                    x_pos = (x_min + x_max) / 2
                    y_pos = (y_min + y_max) / 2
                    width = abs(x_max - x_min)
                    height = abs(y_max - y_min)
                    # **FORMATTING: Round dimension string to 3 decimal places**
                    dim = f"{width:.3f} * {height:.3f}"

        except Exception as e:
            print(f"Could not process group {group_keys}. Error: {e}")
            pass

        processed_data.append({
            'REFDES': refdes,
            'SUBCLASS': subclass,
            'component_id': refdes,
            'shape_type': shape_type,
            'x_position': x_pos,
            'y_position': y_pos,
            'dimension': dim
        })

    if not processed_data:
        return pd.DataFrame(columns=['component_id', 'shape_type', 'x_position', 'y_position', 'dimension'])

    result_df = pd.DataFrame(processed_data)
    result_df = pd.merge(result_df, first_indices, on=['REFDES', 'SUBCLASS'])
    result_df = result_df.sort_values('sort_key').reset_index(drop=True)

    get_component_list_re = result_df[['component_id', 'shape_type', 'x_position', 'y_position', 'dimension']]

    # **FORMATTING: Round position columns to 3 decimal places**
    get_component_list_re['x_position'] = get_component_list_re['x_position'].round(3)
    get_component_list_re['y_position'] = get_component_list_re['y_position'].round(3)
    
    return get_component_list_re

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Extract component list from Cadence data.")
    parser.add_argument(
        '-f', '--full',
        action='store_true',
        help="Print the full DataFrame without truncation."
    )
    args = parser.parse_args()

    if args.full:
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)

    get_component_list_re = get_component_list()
    print(get_component_list_re)
