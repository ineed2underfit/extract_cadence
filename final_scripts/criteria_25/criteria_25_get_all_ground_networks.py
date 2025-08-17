
import pandas as pd
import numpy as np
import argparse
import time
import os

def get_all_ground_networks():
    """
    从 Excel 文件中提取所有接地网络信息，并进行分类。
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

    # 3. 筛选包含'GND'的行
    try:
        condition = df['NET_NAME'].str.contains('GND', na=False)
        filtered_df = df[condition].copy()
    except KeyError as e:
        print(f"筛选数据时发生列名错误: {e}。请检查 Excel 文件是否包含 'NET_NAME' 列。")
        return pd.DataFrame()

    # 4. 检查是否有数据
    if filtered_df.empty:
        print("警告: 未找到任何 NET_NAME 包含 'GND' 的网络信息。")
        return pd.DataFrame()

    # 5. 构建最终 DataFrame
    get_all_ground_networks_re = pd.DataFrame()
    get_all_ground_networks_re['net_id'] = filtered_df['REFDES']
    get_all_ground_networks_re['name'] = filtered_df['NET_NAME']

    # 定义类型映射规则
    # 定义类型映射规则
    conditions = [
        filtered_df['NET_NAME'].isin(['DGND', 'SGND']),
        filtered_df['NET_NAME'].isin(['ADCGND', 'AGND', 'PGND', 'PGND_IN']),
        filtered_df['NET_NAME'].eq('FGND')
    ]
    # 根据您的新要求，修改映射的目标值为英文缩写
    choices = ['DGND', 'AGND', 'FGND']
    # 使用 np.select 进行条件映射
    type_col = np.select(conditions, choices, default=np.nan) # 不符合任何规则的默认为 NaN
    get_all_ground_networks_re['type'] = type_col

    # 根据新的 type 列 ('AGND') 生成 is_analog 列
    get_all_ground_networks_re['is_analog'] = (get_all_ground_networks_re['type'] == 'AGND')

    # 6. 设置原始行号为索引，并保持原始顺序
    get_all_ground_networks_re.index = filtered_df.index + 2
    get_all_ground_networks_re.index.name = None

    return get_all_ground_networks_re

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="从 Excel 文件提取所有接地网络信息。")
    parser.add_argument('-f', '--full', action='store_true', help="完整显示所有行和列。")
    args = parser.parse_args()

    start_time = time.time()
    result_df = get_all_ground_networks()
    title = "🌍 criteria_25_get_all_ground_networks - 获取所有地网络并分类"

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
