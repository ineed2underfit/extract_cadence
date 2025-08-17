import pandas as pd
import numpy as np
import argparse
import time
import os


def get_copper_pad_info_list():
    """
    从 Excel 文件中提取满足条件的铜皮信息。
    """
    # 1. 构建 Excel 文件的绝对路径
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        excel_file_path = os.path.join(os.path.dirname(os.path.dirname(script_dir)), 'final_scripts', 'parsed_tables_250804.xlsx')
    except NameError:
        excel_file_path = r'G:\python_projects\testability_projects\extract_cadence\final_scripts\parsed_tables_250804.xlsx'

    # 2. 读取数据
    try:
        df = pd.read_excel(excel_file_path, sheet_name='CLASS', engine='openpyxl')
    except FileNotFoundError:
        print(f"错误: 未找到 '{excel_file_path}' 文件。")
        return pd.DataFrame()
    except Exception as e:
        print(f"读取 Excel 文件时发生错误: {e}")
        return pd.DataFrame()

    # 3. 筛选数据
    try:
        # 筛选条件: CLASS 字段为 "ETCH" 且 GRAPHIC_DATA_10 字段为 "SHAPE" 且 NET_NAME 包含 "GND"
        condition = (
            (df['CLASS'] == 'ETCH') &
            (df['GRAPHIC_DATA_10'] == 'SHAPE') &
            (df['NET_NAME'].str.contains('GND', na=False))
        )
        filtered_df = df[condition].copy()
    except KeyError as e:
        print(f"筛选数据时发生列名错误: {e}。请检查 Excel 文件是否包含所需列。")
        return pd.DataFrame()

    # 4. 检查是否有数据
    if filtered_df.empty:
        print("警告: 未找到满足条件的铜皮信息。")
        return pd.DataFrame()

    # 5. 处理多边形拼接逻辑
    # 按照 NET_NAME 和 SUBCLASS 分组处理
    grouped = filtered_df.groupby(['NET_NAME', 'SUBCLASS'], sort=False)
    
    # 存储结果的列表
    result_data = []
    
    # 遍历每个分组
    for (net_name, subclass), group in grouped:
        # 按原始行号排序
        group = group.sort_index()
        
        # 将线段转换为点对
        segments = []
        for idx, row in group.iterrows():
            x1, y1 = row['GRAPHIC_DATA_1'], row['GRAPHIC_DATA_2']
            x2, y2 = row['GRAPHIC_DATA_3'], row['GRAPHIC_DATA_4']
            segments.append({
                'index': idx,
                'start': (x1, y1),
                'end': (x2, y2)
            })
        
        # 查找闭合多边形
        polygons = []
        used_indices = set()
        
        for i, seg in enumerate(segments):
            if i in used_indices:
                continue
                
            # 从当前线段开始构建多边形
            polygon = [seg['start'], seg['end']]
            used_indices.add(i)
            start_point = seg['start']
            current_point = seg['end']
            
            # 尝试连接其他线段形成闭合多边形
            changed = True
            while changed and len(used_indices) < len(segments):
                changed = False
                for j, next_seg in enumerate(segments):
                    if j in used_indices:
                        continue
                    
                    # 检查是否可以连接
                    if next_seg['start'] == current_point:
                        # 正向连接
                        polygon.append(next_seg['end'])
                        current_point = next_seg['end']
                        used_indices.add(j)
                        changed = True
                        break
                    elif next_seg['end'] == current_point:
                        # 反向连接
                        polygon.append(next_seg['start'])
                        current_point = next_seg['start']
                        used_indices.add(j)
                        changed = True
                        break
                
                # 检查是否闭合
                if current_point == start_point:
                    break
            
            # 如果成功闭合，添加到结果中
            if current_point == start_point and len(polygon) > 2:
                # 移除最后一个重复点（与第一个点相同）
                polygon = polygon[:-1]
                polygons.append({
                    'points': polygon,
                    'indices': [seg['index'] for seg in segments if seg['index'] in used_indices]
                })
        
        # 为每个找到的多边形创建记录
        for poly_idx, polygon in enumerate(polygons, 1):
            poly_id = f"{net_name}_{subclass}_{poly_idx}"
            boundary = polygon['points']
            
            # 获取该多边形中最小的原始行号作为代表行号
            original_index = min(polygon['indices']) + 2  # Excel行号从1开始，且有标题行
            
            result_data.append({
                'poly_id': poly_id,
                'layer': subclass,
                'net_id': net_name,
                'boundary': boundary
            })
    
    # 6. 构建最终 DataFrame
    if not result_data:
        print("警告: 未找到任何闭合的多边形。")
        return pd.DataFrame()
    
    criteria_25_get_copper_pad_info_list_re = pd.DataFrame(result_data)
    
    # 设置原始行号为索引，并保持原始顺序
    # 注意：这里我们使用多边形在结果中的顺序作为索引，而不是原始Excel行号
    # 因为一个原始行号可能对应多个多边形，或者多个原始行号组成一个多边形
    
    return criteria_25_get_copper_pad_info_list_re


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="从 Excel 文件提取满足条件的铜皮信息。")
    parser.add_argument('-f', '--full', action='store_true', help="完整显示所有行和列。")
    args = parser.parse_args()

    start_time = time.time()
    result_df = get_copper_pad_info_list()
    title = "🗺️ criteria_25_get_copper_pad_info_list - 获取铜皮多边形信息"

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