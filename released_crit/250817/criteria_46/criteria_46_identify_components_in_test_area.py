
import pandas as pd
import numpy as np
import argparse
import time
import os
import sys

# 动态地将父目录添加到 sys.path，以便导入兄弟模块
try:
    # 获取当前脚本所在的目录 (criteria_46)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 获取父目录 (final_scripts)
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)
    # 从兄弟目录 criteria_46 中导入 get_connector_list 函数
    from criteria_46.criteria_46_get_connector_list import get_connector_list
except (ImportError, NameError) as e:
    print(f"错误：无法导入依赖的 get_connector_list 函数: {e}")
    print("请确保 criteria_46_get_connector_list.py 文件存在于同一个 criteria_46 文件夹下。")
    # 在无法导入时提供一个虚拟函数，以便程序能继续执行并提示错误，而不是直接崩溃
    def get_connector_list():
        print("错误：get_connector_list 依赖未能加载，将返回空结果。")
        return pd.DataFrame(columns=['connector_id', 'x_min', 'y_min', 'x_max', 'y_max'])

def calculate_component_boundaries():
    """
    从Excel的SYM_NAME工作表中提取所有元件(component)的边界信息。
    """
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        excel_file_path = os.path.join(os.path.dirname(script_dir), 'parsed_tables_250804.xlsx')
    except NameError:
        excel_file_path = r'E:\pycharm_projects\testability_projects\extract_cadence\final_scripts\parsed_tables_250804.xlsx'

    try:
        df = pd.read_excel(excel_file_path, sheet_name='SYM_NAME')
    except Exception as e:
        print(f"读取Excel文件时发生错误: {e}")
        return pd.DataFrame()

    condition = (
        df['SUBCLASS'].isin(['PLACE_BOUND_TOP', 'PLACE_BOUND_BOTTOM']) &
        df['GRAPHIC_DATA_NAME'].isin(['LINE', 'RECTANGLE'])
    )
    filtered_df = df[condition].copy()

    if filtered_df.empty:
        return pd.DataFrame()

    coord_cols = ['GRAPHIC_DATA_1', 'GRAPHIC_DATA_2', 'GRAPHIC_DATA_3', 'GRAPHIC_DATA_4']
    for col in coord_cols:
        filtered_df[col] = pd.to_numeric(filtered_df[col], errors='coerce')

    rect_df = filtered_df[filtered_df['GRAPHIC_DATA_NAME'] == 'RECTANGLE'].copy()
    line_df = filtered_df[filtered_df['GRAPHIC_DATA_NAME'] == 'LINE'].copy()

    processed_results = []

    if not rect_df.empty:
        rect_df['comp_x_min'] = np.minimum(rect_df['GRAPHIC_DATA_1'], rect_df['GRAPHIC_DATA_3'])
        rect_df['comp_y_min'] = np.minimum(rect_df['GRAPHIC_DATA_2'], rect_df['GRAPHIC_DATA_4'])
        rect_df['comp_x_max'] = np.maximum(rect_df['GRAPHIC_DATA_1'], rect_df['GRAPHIC_DATA_3'])
        rect_df['comp_y_max'] = np.maximum(rect_df['GRAPHIC_DATA_2'], rect_df['GRAPHIC_DATA_4'])
        processed_results.append(rect_df[['REFDES', 'comp_x_min', 'comp_y_min', 'comp_x_max', 'comp_y_max']])

    if not line_df.empty:
        x_coords = pd.concat([line_df[['REFDES', 'GRAPHIC_DATA_1']].rename(columns={'GRAPHIC_DATA_1': 'x'}), line_df[['REFDES', 'GRAPHIC_DATA_3']].rename(columns={'GRAPHIC_DATA_3': 'x'})])
        y_coords = pd.concat([line_df[['REFDES', 'GRAPHIC_DATA_2']].rename(columns={'GRAPHIC_DATA_2': 'y'}), line_df[['REFDES', 'GRAPHIC_DATA_4']].rename(columns={'GRAPHIC_DATA_4': 'y'})])
        x_bounds = x_coords.groupby('REFDES')['x'].agg(['min', 'max']).rename(columns={'min': 'comp_x_min', 'max': 'comp_x_max'})
        y_bounds = y_coords.groupby('REFDES')['y'].agg(['min', 'max']).rename(columns={'min': 'comp_y_min', 'max': 'comp_y_max'})
        line_meta = line_df[['REFDES']].drop_duplicates(subset=['REFDES']).set_index('REFDES')
        line_processed = line_meta.join(x_bounds).join(y_bounds).reset_index()
        processed_results.append(line_processed)

    if not processed_results:
        return pd.DataFrame()

    return pd.concat(processed_results, ignore_index=True).rename(columns={'REFDES': 'component_id'})

