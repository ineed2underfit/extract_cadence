
import pandas as pd
import numpy as np
import argparse
import time
import os
from criteria_46_get_connector_list import get_connector_list

def identify_components_in_test_area():
    """
    识别位于连接器测试区域内的元器件。

    流程:
    1.  调用 `get_connector_list()` 获取连接器的位置信息。
    2.  为每个连接器定义一个外扩 787mil 的测试区域。
    3.  从 Excel 的 'SYM_NAME' 工作表加载所有元器件的边界定义。
    4.  筛选出有效的元器件边界数据 (`PLACE_BOUND_TOP/BOTTOM`, `RECTANGLE/LINE`)。
    5.  计算每个元器件的精确边界框 (bounding box)。
    6.  遍历所有连接器和元器件对，判断元器件是否与连接器的测试区域重叠。
    7.  返回一个包含所有分析结果的 DataFrame。

    数据来源:
        - 函数: `criteria_46_get_connector_list.get_connector_list()`
        - Excel 文件: 'parsed_tables_250804.xlsx'
        - 工作表: 'SYM_NAME'

    返回:
        pandas.DataFrame: 命名为 `identify_components_in_test_area_re`，包含以下字段:
                          - `connector_id` (str): 连接器 ID。
                          - `component_id` (str): 元器件 ID。
                          - `expansion_distance` (float): 固定的外扩距离 (787)。
                          - `test_area_x1`, `test_area_y1`, `test_area_x2`, `test_area_y2` (float): 连接器测试区域的坐标。
                          - `component_x1`, `component_y1`, `component_x2`, `component_y2` (float): 元器件的边界坐标。
                          - `is_in_test_area` (bool): 元器件是否与测试区域重叠。
    """
    # 1. 获取连接器列表及其边界
    connectors_df = get_connector_list()
    if connectors_df.empty:
        print("警告: 未能从 get_connector_list() 获取任何连接器数据，无法继续。")
        return pd.DataFrame()

    # 2. 定义测试区域
    expansion_distance = 787.0
    connectors_df['expansion_distance'] = expansion_distance
    connectors_df['test_area_x1'] = connectors_df['x_min'] - expansion_distance
    connectors_df['test_area_y1'] = connectors_df['y_min'] - expansion_distance
    connectors_df['test_area_x2'] = connectors_df['x_max'] + expansion_distance
    connectors_df['test_area_y2'] = connectors_df['y_max'] + expansion_distance

    # 3. 加载元器件数据
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        excel_file_path = os.path.join(os.path.dirname(script_dir), 'parsed_tables_250804.xlsx')
    except NameError:
        excel_file_path = r'G:\python_projects\testability_projects\extract_cadence\final_scripts\parsed_tables_250804.xlsx'

    try:
        sym_name_df = pd.read_excel(excel_file_path, sheet_name='SYM_NAME')
    except FileNotFoundError:
        print(f"错误: 未找到 '{excel_file_path}' 文件。")
        return pd.DataFrame()
    except Exception as e:
        print(f"读取 Excel 文件时发生错误: {e}")
        return pd.DataFrame()

    # 4. 筛选元器件的边界定义
    comp_condition = (
        sym_name_df['SUBCLASS'].isin(['PLACE_BOUND_TOP', 'PLACE_BOUND_BOTTOM']) &
        sym_name_df['GRAPHIC_DATA_NAME'].isin(['RECTANGLE', 'LINE'])
    )
    components_raw_df = sym_name_df[comp_condition].copy()
    
    if components_raw_df.empty:
        print("警告: 在 'SYM_NAME' 表中未找到任何元器件的边界定义。")
        return pd.DataFrame()

    # 保留原始行号
    components_raw_df['original_row'] = components_raw_df.index

    # 5. 计算每个元器件的边界框
    coord_cols = ['GRAPHIC_DATA_1', 'GRAPHIC_DATA_2', 'GRAPHIC_DATA_3', 'GRAPHIC_DATA_4']
    for col in coord_cols:
        components_raw_df[col] = pd.to_numeric(components_raw_df[col], errors='coerce')

    # 分离 RECTANGLE 和 LINE
    rect_df = components_raw_df[components_raw_df['GRAPHIC_DATA_NAME'] == 'RECTANGLE'].copy()
    line_df = components_raw_df[components_raw_df['GRAPHIC_DATA_NAME'] == 'LINE'].copy()

    processed_components = []

    # 处理 RECTANGLE (聚合版本)
    if not rect_df.empty:
        # 首先，计算每个单独矩形行的边界
        rect_df['x1'] = np.minimum(rect_df['GRAPHIC_DATA_1'], rect_df['GRAPHIC_DATA_3'])
        rect_df['y1'] = np.minimum(rect_df['GRAPHIC_DATA_2'], rect_df['GRAPHIC_DATA_4'])
        rect_df['x2'] = np.maximum(rect_df['GRAPHIC_DATA_1'], rect_df['GRAPHIC_DATA_3'])
        rect_df['y2'] = np.maximum(rect_df['GRAPHIC_DATA_2'], rect_df['GRAPHIC_DATA_4'])
        
        # 按 REFDES 分组，计算包围所有矩形的总边界
        rect_bounds = rect_df.groupby('REFDES').agg(
            component_x1=('x1', 'min'),
            component_y1=('y1', 'min'),
            component_x2=('x2', 'max'),
            component_y2=('y2', 'max')
        )
        
        # 获取每个组件的第一个原始行号作为代表
        rect_meta = rect_df[['REFDES', 'original_row']].drop_duplicates(subset=['REFDES']).set_index('REFDES')
        
        rect_processed = rect_meta.join(rect_bounds).reset_index()
        processed_components.append(rect_processed)

    # 处理 LINE
    if not line_df.empty:
        x_coords = pd.concat([
            line_df[['REFDES', 'GRAPHIC_DATA_1']].rename(columns={'GRAPHIC_DATA_1': 'x'}),
            line_df[['REFDES', 'GRAPHIC_DATA_3']].rename(columns={'GRAPHIC_DATA_3': 'x'})
        ])
        y_coords = pd.concat([
            line_df[['REFDES', 'GRAPHIC_DATA_2']].rename(columns={'GRAPHIC_DATA_2': 'y'}),
            line_df[['REFDES', 'GRAPHIC_DATA_4']].rename(columns={'GRAPHIC_DATA_4': 'y'})
        ])
        x_bounds = x_coords.groupby('REFDES')['x'].agg(['min', 'max']).rename(columns={'min': 'component_x1', 'max': 'component_x2'})
        y_bounds = y_coords.groupby('REFDES')['y'].agg(['min', 'max']).rename(columns={'min': 'component_y1', 'max': 'component_y2'})
        
        line_meta = line_df[['REFDES', 'original_row']].drop_duplicates(subset=['REFDES']).set_index('REFDES')
        line_processed = line_meta.join(x_bounds).join(y_bounds).reset_index()
        processed_components.append(line_processed)

    if not processed_components:
        print("警告: 处理后没有有效的元器件边界数据。")
        return pd.DataFrame()

    components_df = pd.concat(processed_components, ignore_index=True).rename(columns={'REFDES': 'component_id'})

    # 6. 判断重叠
    if components_df.empty:
        print("警告: 没有有效的元器件可供比较。")
        return pd.DataFrame()
        
    # 使用 cross join 生成所有 connector 和 component 的组合
    connectors_df['_key'] = 1
    components_df['_key'] = 1
    cross_join_df = pd.merge(connectors_df, components_df, on='_key', how='outer').drop('_key', axis=1)

    # 向量化计算重叠
    overlap_x = (cross_join_df['test_area_x1'] < cross_join_df['component_x2']) & (cross_join_df['test_area_x2'] > cross_join_df['component_x1'])
    overlap_y = (cross_join_df['test_area_y1'] < cross_join_df['component_y2']) & (cross_join_df['test_area_y2'] > cross_join_df['component_y1'])
    cross_join_df['is_in_test_area'] = overlap_x & overlap_y

    # 7. 格式化最终输出
    result_cols = [
        'connector_id', 'component_id', 'expansion_distance',
        'test_area_x1', 'test_area_y1', 'test_area_x2', 'test_area_y2',
        'component_x1', 'component_y1', 'component_x2', 'component_y2',
        'is_in_test_area'
    ]
    identify_components_in_test_area_re = cross_join_df[result_cols]
    
    # 合并原始行号并设为索引
    id_to_row_map = components_df[['component_id', 'original_row']].drop_duplicates(subset=['component_id'])
    final_df_with_row = pd.merge(
        identify_components_in_test_area_re,
        id_to_row_map,
        on='component_id',
        how='left'
    )
    final_df = final_df_with_row.set_index('original_row', drop=True)
    final_df.index.name = None

    return final_df

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="识别位于连接器测试区域内的元器件。 সন")
    parser.add_argument('-f', '--full', action='store_true', help="完整显示所有行和列。")
    args = parser.parse_args()

    start_time = time.time()
    result_df = identify_components_in_test_area()
    title = "🔩 criteria_46 - 识别测试区域内的元器件"

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
