import pandas as pd
import numpy as np
import argparse
import time
import os



def get_connector_list():
    """
    从 Excel 文件中提取连接器的边界坐标信息。

    数据来源:
        - Excel 文件: 'parsed_tables_250804.xlsx'
        - 工作表: 'SYM_NAME'

    筛选条件:
        1. 'REFDES' 列以 'XP' 开头。
        2. 'SUBCLASS' 列等于 'PLACE_BOUND_TOP'。
        3. 'GRAPHIC_DATA_NAME' 列为 'LINE' 或 'RECTANGLE'。

    坐标计算规则:
        - RECTANGLE: 每个器件只有一行，直接取 GRAPHIC_DATA_1/3 (x), 2/4 (y) 的 min/max。
        - LINE: 每个器件有四行，聚合所有行的 GRAPHIC_DATA_1/3 (x), 2/4 (y) 坐标后取 min/max。
        - NaN 值会传播，即输入为 NaN 则输出也为 NaN。

    返回:
        pandas.DataFrame: 命名为 `get_connector_list_re`，包含以下字段，并以原始行号为索引：
                          - connector_id (str): 来自 'REFDES'。
                          - shape_name (str): 来自 'GRAPHIC_DATA_NAME'。
                          - x_min (float): 边界的最小 x 坐标。
                          - y_min (float): 边界的最小 y 坐标。
                          - x_max (float): 边界的最大 x 坐标。
                          - y_max (float): 边界的最大 y 坐标。
    """
    # 1. 构建 Excel 文件的绝对路径
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # 路径上溯一层到 final_scripts 目录，然后拼接 Excel 文件名
        excel_file_path = os.path.join(os.path.dirname(script_dir), 'parsed_tables_250804.xlsx')
    except NameError:
        # 适用于非脚本环境（如 Jupyter, REPL），请根据实际情况调整
        excel_file_path = r'E:\pycharm_projects\testability_projects\extract_cadence\final_scripts\parsed_tables_250804.xlsx'

    # 2. 从 Excel 文件读取数据
    try:
        df = pd.read_excel(excel_file_path, sheet_name='SYM_NAME')
    except FileNotFoundError:
        print(f"错误: 未找到 '{excel_file_path}' 文件。" )
        return pd.DataFrame()
    except Exception as e:
        print(f"读取 Excel 文件时发生错误: {e}")
        return pd.DataFrame()

    # 3. 筛选行
    try:
        condition = (
            df['REFDES'].str.startswith('XP', na=False) &
            (df['SUBCLASS'] == 'PLACE_BOUND_TOP') &
            (df['GRAPHIC_DATA_NAME'].isin(['LINE', 'RECTANGLE']))
        )
        filtered_df = df[condition].copy()
    except KeyError as e:
        print(f"筛选数据时发生列名错误: {e}。请检查 Excel 文件是否包含所有必需的列。" )
        return pd.DataFrame()

    # 4. 检查是否有数据
    if filtered_df.empty:
        print("警告: 根据筛选条件，没有找到可处理的数据。" )
        return pd.DataFrame(columns=['connector_id', 'shape_name', 'x_min', 'y_min', 'x_max', 'y_max'])

    # 5. 保留原始 Excel 行号（索引+2，因为Excel从1开始且有1行表头）
    filtered_df['original_row'] = filtered_df.index + 2

    # 6. [关键步骤] 强制将坐标列转换为数字，无效值(如文本)变为 NaN
    coord_cols = ['GRAPHIC_DATA_1', 'GRAPHIC_DATA_2', 'GRAPHIC_DATA_3', 'GRAPHIC_DATA_4']
    for col in coord_cols:
        filtered_df[col] = pd.to_numeric(filtered_df[col], errors='coerce')

    # 7. 分离 RECTANGLE 和 LINE 数据
    rect_df = filtered_df[filtered_df['GRAPHIC_DATA_NAME'] == 'RECTANGLE'].copy()
    line_df = filtered_df[filtered_df['GRAPHIC_DATA_NAME'] == 'LINE'].copy()

    processed_results = []

    # 8. 处理 RECTANGLE 数据
    if not rect_df.empty:
        rect_df['x_min'] = np.minimum(rect_df['GRAPHIC_DATA_1'], rect_df['GRAPHIC_DATA_3'])
        rect_df['y_min'] = np.minimum(rect_df['GRAPHIC_DATA_2'], rect_df['GRAPHIC_DATA_4'])
        rect_df['x_max'] = np.maximum(rect_df['GRAPHIC_DATA_1'], rect_df['GRAPHIC_DATA_3'])
        rect_df['y_max'] = np.maximum(rect_df['GRAPHIC_DATA_2'], rect_df['GRAPHIC_DATA_4'])
        
        # 只保留最终需要的列，以确保能和 LINE 的结果干净地合并
        rect_processed = rect_df[['REFDES', 'GRAPHIC_DATA_NAME', 'original_row', 'x_min', 'y_min', 'x_max', 'y_max']]
        processed_results.append(rect_processed)

    # 9. 处理 LINE 数据
    if not line_df.empty:
        # 将 x 和 y 坐标分别 "unpivot" 成长格式，以便于分组计算
        x_coords = pd.concat([
            line_df[['REFDES', 'GRAPHIC_DATA_1']].rename(columns={'GRAPHIC_DATA_1': 'x'}),
            line_df[['REFDES', 'GRAPHIC_DATA_3']].rename(columns={'GRAPHIC_DATA_3': 'x'})
        ])
        y_coords = pd.concat([
            line_df[['REFDES', 'GRAPHIC_DATA_2']].rename(columns={'GRAPHIC_DATA_2': 'y'}),
            line_df[['REFDES', 'GRAPHIC_DATA_4']].rename(columns={'GRAPHIC_DATA_4': 'y'})
        ])

        # 按 REFDES 分组计算 min/max
        x_bounds = x_coords.groupby('REFDES')['x'].agg(['min', 'max']).rename(columns={'min': 'x_min', 'max': 'x_max'})
        y_bounds = y_coords.groupby('REFDES')['y'].agg(['min', 'max']).rename(columns={'min': 'y_min', 'max': 'y_max'})

        # 获取每个 REFDES 的元数据（shape_name 和第一个出现的 original_row）
        line_meta = line_df[['REFDES', 'GRAPHIC_DATA_NAME', 'original_row']].drop_duplicates(subset=['REFDES']).set_index('REFDES')

        # 将元数据和计算出的边界连接起来
        line_processed = line_meta.join(x_bounds).join(y_bounds).reset_index()
        processed_results.append(line_processed)

    # 10. 检查是否有任何结果
    if not processed_results:
        print("警告: 处理 RECTANGLE 和 LINE 数据后没有结果。" )
        return pd.DataFrame(columns=['connector_id', 'shape_name', 'x_min', 'y_min', 'x_max', 'y_max'])

    # 11. 合并结果
    final_df = pd.concat(processed_results, ignore_index=True)

    # 12. 重命名列并设置为正确的索引
    get_connector_list_re = final_df.rename(columns={'REFDES': 'connector_id', 'GRAPHIC_DATA_NAME': 'shape_name'})
    get_connector_list_re = get_connector_list_re.set_index('original_row').sort_index()
    get_connector_list_re.index.name = None

    # 13. [关键步骤] 确保列的顺序和名称完全符合要求
    get_connector_list_re = get_connector_list_re[['connector_id', 'shape_name', 'x_min', 'y_min', 'x_max', 'y_max']]

    return get_connector_list_re

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="从 Excel 文件提取连接器边界坐标。" )
    parser.add_argument('-f', '--full', action='store_true', help="完整显示所有行和列。" )
    args = parser.parse_args()

    start_time = time.time()
    result_df = get_connector_list()
    title = "🔩 criteria_46 - 获取连接器边界坐标"

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