def identify_components_in_test_area():
    """
    识别每个连接器测试区域内的所有元件。
    """
    print("步骤 1/3: 从 criteria_46_get_connector_list 获取连接器数据...")
    connectors_df = get_connector_list()
    if connectors_df.empty:
        print("警告: 未能获取到连接器数据，无法继续。")
        return pd.DataFrame()

    print("步骤 2/3: 计算所有元件的边界...")
    components_df = calculate_component_boundaries()
    if components_df.empty:
        print("警告: 未能计算出任何元件的边界，无法继续。")
        return pd.DataFrame()

    print("步骤 3/3: 交叉匹配连接器测试区域与元件...")
    expansion_distance = 787.0

    # 计算测试区域
    connectors_df['test_x_min'] = connectors_df['x_min'] - expansion_distance
    connectors_df['test_y_min'] = connectors_df['y_min'] - expansion_distance
    connectors_df['test_x_max'] = connectors_df['x_max'] + expansion_distance
    connectors_df['test_y_max'] = connectors_df['y_max'] + expansion_distance

    # 使用 cross join 创建所有可能的组合
    connectors_df['_key'] = 1
    components_df['_key'] = 1
    combined_df = pd.merge(connectors_df, components_df, on='_key').drop('_key', axis=1)

    # 筛选出所有相交的组合
    intersect_condition = (
        (combined_df['test_x_min'] < combined_df['comp_x_max']) &
        (combined_df['test_x_max'] > combined_df['comp_x_min']) &
        (combined_df['test_y_min'] < combined_df['comp_y_max']) &
        (combined_df['test_y_max'] > combined_df['comp_y_min'])
    )
    intersected_df = combined_df[intersect_condition].copy()

    if intersected_df.empty:
        print("完成：在所有连接器的测试区域内均未发现重叠元件。")
        return pd.DataFrame()

    # 格式化最终输出
    get_connector_list_re = pd.DataFrame()
    get_connector_list_re['connector_id'] = intersected_df['connector_id']
    get_connector_list_re['component_id'] = intersected_df['component_id']
    get_connector_list_re['expansion_distance'] = expansion_distance
    # 应用新的格式化规则：保留4位小数，并用", "连接
    get_connector_list_re['test_area_min_xy'] = intersected_df['test_x_min'].round(4).astype(str) + ',' + intersected_df['test_y_min'].round(4).astype(str)
    get_connector_list_re['test_area_max_xy'] = intersected_df['test_x_max'].round(4).astype(str) + ',' + intersected_df['test_y_max'].round(4).astype(str)
    get_connector_list_re['component_min_xy'] = intersected_df['comp_x_min'].round(4).astype(str) + ',' + intersected_df['comp_y_min'].round(4).astype(str)
    get_connector_list_re['component_max_xy'] = intersected_df['comp_x_max'].round(4).astype(str) + ',' + intersected_df['comp_y_max'].round(4).astype(str)
    
    # 保留原始索引（这里以connector的原始索引为准）
    get_connector_list_re.index = intersected_df.index

    return get_connector_list_re

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="识别连接器测试区域内的所有元件。")
    parser.add_argument('-f', '--full', action='store_true', help="完整显示所有行和列。")
    args = parser.parse_args()

    start_time = time.time()
    result_df = identify_components_in_test_area()
    title = "🎯 criteria_46 - 识别测试区域内的元件"

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
