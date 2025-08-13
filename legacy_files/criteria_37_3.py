import pandas as pd
import argparse
import time
import os

def get_component_list():
    """
    从 Excel 文件中提取元器件的边界框信息。

    读取 'parsed_tables_new.xlsx' 文件中的 'SYM_NAME' 工作表，
    筛选出 'SUBCLASS' 为 'PLACE_BOUND_TOP' 或 'PLACE_BOUND_BOTTOM' 的行，
    并为每个元器件（REFDES）在每个 SUBCLASS 下计算边界框。

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
    # 1. 构建 Excel 文件的绝对路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    excel_file_path = os.path.join(os.path.dirname(script_dir), 'parsed_tables_250804.xlsx')
    
    # 1. 从 Excel 文件读取数据
    try:
        df = pd.read_excel(excel_file_path, sheet_name='SYM_NAME')
    except FileNotFoundError:
        print(f"错误: 未找到 '{excel_file_path}' 文件。")
        return pd.DataFrame()
    except Exception as e:
        print(f"读取 Excel 文件时发生错误: {e}")
        return pd.DataFrame()

    # 2. 筛选行
    subclasses_to_keep = ['PLACE_BOUND_TOP', 'PLACE_BOUND_BOTTOM']
    filtered_df = df[df['SUBCLASS'].isin(subclasses_to_keep)].copy()

    # 将原始索引（行号）保存到一个新列中
    filtered_df.reset_index(inplace=True)
    # Excel 行号从1开始，pandas 索引从0开始，加2对齐（1为标题行）
    filtered_df['original_row'] = filtered_df['index'] + 2


    # 确保坐标数据列是数值类型
    for col in ['GRAPHIC_DATA_1', 'GRAPHIC_DATA_2', 'GRAPHIC_DATA_3', 'GRAPHIC_DATA_4']:
        filtered_df[col] = pd.to_numeric(filtered_df[col], errors='coerce')

    # 注意：根据第8条规则，不删除 NaN 值
    
    if filtered_df.empty:
        print("警告: 筛选后没有可处理的数据。")
        return pd.DataFrame(columns=['component_id', 'shape_name', 'min_x', 'min_y', 'max_x', 'max_y', 'layer'])

    # 3. 按 (REFDES, SUBCLASS) 分组并聚合计算边界框和获取 shape_name
    grouped = filtered_df.groupby(['REFDES', 'SUBCLASS'])
    
    # 4. 对每个分组分别计算边界框坐标和获取 shape_name
    agg_results = grouped.agg(
        original_row=('original_row', 'first'), # 获取每个组的第一个原始行号
        shape_name=('GRAPHIC_DATA_NAME', 'first'), # 获取每个组的第一个 GRAPHIC_DATA_NAME 值
        g1_min=('GRAPHIC_DATA_1', 'min'),
        g1_max=('GRAPHIC_DATA_1', 'max'),
        g2_min=('GRAPHIC_DATA_2', 'min'),
        g2_max=('GRAPHIC_DATA_2', 'max'),
        g3_min=('GRAPHIC_DATA_3', 'min'),
        g3_max=('GRAPHIC_DATA_3', 'max'),
        g4_min=('GRAPHIC_DATA_4', 'min'),
        g4_max=('GRAPHIC_DATA_4', 'max')
    )
    
    # 5. 计算最终的边界框坐标和 layer
    # 创建一个临时的 DataFrame 来处理 MultiIndex
    temp_df = agg_results.copy()
    temp_df['min_x'] = temp_df[['g1_min', 'g3_min']].min(axis=1)
    temp_df['min_y'] = temp_df[['g2_min', 'g4_min']].min(axis=1)
    temp_df['max_x'] = temp_df[['g1_max', 'g3_max']].max(axis=1)
    temp_df['max_y'] = temp_df[['g2_max', 'g4_max']].max(axis=1)
    temp_df['layer'] = temp_df.index.get_level_values('SUBCLASS')  # layer = 当前分组的 SUBCLASS
    temp_df['component_id'] = temp_df.index.get_level_values('REFDES')  # component_id = 当前分组的 REFDES
    
    # 6. 构建最终结果 DataFrame
    get_component_list_re = pd.DataFrame({
        'original_row': temp_df['original_row'],
        'component_id': temp_df['component_id'],
        'shape_name': temp_df['shape_name'],
        'min_x': temp_df['min_x'],
        'min_y': temp_df['min_y'],
        'max_x': temp_df['max_x'],
        'max_y': temp_df['max_y'],
        'layer': temp_df['layer']
    })

    # 7. 将 component_id 和 shape_name 设置为字符串类型
    get_component_list_re['component_id'] = get_component_list_re['component_id'].astype(str)
    get_component_list_re['shape_name'] = get_component_list_re['shape_name'].astype(str)

    # 8. 将原始行号设置为最终的索引并排序
    get_component_list_re.set_index('original_row', inplace=True)
    get_component_list_re.sort_index(inplace=True)
    get_component_list_re.index.name = None # 移除索引列的标题

    return get_component_list_re

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="从 Excel 文件提取元器件清单。")
    parser.add_argument('-f', '--full', action='store_true', help="完整显示所有行和列。")
    args = parser.parse_args()

    start_time = time.time()
    result_df = get_component_list()
    title = "🔍 criteria_37_3 - 获取元器件清单"

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
