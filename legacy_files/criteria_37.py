import pandas as pd
import argparse
import time

def get_component_list():
    """
    从 Excel 文件中提取元器件的边界框信息。

    读取 'parsed_tables_new.xlsx' 文件中的 'SYM_NAME' 工作表，
    筛选出 'SUBCLASS' 为 'PLACE_BOUND_TOP' 或 'PLACE_BOUND_BOTTOM' 的行，
    并为每个元器件（REFDES）计算边界框。

    返回:
        pandas.DataFrame: 包含以下字段的 DataFrame，并以原始行号为索引：
                          - component_id (str): 元器件的 REFDES。
                          - min_x (float): 最小 X 坐标。
                          - min_y (float): 最小 Y 坐标。
                          - max_x (float): 最大 X 坐标。
                          - max_y (float): 最大 Y 坐标。
    """
    # 1. 从 Excel 文件读取数据
    try:
        df = pd.read_excel('final_scripts/parsed_tables_250804.xlsx', sheet_name='SYM_NAME')
    except FileNotFoundError:
        print("错误: 未找到 'parsed_tables_250804.xlsx' 文件。")
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

    # 删除转换后在坐标数据列中包含 NaN 的行
    filtered_df.dropna(subset=['GRAPHIC_DATA_1', 'GRAPHIC_DATA_2', 'GRAPHIC_DATA_3', 'GRAPHIC_DATA_4'], inplace=True)

    if filtered_df.empty:
        print("警告: 筛选后没有可处理的数据。")
        return pd.DataFrame(columns=['component_id', 'min_x', 'min_y', 'max_x', 'max_y'])

    # 3. 按 REFDES 分组并聚合计算边界框，同时获取第一个原始行号
    grouped = filtered_df.groupby('REFDES')
    agg_results = grouped.agg(
        original_row=('original_row', 'first'), # 获取每个组的第一个原始行号
        g1_min=('GRAPHIC_DATA_1', 'min'),
        g1_max=('GRAPHIC_DATA_1', 'max'),
        g2_min=('GRAPHIC_DATA_2', 'min'),
        g2_max=('GRAPHIC_DATA_2', 'max'),
        g3_min=('GRAPHIC_DATA_3', 'min'),
        g3_max=('GRAPHIC_DATA_3', 'max'),
        g4_min=('GRAPHIC_DATA_4', 'min'),
        g4_max=('GRAPHIC_DATA_4', 'max')
    )

    # 4. 计算最终的边界框坐标
    get_component_list_re = pd.DataFrame({
        'original_row': agg_results['original_row'],
        'min_x': agg_results[['g1_min', 'g3_min']].min(axis=1),
        'min_y': agg_results[['g2_min', 'g4_min']].min(axis=1),
        'max_x': agg_results[['g1_max', 'g3_max']].max(axis=1),
        'max_y': agg_results[['g2_max', 'g4_max']].max(axis=1)
    })

    # 5. 重命名字段并设置 component_id 类型
    get_component_list_re.reset_index(inplace=True)
    get_component_list_re = get_component_list_re.rename(columns={'REFDES': 'component_id'})
    get_component_list_re['component_id'] = get_component_list_re['component_id'].astype(str)

    # 6. 将原始行号设置为最终的索引并排序
    get_component_list_re.set_index('original_row', inplace=True)
    get_component_list_re.sort_index(inplace=True)
    get_component_list_re.index.name = None # 移除索引列的标题

    return get_component_list_re

if __name__ == '__main__':
    # --- 记录开始时间 ---
    start_time = time.time()

    # --- 使用 argparse 处理命令行参数 ---
    parser = argparse.ArgumentParser(description="从 Excel 文件提取元器件清单。")
    parser.add_argument('-f', '--full', action='store_true', help="显示完整的输出，而不是省略版本。")
    args = parser.parse_args()

    try:
        get_component_list_re = get_component_list()

        if not get_component_list_re.empty:
            if args.full:
                # --- 完整模式 ---
                print("--- criteria_37 获取元器件清单 ---")
                print("--- (Full Mode) ---")
                pd.set_option('display.max_rows', None)
                pd.set_option('display.max_columns', None)
            else:
                # --- 默认省略模式 ---
                print("--- criteria_37 获取元器件清单 ---")
                print("--- (Default Mode, use -f or --full to show all) ---")

            # --- 打印 DataFrame (恢复默认行为，以支持省略模式) ---
            print(get_component_list_re)

            if args.full:
                print(f"\n[{get_component_list_re.shape[0]} rows x {get_component_list_re.shape[1]} columns]")
            
            # print("--------------------")

    except (FileNotFoundError, IOError) as e:
        print(e)
    except Exception as e:
        print(f"发生未知错误: {e}")
    finally:
        # --- 计算并打印总运行时间 ---
        end_time = time.time()
        print(f"Total script runtime: {end_time - start_time:.2f} seconds\n")
