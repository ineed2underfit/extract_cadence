import pandas as pd
import numpy as np
import argparse
import time
import os

def get_copper_pad_info_list():
    """
    从Excel文件中提取铺铜多边形的边界信息。
    """
    # 1. 构建路径并读取数据
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        excel_file_path = os.path.join(os.path.dirname(script_dir), 'parsed_tables_250804.xlsx')
    except NameError:
        excel_file_path = r'E:\pycharm_projects\testability_projects\extract_cadence\final_scripts\parsed_tables_250804.xlsx'

    try:
        df = pd.read_excel(excel_file_path, sheet_name='CLASS', engine='openpyxl')
    except Exception as e:
        print(f"读取 Excel 文件时发生错误: {e}")
        return pd.DataFrame()

    # 2. 数据筛选
    try:
        condition = (
            df['CLASS'].eq('ETCH') &
            df['GRAPHIC_DATA_10'].eq('SHAPE') &
            df['NET_NAME'].str.contains('GND', na=False)
        )
        filtered_df = df[condition].copy()
    except KeyError as e:
        print(f"筛选数据时发生列名错误: {e}。")
        return pd.DataFrame()

    if filtered_df.empty:
        print("警告: 未找到符合条件的铺铜数据。" )
        return pd.DataFrame()

    # 3. [关键修正] 处理浮点数精度问题
    coord_cols = ['GRAPHIC_DATA_1', 'GRAPHIC_DATA_2', 'GRAPHIC_DATA_3', 'GRAPHIC_DATA_4']
    filtered_df[coord_cols] = filtered_df[coord_cols].round(4)
    filtered_df['original_row'] = filtered_df.index + 2

    # 4. 多边形重建
    all_polygons_data = []
    grouped = filtered_df.groupby(['NET_NAME', 'SUBCLASS'])

    for (net_name, layer), group_df in grouped:
        # 使用字典进行快速查找，键为起点，值为(终点, 原始行号, 是否已访问)
        # 存储双向边以简化查找
        edge_map = {}
        for _, row in group_df.iterrows():
            p1 = (row['GRAPHIC_DATA_1'], row['GRAPHIC_DATA_2'])
            p2 = (row['GRAPHIC_DATA_3'], row['GRAPHIC_DATA_4'])
            original_row = row['original_row']
            if p1 not in edge_map: edge_map[p1] = []
            if p2 not in edge_map: edge_map[p2] = []
            edge_map[p1].append([p2, original_row, False])
            edge_map[p2].append([p1, original_row, False])

        poly_index = 1
        for start_node in edge_map:
            for edge_data in edge_map[start_node]:
                if not edge_data[2]: # 如果该边未被访问
                    # 开始一个新的多边形路径查找
                    path = [start_node]
                    current_node = edge_data[0]
                    edge_data[2] = True # 标记为已访问
                    # 找到对应的反向边并标记
                    for rev_edge in edge_map[current_node]:
                        if rev_edge[0] == start_node and rev_edge[1] == edge_data[1]:
                            rev_edge[2] = True
                            break
                    
                    first_segment_row = edge_data[1]

                    while current_node != start_node:
                        path.append(current_node)
                        found_next = False
                        for next_edge in edge_map[current_node]:
                            if not next_edge[2]:
                                next_node_candidate = next_edge[0]
                                next_edge[2] = True
                                for rev_edge in edge_map[next_node_candidate]:
                                    if rev_edge[0] == current_node and rev_edge[1] == next_edge[1]:
                                        rev_edge[2] = True
                                        break
                                current_node = next_node_candidate
                                found_next = True
                                break
                        if not found_next:
                            path = [] # 路径不闭合，不是有效的多边形
                            break
                    
                    if path: # 如果路径有效（已闭合）
                        poly_id = f"{net_name}_{layer}_{poly_index}"
                        all_polygons_data.append({
                            'original_row': first_segment_row,
                            'poly_id': poly_id,
                            'layer': layer,
                            'net_id': net_name,
                            'boundary': path
                        })
                        poly_index += 1

    # 5. 创建最终DataFrame
    if not all_polygons_data:
        print("警告: 数据筛选后，未能成功重建任何多边形。" )
        return pd.DataFrame()

    get_copper_pad_info_list_re = pd.DataFrame(all_polygons_data)
    # 按要求使用第一条线段的原始行号作为索引
    final_df = get_copper_pad_info_list_re.set_index('original_row').sort_index()
    final_df.index.name = None

    return final_df

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="提取铺铜多边形的边界信息。" )
    parser.add_argument('-f', '--full', action='store_true', help="完整显示所有行和列。" )
    args = parser.parse_args()

    start_time = time.time()
    result_df = get_copper_pad_info_list()
    title = "🌐 criteria_25 - 获取铺铜信息列表"

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