import pandas as pd
import time
import sys
import re
import argparse
import numpy as np
import os


def get_large_rcl_info():
    """
    从 Excel 文件中提取 R, C, L 元器件信息，并进行格式化处理。
    以 SYM_TYPE 工作表为绝对基准，确保原始行号准确无误。
    """
    # 获取大电阻/电容/电感信息
    # 使用相对于当前脚本文件位置的路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    excel_file = os.path.join(os.path.dirname(script_dir), 'parsed_tables_250804.xlsx')
    try:
        df_sym_type = pd.read_excel(excel_file, sheet_name='SYM_TYPE', engine='openpyxl')
        df_sym_name = pd.read_excel(excel_file, sheet_name='SYM_NAME', engine='openpyxl')
    except FileNotFoundError:
        print(f"错误：无法找到文件 '{excel_file}'。请确保文件在正确位置。")
        return pd.DataFrame()
    except Exception as e:
        print(f"读取 Excel 文件时发生错误: {e}")
        return pd.DataFrame()

    # --- 核心逻辑 ---
    # 保留原始索引
    df_sym_type.reset_index(inplace=True)
    df_sym_type.rename(columns={'index': '_original_index'}, inplace=True)

    # 仅保留 REFDES 以 R、C 或 L 开头的行
    rcl_filter = df_sym_type['REFDES'].str.startswith(('R', 'C', 'L'), na=False)
    df_sym_type_filtered = df_sym_type[rcl_filter].copy()

    # 合并两个表，以 SYM_TYPE 为基准
    df_merged = pd.merge(df_sym_type_filtered, df_sym_name[['REFDES', 'NET_NAME', 'COMP_DEVICE_TYPE']], 
                         on='REFDES', how='left')

    # 定义获取 component_type 的函数
    def get_component_type(refdes_series):
        conditions = [
            refdes_series.str.startswith('R', na=False),
            refdes_series.str.startswith('C', na=False),
            refdes_series.str.startswith('L', na=False)
        ]
        choices = ['R-Resistor', 'C-Capacitor', 'L-Inductor']
        return np.select(conditions, choices, default='')

    # 定义提取 param_value 的函数（根据新规则）
    def extract_param_value(comp_device_type_series):
        # 从 COMP_DEVICE_TYPE 中提取参数值
        param_values = []
        for value in comp_device_type_series:
            if pd.isna(value):
                param_values.append('')
                continue
            
            # 将值转换为字符串
            value_str = str(value)
            
            # 按空格分割
            parts = value_str.split()
            
            # 寻找最后一个带下划线的子串
            last_underscore_part = None
            for part in reversed(parts):  # 从后往前找
                if '_' in part:
                    last_underscore_part = part
                    break
            
            # 如果找到了带下划线的子串
            if last_underscore_part:
                # 提取最后一个下划线后的内容
                last_part = last_underscore_part.split('_')[-1]
                # 检查是否以 K、R、P、U、UH 结尾（大写）
                if last_part.upper().endswith(('K', 'R', 'P', 'U')) or last_part.upper().endswith('UH'):
                    param_values.append(last_part)
                else:
                    param_values.append('')
            else:
                param_values.append('')
        
        return param_values

    # 定义获取 unit 的函数
    def get_unit(component_types):
        units = []
        for ctype in component_types:
            if ctype == 'R-Resistor':
                units.append('Ω')
            elif ctype == 'C-Capacitor':
                units.append('F')
            elif ctype == 'L-Inductor':
                units.append('H')
            else:
                units.append('')
        return units

    # 构建最终结果 DataFrame
    component_types = get_component_type(df_merged['REFDES'])
    param_values = extract_param_value(df_merged['COMP_DEVICE_TYPE'])
    units = get_unit(component_types)
    
    get_large_rcl_info_re = pd.DataFrame({
        'original_row': df_merged['_original_index'] + 2,
        'component_id': df_merged['REFDES'],
        'net_name': df_merged['NET_NAME'],
        'component_type': component_types,
        'location_x': df_merged['SYM_CENTER_X'],
        'location_y': df_merged['SYM_CENTER_Y'],
        'param_value': param_values,
        'unit': units
    })

    # 设置并排序最终的 Excel 行号索引
    get_large_rcl_info_re.set_index('original_row', inplace=True)
    get_large_rcl_info_re.sort_index(inplace=True)
    get_large_rcl_info_re.index.name = None

    return get_large_rcl_info_re


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="从 Cadence 导出的 Excel 文件中提取大电阻/电容/电感信息。")
    parser.add_argument('-f', '--full', action='store_true', help="完整显示所有行和列。")
    args = parser.parse_args()

    start_time = time.time()
    result_df = get_large_rcl_info()
    title = "criteria_34_1 - 获取大电阻/电容/电感信息"

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
    # 只有在成功执行后才打印时间
    if result_df is not None:
        print(f"Total script runtime: {end_time - start_time:.2f} seconds\n")