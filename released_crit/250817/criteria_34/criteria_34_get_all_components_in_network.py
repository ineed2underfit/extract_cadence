import pandas as pd
import numpy as np
import argparse
import time
import os

def get_connected_components_on_net():
    """
    从 Excel 的 NET_NAME_SORT 工作表中提取所有连接的元件信息。
    """
    # 1. 构建 Excel 文件的绝对路径
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        excel_file_path = os.path.join(os.path.dirname(script_dir), 'parsed_tables_250804.xlsx')
    except NameError:
        excel_file_path = r'E:\pycharm_projects\testability_projects\extract_cadence\final_scripts\parsed_tables_250804.xlsx'

    # 2. 读取数据
    try:
        df = pd.read_excel(excel_file_path, sheet_name='NET_NAME_SORT', engine='openpyxl')
    except FileNotFoundError:
        print(f"错误: 未找到 '{excel_file_path}' 文件。")
        return pd.DataFrame()
    except Exception as e:
        print(f"读取 Excel 文件时发生错误: {e}")
        return pd.DataFrame()

    # 3. 检查是否有数据
    if df.empty:
        print("警告: NET_NAME_SORT 工作表为空或不存在。")
        return pd.DataFrame()

    # 4. 构建最终 DataFrame
    # 为安全拼接，先将可能为 NaN 的列转为字符串
    try:
        refdes_str = df['REFDES'].astype(str).fillna('')
        pin_num_str = df['PIN_NUMBER'].astype(str).fillna('')
    except KeyError as e:
        print(f"错误: 工作表中缺少必需的列: {e}")
        return pd.DataFrame()

    get_connected_components_on_net_re = pd.DataFrame()
    get_connected_components_on_net_re['component_id'] = refdes_str + '_' + pin_num_str
    get_connected_components_on_net_re['net_name'] = df['NET_NAME']
    
    # 5. 设置原始行号为索引，并保持原始顺序
    get_connected_components_on_net_re.index = df.index + 2
    get_connected_components_on_net_re.index.name = None

    return get_connected_components_on_net_re

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="从 NET_NAME_SORT 工作表提取所有连接的元件列表。")
    parser.add_argument('-f', '--full', action='store_true', help="完整显示所有行和列。")
    args = parser.parse_args()

    start_time = time.time()
    result_df = get_connected_components_on_net()
    title = "🔍 criteria_34 - 获取网络上的所有连接元件"

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
