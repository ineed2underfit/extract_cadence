import pandas as pd
import numpy as np
import argparse
import time
import os

def get_connector_pin_list():
    """
    从 Excel 文件中提取连接器引脚列表信息。

    筛选条件:
        - REFDES 以 'XP' 开头。
    """
    # 1. 构建 Excel 文件的绝对路径
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        excel_file_path = os.path.join(os.path.dirname(script_dir), 'parsed_tables_250804.xlsx')
    except NameError:
        excel_file_path = r'E:\pycharm_projects\testability_projects\extract_cadence\final_scripts\parsed_tables_250804.xlsx'

    # 2. 读取 Excel 数据
    try:
        df = pd.read_excel(excel_file_path, sheet_name='SYM_NAME', engine='openpyxl')
    except FileNotFoundError:
        print(f"错误: 未找到 '{excel_file_path}' 文件。")
        return pd.DataFrame()
    except Exception as e:
        print(f"读取 Excel 文件时发生错误: {e}")
        return pd.DataFrame()

    # 3. 应用筛选条件：REFDES 以 'XP' 开头
    try:
        condition = df['REFDES'].str.startswith('XP', na=False)
        filtered_df = df[condition].copy()
    except KeyError as e:
        print(f"筛选数据时发生列名错误: {e}。请检查 Excel 文件是否包含 'REFDES' 列。")
        return pd.DataFrame()

    # 4. 检查是否有数据
    if filtered_df.empty:
        print("警告: 未找到任何 REFDES 以 'XP' 开头的连接器信息。")
        return pd.DataFrame()

    # 5. 构建最终 DataFrame
    # 为安全拼接，先将可能为 NaN 的列转为字符串
    refdes_str = filtered_df['REFDES'].astype(str)
    pin_num_str = filtered_df['PIN_NUMBER'].astype(str)

    get_connector_pin_list_re = pd.DataFrame({
        'original_row': filtered_df.index + 2, # Excel 行号从1开始，且有1行表头
        'connector_id': filtered_df['REFDES'],
        'pin_id': refdes_str + '_' + pin_num_str,
        'net_name': filtered_df['NET_NAME']
    })

    # 6. 设置原始行号为索引，并保持原始顺序（不排序）
    get_connector_pin_list_re = get_connector_pin_list_re.set_index('original_row', drop=True)
    get_connector_pin_list_re.index.name = None

    return get_connector_pin_list_re

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="从 Excel 文件提取连接器引脚列表。")
    parser.add_argument('-f', '--full', action='store_true', help="完整显示所有行和列。")
    args = parser.parse_args()

    start_time = time.time()
    result_df = get_connector_pin_list()
    title = "🔍 criteria_29_get_connector_pin_list - 获取连接器引脚列表"

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
