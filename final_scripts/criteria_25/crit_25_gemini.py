import pandas as pd
import numpy as np
import argparse
import time
import os
from collections import defaultdict


def get_copper_pad_info_list():
    """
    从 Excel 文件中读取 CLASS 工作表，筛选出与铺铜相关的数据，
    并根据坐标信息重构出每个铺铜区域的多边形边界。

    Returns:
        pandas.DataFrame: 包含铺铜信息 (poly_id, layer, net_id, boundary) 的 DataFrame。
                          如果发生错误或未找到数据，则返回一个空的 DataFrame。
    """
    # 使用绝对路径
    excel_file_path = r'G:\python_projects\testability_projects\extract_cadence\final_scripts\parsed_tables_250804.xlsx'

    # 2. 读取 Excel 数据
    try:
        df = pd.read_excel(excel_file_path, sheet_name='CLASS', engine='openpyxl')
    except FileNotFoundError:
        print(f"错误: 文件未找到 '{excel_file_path}'。请检查路径是否正确。")
        return pd.DataFrame()
    except Exception as e:
        print(f"读取 Excel 文件时发生错误: {e}")
        return pd.DataFrame()

    # 3. 数据筛选
    try:
        condition = (
                (df['CLASS'] == 'ETCH') &
                (df['GRAPHIC_DATA_10'] == 'SHAPE') &
                (df['NET_NAME'].str.contains('GND', na=False))
        )
        filtered_df = df[condition].copy()
    except KeyError as e:
        print(f"筛选数据时发生列名错误: {e}。请检查 Excel 文件是否包含所需的列。")
        return pd.DataFrame()

    # 4. 检查是否有数据
    if filtered_df.empty:
        print("警告: 根据筛选条件，未找到任何铺铜信息。")
        return pd.DataFrame()

    # 5. 重构多边形边界
    output_rows = []
    # 按 NET_NAME 和 SUBCLASS 分组，以处理每个铺铜区域
    grouped = filtered_df.groupby(['NET_NAME', 'SUBCLASS'])

    for (net_name, layer), group_df in grouped:
        # 将线段数据转换为更易于处理的格式 (起点 -> 终点)
        # 使用 iterrows() 以保持 Excel 中的原始顺序
        segments = []
        for index, row in group_df.iterrows():
            p1 = (row['GRAPHIC_DATA_1'], row['GRAPHIC_DATA_2'])
            p2 = (row['GRAPHIC_DATA_3'], row['GRAPHIC_DATA_4'])
            segments.append({'start': p1, 'end': p2, 'used': False})

        poly_counter = 0
        for i in range(len(segments)):
            if segments[i]['used']:
                continue

            poly_counter += 1
            # 找到一个未使用的线段作为新多边形的起点
            current_polygon = [segments[i]['start'], segments[i]['end']]
            segments[i]['used'] = True

            is_closed = (segments[i]['end'] == segments[i]['start'])

            # 循环拼接线段，直到多边形闭合或无更多线段可连接
            while not is_closed:
                found_next = False
                last_point = current_polygon[-1]

                # 从头开始寻找下一个连接点，以保证拼接顺序
                for j in range(len(segments)):
                    if not segments[j]['used'] and segments[j]['start'] == last_point:
                        next_point = segments[j]['end']
                        segments[j]['used'] = True

                        # 检查是否闭合
                        if next_point == current_polygon[0]:
                            is_closed = True
                        else:
                            current_polygon.append(next_point)

                        found_next = True
                        break  # 找到后跳出内层循环，继续寻找下一个点

                # 如果遍历完所有线段都找不到下一个连接点，说明此路径中断
                if not found_next:
                    # print(f"警告: 在 {net_name}/{layer} 中发现未闭合的多边形。")
                    break

            if is_closed:
                poly_id = f"{net_name}_{layer}_{poly_counter}"
                output_rows.append({
                    'poly_id': poly_id,
                    'layer': layer,
                    'net_id': net_name,
                    'boundary': current_polygon
                })

    # 6. 构建最终的 DataFrame
    if not output_rows:
        print("警告: 成功处理了数据，但未能构建任何闭合的多边形。")
        return pd.DataFrame()

    criteria_25_get_copper_pad_info_list_re = pd.DataFrame(output_rows)

    # 保留原始 Excel 行号的意图是通过处理顺序来体现，最终输出是按多边形而非线段，故采用新的默认索引
    return criteria_25_get_copper_pad_info_list_re


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="从 Excel 文件中提取铺铜信息并重构多边形边界。")
    parser.add_argument('-f', '--full', action='store_true', help="完整显示 DataFrame 的所有行和列。")
    args = parser.parse_args()

    start_time = time.time()
    result_df = get_copper_pad_info_list()
    title = "🌍 criteria_25_get_copper_pad_info_list - 获取铺铜信息"

    if result_df is not None and not result_df.empty:
        print("\n==================================================")
        print(f" {title}")
        if args.full:
            print(" Mode: Full Mode (--full)")
            print("==================================================")
            # 设置 pandas 打印选项以完整显示
            with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 120):
                print(result_df)
            print(f"\n[{result_df.shape[0]} rows x {result_df.shape[1]} columns]")
        else:
            print(" Mode: Default (use -f or --full to show all)")
            print("==================================================")
            print(result_df)

    end_time = time.time()
    if result_df is not None:
        print(f"\nTotal script runtime: {end_time - start_time:.2f} seconds")
