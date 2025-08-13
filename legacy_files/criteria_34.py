import pandas as pd
import time
import sys
import re
import argparse
import numpy as np


def get_large_rcl_info():
    """
    从 Excel 文件中提取 R, C, L 元器件信息，并进行格式化处理。
    以 SYM_TYPE 工作表为绝对基准，确保原始行号准确无误。
    """
    # 获取大电阻/电容/电感信息
    excel_file = 'parsed_tables_250804.xlsx'
    try:
        df_sym_type = pd.read_excel(excel_file, sheet_name='SYM_TYPE', engine='openpyxl')
        df_sym_name = pd.read_excel(excel_file, sheet_name='SYM_NAME', engine='openpyxl')
    except FileNotFoundError:
        print(f"错误：无法找到文件 '{excel_file}'。请确保文件在当前目录中。")
        return pd.DataFrame()
    except Exception as e:
        print(f"读取 Excel 文件时发生错误: {e}")
        return pd.DataFrame()

    # --- 核心逻辑 ---
    df_sym_type.reset_index(inplace=True)
    df_sym_type.rename(columns={'index': '_original_index'}, inplace=True)

    rcl_filter = df_sym_type['REFDES'].str.startswith(('R', 'C', 'L'), na=False)
    df_sym_type_filtered = df_sym_type[rcl_filter].copy()

    df_sym_name_unique = df_sym_name.drop_duplicates(subset='REFDES', keep='first')

    df_merged = pd.merge(df_sym_type_filtered, df_sym_name_unique, on='REFDES', how='left')

    def get_component_type(series):
        conditions = [series.str.startswith('R'), series.str.startswith('C'), series.str.startswith('L')]
        choices = ['R-Resistor', 'C-Capacitor', 'L-Inductor']
        return np.select(conditions, choices, default='')

    def extract_param_value(series):
        return series.str.upper().str.extract(r'(\d+\.?\d*[PUKRH])', expand=False).fillna('')

    def extract_unit(series):
        return series.str.upper().str.extract(r'([A-Z]+)$', expand=False).fillna('')

    param_values = extract_param_value(df_merged['COMP_DEVICE_TYPE'])
    
    final_df = pd.DataFrame({
        'original_row': df_merged['_original_index'] + 2,
        'component_id': df_merged['REFDES'],
        'net_name': df_merged['NET_NAME'],
        'component_type': get_component_type(df_merged['REFDES']),
        'location_x': df_merged['SYM_CENTER_X'],
        'location_y': df_merged['SYM_CENTER_Y'],
        'param_value_raw': df_merged['COMP_DEVICE_TYPE']
    })
    
    final_df['param_value'] = extract_param_value(final_df['param_value_raw'])
    final_df['unit'] = extract_unit(final_df['param_value'])

    final_df.drop(columns=['param_value_raw'], inplace=True)
    final_df.set_index('original_row', inplace=True)
    final_df.sort_index(inplace=True)
    final_df.index.name = None

    return final_df

# 获取该网络上的连接的所有元件及其参数
def get_connected_components_on_net_re():
    """
    从 NET_NAME_SORT 工作表中提取网络上的连接元器件信息。
    """
    # 1. 从 Excel 文件读取数据
    excel_file = 'parsed_tables_250804.xlsx'
    try:
        df = pd.read_excel(excel_file, sheet_name='NET_NAME_SORT', engine='openpyxl')
    except FileNotFoundError:
        print(f"错误：无法找到文件 '{excel_file}'。请确保文件在当前目录中。")
        return pd.DataFrame()
    except Exception as e:
        print(f"读取 Excel 文件时发生错误: {e}")
        return pd.DataFrame()

    # 2. 保留原始索引作为“身份证”
    df.reset_index(inplace=True)
    df.rename(columns={'index': '_original_index'}, inplace=True)

    # 3. 一次性、安全地构建最终 DataFrame
    get_connected_components_on_net_re = pd.DataFrame({
        'original_row': df['_original_index'] + 2,
        # 确保 REFDES 和 PIN_NUMBER 在拼接前都是字符串
        'component_id': df['REFDES'].astype(str) + '_' + df['PIN_NUMBER'].astype(str),
        'net_name': df['NET_NAME']
    })

    # 4. 设置并排序最终的 Excel 行号索引
    get_connected_components_on_net_re.set_index('original_row', inplace=True)
    get_connected_components_on_net_re.sort_index(inplace=True)
    get_connected_components_on_net_re.index.name = None
    
    return get_connected_components_on_net_re

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="从 Cadence 导出的 Excel 文件中提取信息。" )
    parser.add_argument('-f', '--full', action='store_true', help="完整显示所有行和列。" )
    args = parser.parse_args()

    # --- 添加函数选择菜单 ---
    choice = input("Select an option:\n 1: 获取大电阻/电容/电感信息\n 2: 获取网络上的连接元器件\nEnter your choice (1 or 2): ")

    start_time = time.time()
    result_df = None
    title = ""

    if choice == '1':
        result_df = get_large_rcl_info()
        title = "🔍 criteria_34 - 获取大电阻/电容/电感信息"
    elif choice == '2':
        result_df = get_connected_components_on_net_re()
        title = "🔍 criteria_34 - 获取该网络上的连接的所有元件及其参数"
    else:
        print("\n无效的选项，请输入 1 或 2。" )

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
