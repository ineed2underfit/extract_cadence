import pandas as pd
import argparse
import time
import os

def get_component_list():
    """
    从 Excel 文件中提取并处理元器件的边界框信息。

    读取 'parsed_tables_250804.xlsx' 文件中的 'SYM_NAME' 工作表，
    根据特定规则筛选和分组数据，并为每个元器件在每个层（SUBCLASS）上计算边界框。

    提取规则:
    1. 从 Excel 文件 parsed_tables_250804.xlsx 中的工作表 `SYM_NAME`读取数据；
    2. 仅保留 `SUBCLASS`字段为 "`PLACE_BOUND_TOP`" 或 "`PLACE_BOUND_BOTTOM`" 的行；
    3. 剔除 `GRAPHIC_DATA_NAME` 列值等于`TEXT` 的所有行;
    4. 按 `(REFDES, SUBCLASS)` 分组；
    5. 对每个分组分别计算：
        - `min_x` = min(该组所有 `GRAPHIC_DATA_1` 与 `GRAPHIC_DATA_3` 的值)；
        - `min_y` = min(该组所有 `GRAPHIC_DATA_2` 与 `GRAPHIC_DATA_4` 的值)；
        - `max_x` = max(该组所有 `GRAPHIC_DATA_1` 与 `GRAPHIC_DATA_3` 的值)；
        - `max_y` = max(该组所有 `GRAPHIC_DATA_2` 与 `GRAPHIC_DATA_4` 的值)；
    6. 生成结果 DataFrame，并以原始行号为索引。

    返回:
        pandas.DataFrame: 包含以下字段的 DataFrame，并以原始行号为索引：
                          - component_id (str): 元器件的 REFDES。
                          - shape_name (str): 对应字段 GRAPHIC_DATA_NAME 的值。
                          - min_x (float): 最小 X 坐标。
                          - min_y (float): 最小 Y 坐标。
                          - max_x (float): 最大 X 坐标。
                          - max_y (float): 最大 Y 坐标。
                          - layer (str): 当前分组的 SUBCLASS 值。
    """
    # 构建 Excel 文件的绝对路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    excel_file_path = os.path.join(os.path.dirname(script_dir), 'parsed_tables_250804.xlsx')

    # 1. 从 Excel 文件读取数据
    try:
        df = pd.read_excel(excel_file_path, sheet_name='SYM_NAME')
    except FileNotFoundError:
        print(f"错误: 未找到 '{excel_file_path}' 文件。请确保它位于正确的路径下。")
        return pd.DataFrame()
    except Exception as e:
        print(f"读取 Excel 文件时发生错误: {e}")
        return pd.DataFrame()

    # 确保坐标数据列是数值类型，转换失败则设为 NaN
    for col in ['GRAPHIC_DATA_1', 'GRAPHIC_DATA_2', 'GRAPHIC_DATA_3', 'GRAPHIC_DATA_4']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # 2. 筛选 `SUBCLASS`
    subclasses_to_keep = ['PLACE_BOUND_TOP', 'PLACE_BOUND_BOTTOM']
    filtered_df = df[df['SUBCLASS'].isin(subclasses_to_keep)].copy()

    # 3. 剔除 `GRAPHIC_DATA_NAME` 为 'TEXT' 的行
    filtered_df = filtered_df[filtered_df['GRAPHIC_DATA_NAME'] != 'TEXT']
    
    # 保存原始行号
    filtered_df.reset_index(inplace=True)
    # Excel行号从1开始，pandas索引从0开始，加2对齐（1为标题行）
    filtered_df['original_row'] = filtered_df['index'] + 2

    # 如果筛选后为空，则返回空 DataFrame
    if filtered_df.empty:
        print("警告: 筛选后没有可处理的数据。")
        return pd.DataFrame(columns=['component_id', 'shape_name', 'min_x', 'min_y', 'max_x', 'max_y', 'layer'])

    # 4. 按 (REFDES, SUBCLASS) 分组
    grouped = filtered_df.groupby(['REFDES', 'SUBCLASS'])

    # 5. 定义聚合计算函数
    def calculate_bounds(group):
        x_coords = pd.concat([group['GRAPHIC_DATA_1'], group['GRAPHIC_DATA_3']], ignore_index=True)
        y_coords = pd.concat([group['GRAPHIC_DATA_2'], group['GRAPHIC_DATA_4']], ignore_index=True)
        
        x_bounds = x_coords.agg(['min', 'max'])
        y_bounds = y_coords.agg(['min', 'max'])

        result = {
            'min_x': x_bounds['min'],
            'max_x': x_bounds['max'],
            'min_y': y_bounds['min'],
            'max_y': y_bounds['max'],
            'shape_name': group['GRAPHIC_DATA_NAME'].iloc[0] if not group.empty else None,
            'original_row': group['original_row'].iloc[0] if not group.empty else None
        }
        return pd.Series(result)

    # 应用聚合函数
    agg_results = grouped.apply(calculate_bounds)

    # 6. 构建最终结果 DataFrame
    get_component_list_re = agg_results.reset_index()

    # 重命名字段
    get_component_list_re.rename(columns={'REFDES': 'component_id', 'SUBCLASS': 'layer'}, inplace=True)

    # 7. 调整字段类型
    get_component_list_re['component_id'] = get_component_list_re['component_id'].astype(str)
    get_component_list_re['shape_name'] = get_component_list_re['shape_name'].astype(str)
    
    # 8. 将原始行号设置为最终的索引并排序
    if 'original_row' in get_component_list_re.columns:
        get_component_list_re['original_row'] = pd.to_numeric(get_component_list_re['original_row'])
        get_component_list_re.set_index('original_row', inplace=True)
        get_component_list_re.sort_index(inplace=True)
        get_component_list_re.index.name = None
    
    final_columns = ['component_id', 'shape_name', 'min_x', 'min_y', 'max_x', 'max_y', 'layer']
    get_component_list_re = get_component_list_re[final_columns]

    return get_component_list_re

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="从 Excel 文件提取元器件清单。" )
    parser.add_argument('-f', '--full', action='store_true', help="完整显示所有行和列。" )
    args = parser.parse_args()

    start_time = time.time()
    result_df = get_component_list()
    title = "🔍 criteria_37_get_component_list - 获取元器件清单"

    if result_df is not None and not result_df.empty:
        print("==================================================")
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
