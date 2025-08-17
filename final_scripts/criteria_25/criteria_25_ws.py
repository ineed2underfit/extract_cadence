import pandas as pd
import numpy as np
import argparse
import time
import os
from typing import List, Tuple

def get_copper_pad_info_list() -> pd.DataFrame:
    """
    从 Excel 文件中提取铺铜多边形信息。
    
    Returns:
        pd.DataFrame: 包含铺铜多边形信息的DataFrame，包含以下列：
            - poly_id: 铺铜多边形ID，格式为 {NET_NAME}_{layer}_{index}
            - layer: 层信息（SUBCLASS）
            - net_id: 网络名称（NET_NAME）
            - boundary: 多边形边界坐标列表
    """
    start_time = time.time()
    
    # 1. 构建 Excel 文件的绝对路径
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        excel_file_path = os.path.join(os.path.dirname(script_dir), 'parsed_tables_250804.xlsx')
    except NameError:
        excel_file_path = r'E:\pycharm_projects\testability_projects\extract_cadence\final_scripts\parsed_tables_250804.xlsx'

    # 2. 读取数据
    try:
        df = pd.read_excel(excel_file_path, sheet_name='CLASS', engine='openpyxl')
    except FileNotFoundError:
        print(f"错误: 未找到 '{excel_file_path}' 文件。")
        return pd.DataFrame()
    except Exception as e:
        print(f"读取 Excel 文件时发生错误: {e}")
        return pd.DataFrame()

    # 3. 数据筛选
    try:
        # 筛选条件
        condition = (
            (df['CLASS'] == 'ETCH') & 
            (df['GRAPHIC_DATA_10'] == 'SHAPE') & 
            (df['NET_NAME'].str.contains('GND', na=False))
        )
        filtered_df = df[condition].copy()
    except KeyError as e:
        print(f"筛选数据时发生列名错误: {e}。请检查 Excel 文件是否包含必要的列。")
        return pd.DataFrame()

    # 4. 检查是否有数据
    if filtered_df.empty:
        print("警告: 未找到任何符合条件的铺铜多边形信息。")
        return pd.DataFrame()

    # 5. 按 NET_NAME 和 SUBCLASS 分组并处理多边形
    results = []
    
    # 按 NET_NAME 和 SUBCLASS 分组
    grouped = filtered_df.groupby(['NET_NAME', 'SUBCLASS'])
    
    for (net_name, layer), group in grouped:
        # 对每个组内的多边形进行编号
        poly_count = 1
        # 按原始顺序处理每一行
        for _, row in group.iterrows():
            # 构建 poly_id
            poly_id = f"{net_name}_{layer}_{poly_count}"
            poly_count += 1
            
            # 提取坐标点
            x1, y1 = row['GRAPHIC_DATA_1'], row['GRAPHIC_DATA_2']
            x2, y2 = row['GRAPHIC_DATA_3'], row['GRAPHIC_DATA_4']
            
            # 创建边界点列表
            boundary = [(x1, y1), (x2, y2)]
            
            # 添加到结果列表
            results.append({
                'poly_id': poly_id,
                'layer': layer,
                'net_id': net_name,
                'boundary': boundary
            })
    
    # 6. 创建结果DataFrame
    if not results:
        print("警告: 未生成任何多边形数据。")
        return pd.DataFrame()
        
    result_df = pd.DataFrame(results)
    
    # 7. 设置原始行号为索引，并保持原始顺序
    result_df.index = filtered_df.index
    result_df.index.name = None
    
    end_time = time.time()
    print(f"处理完成，耗时: {end_time - start_time:.2f} 秒")
    
    return result_df

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="从 Excel 文件提取铺铜多边形信息。")
    parser.add_argument('-f', '--full', action='store_true', help="完整显示所有行和列。")
    args = parser.parse_args()

    start_time = time.time()
    result_df = get_copper_pad_info_list()
    title = "🔶 criteria_25_get_copper_pad_info_list - 获取铺铜多边形信息"

    if result_df is not None and not result_df.empty:
        print("\n" + "="*50)
        print(f" {title}")
        if args.full:
            print(" Mode: Full Mode (--full)")
            print("="*50)
            with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 1000):
                print(result_df)
            print(f"\n[{result_df.shape[0]} rows x {result_df.shape[1]} columns]")
        else:
            print(" Mode: Default (use -f or --full to show all)")
            print("="*50)
            print(result_df)

    end_time = time.time()
    if result_df is not None:
        print(f"Total script runtime: {end_time - start_time:.2f} seconds\n")
