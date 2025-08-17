
import pandas as pd
import numpy as np
import argparse
import time
import os

def get_tag_info():
    """
    从 Excel 文件中提取标签信息。
    """
    # 1. 构建 Excel 文件的绝对路径
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        excel_file_path = os.path.join(os.path.dirname(script_dir), 'parsed_tables_250804.xlsx')
    except NameError:
        excel_file_path = r'E:\pycharm_projects\testability_projects\extract_cadence\final_scripts\parsed_tables_250804.xlsx'

    # 2. 读取数据
    try:
        df = pd.read_excel(excel_file_path, sheet_name='SYM_NAME', engine='openpyxl')
    except FileNotFoundError:
        print(f"错误: 未找到 '{excel_file_path}' 文件。")
        return pd.DataFrame()
    except Exception as e:
        print(f"读取 Excel 文件时发生错误: {e}")
        return pd.DataFrame()

    # 3. 应用所有筛选条件
    try:
        condition = (
            df['REFDES'].str.startswith('TP', na=False) &
            df['CLASS'].eq('REF DES') &
            df['SUBCLASS'].isin(['SILKSCREEN_TOP', 'SILKSCREEN_BOTTOM']) &
            df['GRAPHIC_DATA_NAME'].eq('TEXT')
        )
        filtered_df = df[condition].copy()
    except KeyError as e:
        print(f"筛选数据时发生列名错误: {e}。请检查 Excel 文件是否包含所有必需的列。")
        return pd.DataFrame()

    # 4. 检查是否有数据
    if filtered_df.empty:
        print("警告: 未找到任何符合条件的标签信息。")
        return pd.DataFrame()

    # 5. 构建最终 DataFrame
    get_all_ground_networks_re = pd.DataFrame()
    get_all_ground_networks_re['p_id'] = filtered_df['REFDES']
    get_all_ground_networks_re['text_mark'] = filtered_df['GRAPHIC_DATA_7']
    get_all_ground_networks_re['color_mark'] = '' # 按要求，全部输出为空字符串

    # 6. 设置原始行号为索引，并保持原始顺序
    get_all_ground_networks_re.index = filtered_df.index + 2
    get_all_ground_networks_re.index.name = None

    return get_all_ground_networks_re

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="从 Excel 文件提取标签信息。" )
    parser.add_argument('-f', '--full', action='store_true', help="完整显示所有行和列。" )
    args = parser.parse_args()

    start_time = time.time()
    result_df = get_tag_info()
    title = "🏷️ criteria_38 - 获取标签信息"

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
