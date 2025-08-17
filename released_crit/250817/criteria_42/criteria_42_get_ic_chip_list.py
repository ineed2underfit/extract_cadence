
import pandas as pd
import numpy as np
import argparse
import time
import os

def get_ic_chip_list():
    """
    从 Excel 文件中提取 IC 芯片及其引脚信息，并计算芯片中心坐标。
    """
    # 1. 构建 Excel 文件的绝对路径
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        excel_file_path = os.path.join(os.path.dirname(script_dir), 'parsed_tables_250804.xlsx')
    except NameError:
        excel_file_path = r'E:\\pycharm_projects\\testability_projects\\extract_cadence\\final_scripts\\parsed_tables_250804.xlsx'

    # 2. 读取 Excel 数据
    try:
        df = pd.read_excel(excel_file_path, sheet_name='SYM_NAME', engine='openpyxl')
    except FileNotFoundError:
        print(f"错误: 未找到 '{excel_file_path}' 文件。")
        return pd.DataFrame()
    except Exception as e:
        print(f"读取 Excel 文件时发生错误: {e}")
        return pd.DataFrame()

    # --- 步骤 A: 计算 IC 芯片的中心坐标 ---
    coord_filter = (
        df['REFDES'].str.startswith('U', na=False) &
        df['GRAPHIC_DATA_NAME'].isin(['RECTANGLE', 'LINE']) &
        df['SUBCLASS'].isin(['PLACE_BOUND_TOP', 'PLACE_BOUND_BOTTOM'])
    )
    coord_df = df[coord_filter].copy()

    coords_cal_df = pd.DataFrame()
    if not coord_df.empty:
        coord_cols = ['GRAPHIC_DATA_1', 'GRAPHIC_DATA_2', 'GRAPHIC_DATA_3', 'GRAPHIC_DATA_4']
        for col in coord_cols:
            coord_df[col] = pd.to_numeric(coord_df[col], errors='coerce')

        rect_df = coord_df[coord_df['GRAPHIC_DATA_NAME'] == 'RECTANGLE'].copy()
        line_df = coord_df[coord_df['GRAPHIC_DATA_NAME'] == 'LINE'].copy()
        processed_coords = []

        if not rect_df.empty:
            rect_df['x_min'] = np.minimum(rect_df['GRAPHIC_DATA_1'], rect_df['GRAPHIC_DATA_3'])
            rect_df['x_max'] = np.maximum(rect_df['GRAPHIC_DATA_1'], rect_df['GRAPHIC_DATA_3'])
            rect_df['y_min'] = np.minimum(rect_df['GRAPHIC_DATA_2'], rect_df['GRAPHIC_DATA_4'])
            rect_df['y_max'] = np.maximum(rect_df['GRAPHIC_DATA_2'], rect_df['GRAPHIC_DATA_4'])
            processed_coords.append(rect_df[['REFDES', 'x_min', 'y_min', 'x_max', 'y_max']])

        if not line_df.empty:
            x_coords = pd.concat([line_df[['REFDES', 'GRAPHIC_DATA_1']].rename(columns={'GRAPHIC_DATA_1': 'x'}), line_df[['REFDES', 'GRAPHIC_DATA_3']].rename(columns={'GRAPHIC_DATA_3': 'x'})])
            y_coords = pd.concat([line_df[['REFDES', 'GRAPHIC_DATA_2']].rename(columns={'GRAPHIC_DATA_2': 'y'}), line_df[['REFDES', 'GRAPHIC_DATA_4']].rename(columns={'GRAPHIC_DATA_4': 'y'})])
            x_bounds = x_coords.groupby('REFDES')['x'].agg(['min', 'max']).rename(columns={'min': 'x_min', 'max': 'x_max'})
            y_bounds = y_coords.groupby('REFDES')['y'].agg(['min', 'max']).rename(columns={'min': 'y_min', 'max': 'y_max'})
            line_meta = line_df[['REFDES']].drop_duplicates(subset=['REFDES']).set_index('REFDES')
            line_processed = line_meta.join(x_bounds).join(y_bounds).reset_index()
            processed_coords.append(line_processed)
        
        if processed_coords:
            bounds_df = pd.concat(processed_coords, ignore_index=True)
            bounds_df['x_position'] = (bounds_df['x_min'] + bounds_df['x_max']) / 2
            bounds_df['y_position'] = (bounds_df['y_min'] + bounds_df['y_max']) / 2
            coords_cal_df = bounds_df[['REFDES', 'x_position', 'y_position']]

    # --- 步骤 B: 获取 IC 芯片的引脚信息 ---
    pin_filter = df['CLASS'].eq('PIN') & df['REFDES'].str.startswith('U', na=False)
    pins_df = df[pin_filter].copy()

    if pins_df.empty:
        print("警告: 未找到任何符合条件的 IC 引脚信息 (CLASS=PIN, REFDES 以 U 开头)。")
        return pd.DataFrame()
    
    # 保留原始行号
    pins_df['original_row'] = pins_df.index + 2

    # --- 步骤 C: 合并引脚信息和坐标信息 ---
    if not coords_cal_df.empty:
        merged_df = pd.merge(pins_df, coords_cal_df, on='REFDES', how='left')
    else:
        # 如果没有任何坐标信息，也要保证引脚信息能正常输出
        merged_df = pins_df
        merged_df['x_position'] = np.nan
        merged_df['y_position'] = np.nan

    # --- 步骤 D: 格式化最终输出 ---
    # 创建一个包含所有最终需要的数据的临时DataFrame
    final_df = pd.DataFrame({
        'ic_id': merged_df['REFDES'],
        'package_type': merged_df['SYM_NAME'],
        'pin_count': merged_df['PIN_NUMBER'],
        'x_position': merged_df['x_position'],
        'y_position': merged_df['y_position'],
        'original_row': merged_df['original_row']
    })

    # 根据内容列去除重复项，保留第一个出现的行
    content_columns = ['ic_id', 'package_type', 'pin_count', 'x_position', 'y_position']
    deduplicated_df = final_df.drop_duplicates(subset=content_columns, keep='first')

    # 使用去重后的行的原始行号作为索引
    get_connector_list_re = deduplicated_df.set_index('original_row', drop=True).sort_index()
    get_connector_list_re.index.name = None

    return get_connector_list_re

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="从 Excel 文件提取 IC 芯片列表及其中心坐标。")
    parser.add_argument('-f', '--full', action='store_true', help="完整显示所有行和列。")
    args = parser.parse_args()

    start_time = time.time()
    result_df = get_ic_chip_list()
    title = "🔍 criteria_42 - 获取 IC 芯片列表"

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

    end_time = time.time()
    if result_df is not None:
        print(f"Total script runtime: {end_time - start_time:.2f} seconds\n")
