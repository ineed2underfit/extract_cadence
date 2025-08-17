
import pandas as pd
import numpy as np
import argparse
import time
import os
import re

def extract_param_value(device_type_str):
    """
    根据特定规则从 COMP_DEVICE_TYPE 字符串中提取参数值。
    """
    if not isinstance(device_type_str, str):
        return np.nan

    parts = device_type_str.split()
    last_part_with_underscore = None
    for part in parts:
        if '_' in part:
            last_part_with_underscore = part

    if last_part_with_underscore is None:
        return np.nan

    # 提取最后一个下划线后的内容
    value = last_part_with_underscore.split('_')[-1]

    # 检查结尾是否符合要求
    valid_endings = ['K', 'R', 'P', 'U', 'UH']
    if any(value.upper().endswith(ending) for ending in valid_endings):
        return value
    else:
        return np.nan

def get_large_rcl_info():
    """
    从 Excel 文件中提取大电阻、电容、电感信息。
    """
    # 1. 构建 Excel 文件的绝对路径
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        excel_file_path = os.path.join(os.path.dirname(script_dir), 'parsed_tables_250804.xlsx')
    except NameError:
        excel_file_path = r'E:\pycharm_projects\testability_projects\extract_cadence\final_scripts\parsed_tables_250804.xlsx'

    # 2. 读取数据
    try:
        type_df = pd.read_excel(excel_file_path, sheet_name='SYM_TYPE', engine='openpyxl')
        name_df = pd.read_excel(excel_file_path, sheet_name='SYM_NAME', engine='openpyxl')
    except Exception as e:
        print(f"读取 Excel 文件时发生错误: {e}")
        return pd.DataFrame()

    # 3. 筛选 SYM_TYPE 表
    type_filter = type_df['REFDES'].str.startswith(('R', 'C', 'L'), na=False)
    base_df = type_df[type_filter].copy()
    if base_df.empty:
        print("警告: 在 SYM_TYPE 表中未找到 R, C, L 开头的元件。")
        return pd.DataFrame()
    base_df['original_row'] = base_df.index + 2

    # 4. 准备 SYM_NAME 表用于合并（去重以保证一对一）
    name_agg_df = name_df[['REFDES', 'NET_NAME', 'COMP_DEVICE_TYPE']].drop_duplicates(subset=['REFDES'], keep='first')

    # 5. 合并数据
    merged_df = pd.merge(base_df, name_agg_df, on='REFDES', how='left')

    # 6. 构建最终 DataFrame
    get_large_rcl_info_re = pd.DataFrame()
    get_large_rcl_info_re['component_id'] = merged_df['REFDES']
    get_large_rcl_info_re['net_name'] = merged_df['NET_NAME']
    
    # 映射 component_type
    type_map = {'R': 'R-Resistor', 'C': 'C-Capacitor', 'L': 'L-Inductor'}
    get_large_rcl_info_re['component_type'] = get_large_rcl_info_re['component_id'].str[0].map(type_map)

    get_large_rcl_info_re['location_x'] = merged_df['SYM_CENTER_X']
    get_large_rcl_info_re['location_y'] = merged_df['SYM_CENTER_Y']

    # 应用函数提取 param_value
    get_large_rcl_info_re['param_value'] = merged_df['COMP_DEVICE_TYPE'].apply(extract_param_value)

    # 映射 unit
    unit_map = {'R-Resistor': 'Ω', 'C-Capacitor': 'F', 'L-Inductor': 'H'}
    get_large_rcl_info_re['unit'] = get_large_rcl_info_re['component_type'].map(unit_map)
    
    # 7. 去重与索引设置
    # 先设置索引，再对内容去重，这样可以保留第一个出现的原始行号
    get_large_rcl_info_re['original_row'] = merged_df['original_row']
    final_df = get_large_rcl_info_re.drop_duplicates()
    final_df = final_df.set_index('original_row').sort_index()
    final_df.index.name = None

    return final_df.drop(columns=['original_row'], errors='ignore')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="提取大电阻、电容、电感信息。" )
    parser.add_argument('-f', '--full', action='store_true', help="完整显示所有行和列。" )
    args = parser.parse_args()

    start_time = time.time()
    result_df = get_large_rcl_info()
    title = "🔩 criteria_34 - 获取大阻容电感信息"

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

    end_time = time.time()
    if result_df is not None:
        print(f"Total script runtime: {end_time - start_time:.2f} seconds\n")
