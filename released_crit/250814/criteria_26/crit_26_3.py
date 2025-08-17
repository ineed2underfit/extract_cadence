import pandas as pd
import argparse
import time
import os


def get_mounting_hole_network_name():
    """
    从 Excel 文件中提取安装孔网络名称信息。

    读取 'parsed_tables_250804.xlsx' 文件中的 'SYM_NAME' 工作表，
    筛选出 'REFDES' 以 'M' 开头且 'SUBCLASS == 'BOTTOM'' 的行。

    返回:
        pandas.DataFrame: 包含以下字段的 DataFrame，并以原始行号为索引：
                          - hole_id (str): REFDES 列的值（以 M 开头且 SUBCLASS == 'BOTTOM'）
                          - net_name (str): NET_NAME 列的值
    """
    # 1. 构建 Excel 文件的绝对路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    excel_file_path = os.path.join(os.path.dirname(script_dir), 'parsed_tables_250804.xlsx')
    
    # 2. 从 Excel 文件读取数据
    try:
        df_sym = pd.read_excel(excel_file_path, sheet_name='SYM_NAME')
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
        return pd.DataFrame(columns=['hole_id', 'net_name'])

    # 5. 保留原始索引（行号）
    filtered_sym_df.reset_index(inplace=True)
    # Excel 行号从1开始，pandas 索引从0开始，加2对齐（1为标题行）
    filtered_sym_df['original_row'] = filtered_sym_df['index'] + 2

    # 6. 构建最终结果 DataFrame
    get_mounting_hole_network_name_re = pd.DataFrame({
        'original_row': filtered_sym_df['original_row'],
        'hole_id': filtered_sym_df['REFDES'],
        'net_name': filtered_sym_df['NET_NAME']
    })

    # 7. 将原始行号设置为最终的索引并排序
    get_mounting_hole_network_name_re.set_index('original_row', inplace=True)
    get_mounting_hole_network_name_re.sort_index(inplace=True)
    get_mounting_hole_network_name_re.index.name = None  # 移除索引列的标题

    return get_mounting_hole_network_name_re


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="从 Excel 文件提取安装孔网络名称信息。")
    parser.add_argument('-f', '--full', action='store_true', help="完整显示所有行和列。")
    args = parser.parse_args()

    start_time = time.time()
    result_df = get_mounting_hole_network_name()
    title = "🔍 criteria_26_3 - 获取安装孔网络名称"

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