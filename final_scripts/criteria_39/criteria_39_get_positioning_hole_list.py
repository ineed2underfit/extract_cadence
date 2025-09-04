import pandas as pd
import argparse
import time
import os


def get_positioning_hole_list():
    """
    从 Excel 文件中提取定位孔列表。

    读取 'parsed_tables_250804.xlsx' 文件中的 'SYM_NAME' 和 'PAD_NAME' 工作表，
    筛选出 'REFDES' 以 'M' 开头且 'SUBCLASS == 'BOTTOM'' 的行。

    返回:
        pandas.DataFrame: 包含以下字段的 DataFrame，并以原始行号为索引：
                          - hole_id (str): REFDES 列的值（以 M 开头且 SUBCLASS == 'BOTTOM'）
                          - diameter (float): 对应的钻孔直径
                          - x_position (float): GRAPHIC_DATA_1 列的值
                          - y_position (float): GRAPHIC_DATA_2 列的值
    """
    # 1. 构建 Excel 文件的绝对路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    excel_file_path = os.path.join(os.path.dirname(script_dir), 'parsed_tables_250804.xlsx')
    
    # 2. 从 Excel 文件读取数据
    try:
        df_sym = pd.read_excel(excel_file_path, sheet_name='SYM_NAME')
        df_pad = pd.read_excel(excel_file_path, sheet_name='PAD_NAME')
    except FileNotFoundError:
        print(f"错误: 未找到 '{excel_file_path}' 文件。")
        return pd.DataFrame()
    except Exception as e:
        print(f"读取 Excel 文件时发生错误: {e}")
        return pd.DataFrame()

    # 3. 筛选 SYM_NAME 表中的行 (REFDES 以 'M' 开头 且 SUBCLASS == 'BOTTOM')
    try:
        filtered_sym_df = df_sym[df_sym['REFDES'].str.startswith('M', na=False) & (df_sym['SUBCLASS'] == 'BOTTOM')].copy()
    except Exception as e:
        print(f"筛选 SYM_NAME 数据时发生错误: {e}")
        return pd.DataFrame()

    # 4. 检查是否有数据
    if filtered_sym_df.empty:
        print("警告: 筛选后没有可处理的数据。")
        return pd.DataFrame(columns=['hole_id', 'diameter', 'x_position', 'y_position'])

    # 5. 保留原始索引（行号）
    filtered_sym_df.reset_index(inplace=True)
    # Excel 行号从1开始，pandas 索引从0开始，加2对齐（1为标题行）
    filtered_sym_df['original_row'] = filtered_sym_df['index'] + 2

    # 6. 获取 diameter 值
    # 对于每个 hole_id，在 SYM_NAME 工作表中找到对应行的 PAD_STACK_NAME 值
    # 在 PAD_NAME 工作表中查找 PAD_NAME 等于该值，且 LAYER 列包含 'DRILL' 的记录
    # 取其匹配行的 PADWIDTH 的值作为 diameter
    
    # 初始化 diameter 列为 NaN
    filtered_sym_df['diameter'] = pd.NA
    
    # 遍历筛选后的每一行，查找对应的 diameter
    for idx, row in filtered_sym_df.iterrows():
        pad_stack_name = row['PAD_STACK_NAME']
        if pd.notna(pad_stack_name):
            # 在 PAD_NAME 中查找匹配的记录
            matching_pads = df_pad[(df_pad['PAD_NAME'] == pad_stack_name) & 
                                   (df_pad['LAYER'].str.contains('DRILL', na=False))]
            if not matching_pads.empty:
                # 取第一个匹配项的 PADWIDTH 作为 diameter
                diameter = matching_pads.iloc[0]['PADWIDTH']
                filtered_sym_df.at[idx, 'diameter'] = diameter

    # 7. 构建最终结果 DataFrame
    get_positioning_hole_list_re = pd.DataFrame({
        'original_row': filtered_sym_df['original_row'],
        'hole_id': filtered_sym_df['REFDES'],
        'diameter': filtered_sym_df['diameter'],
        'x_position': filtered_sym_df['GRAPHIC_DATA_1'],
        'y_position': filtered_sym_df['GRAPHIC_DATA_2']
    })

    # 8. 将原始行号设置为最终的索引并排序
    get_positioning_hole_list_re.set_index('original_row', inplace=True)
    get_positioning_hole_list_re.sort_index(inplace=True)
    get_positioning_hole_list_re.index.name = None  # 移除索引列的标题

    return get_positioning_hole_list_re


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="从 Excel 文件提取定位孔列表。")
    parser.add_argument('-f', '--full', action='store_true', help="完整显示所有行和列。")
    args = parser.parse_args()

    start_time = time.time()
    result_df = get_positioning_hole_list()
    title = "🔍 criteria_39 - 获取定位孔列表"

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