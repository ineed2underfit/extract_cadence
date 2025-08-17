import pandas as pd
import numpy as np
import argparse
import time
import os


def get_copper_pad_info_list():
    """
    从 Excel 文件中提取铺铜多边形区域信息。
    """

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

    # 3. 筛选数据 (CLASS="ETCH", GRAPHIC_DATA_10="SHAPE", NET_NAME 包含 "GND")
    try:
        condition = (
            (df['CLASS'] == 'ETCH') &
            (df['GRAPHIC_DATA_10'] == 'SHAPE') &
            (df['NET_NAME'].str.contains('GND', na=False))
        )
        filtered_df = df[condition].copy()
    except KeyError as e:
        print(f"筛选数据时发生列名错误: {e}。请检查 Excel 文件。")
        return pd.DataFrame()

    if filtered_df.empty:
        print("警告: 未找到符合条件的铺铜区域。")
        return pd.DataFrame()

    # 4. 构建多边形
    result_rows = []
    group_cols = ['NET_NAME', 'SUBCLASS']
    grouped = filtered_df.groupby(group_cols, sort=False)

    for (net_name, layer), group in grouped:
        group = group.copy()
        group.index = filtered_df.index[filtered_df.index.isin(group.index)]  # 保留原始行号
        group = group.sort_index()  # 保持原始 Excel 行顺序

        visited = set()
        polygon_id = 0

        for idx, row in group.iterrows():
            if idx in visited:
                continue

            # 起点线段
            x1, y1, x2, y2 = row['GRAPHIC_DATA_1'], row['GRAPHIC_DATA_2'], row['GRAPHIC_DATA_3'], row['GRAPHIC_DATA_4']
            boundary = [(x1, y1), (x2, y2)]
            visited.add(idx)

            # 拼接后续线段
            current_point = (x2, y2)
            closed = False

            while True:
                next_seg = group.loc[
                    (~group.index.isin(visited)) &
                    (
                        (group['GRAPHIC_DATA_1'] == current_point[0]) &
                        (group['GRAPHIC_DATA_2'] == current_point[1])
                        |
                        (group['GRAPHIC_DATA_3'] == current_point[0]) &
                        (group['GRAPHIC_DATA_4'] == current_point[1])
                    )
                ]

                if next_seg.empty:
                    break

                next_idx, next_row = next_seg.iloc[0].name, next_seg.iloc[0]
                nx1, ny1, nx2, ny2 = next_row['GRAPHIC_DATA_1'], next_row['GRAPHIC_DATA_2'], next_row['GRAPHIC_DATA_3'], next_row['GRAPHIC_DATA_4']

                if (nx1, ny1) == current_point:
                    boundary.append((nx2, ny2))
                    current_point = (nx2, ny2)
                else:
                    boundary.append((nx1, ny1))
                    current_point = (nx1, ny1)

                visited.add(next_idx)

                # 闭合检查
                if boundary[0] == current_point:
                    closed = True
                    break

            if closed:
                polygon_id += 1
                poly_id = f"{net_name}_{layer}_{polygon_id}"
                result_rows.append({
                    'poly_id': poly_id,
                    'layer': layer,
                    'net_id': net_name,
                    'boundary': boundary
                })

    # 5. 构建 DataFrame
    criteria_25_get_copper_pad_info_list_re = pd.DataFrame(result_rows)

    return criteria_25_get_copper_pad_info_list_re


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="从 Excel 文件提取铺铜多边形区域信息。")
    parser.add_argument('-f', '--full', action='store_true', help="完整显示所有行和列。")
    args = parser.parse_args()

    start_time = time.time()
    result_df = get_copper_pad_info_list()
    title = "🔶 criteria_25_get_copper_pad_info_list - 获取铺铜多边形区域信息"

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
