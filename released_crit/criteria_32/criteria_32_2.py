import pandas as pd
import argparse
import time
import os

def get_connector_list():
    """
    从 Excel 文件中提取连接器列表信息。

    读取 'parsed_tables_250804.xlsx' 文件中的 'SYM_NAME' 工作表，
    筛选出 'REFDES' 以 'XP' 开头且所有需要的列均非 NaN 的行。

    返回:
        pandas.DataFrame: 包含以下字段的 DataFrame，并以原始行号为索引：
                          - connector_id (str): 由 REFDES 和 PIN_NUMBER 的值用下划线 _ 拼接而成。
                          - net_name (str): NET_NAME 列的值。
                          - shape_name (str): GRAPHIC_DATA_NAME 列的值。
                          - layer (str): SUBCLASS 列的值。
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

    # 2. 筛选行 (REFDES 以 'XP' 开头)
    try:
        filtered_df = df[df['REFDES'].str.startswith('XP', na=False)].copy()
    except Exception as e:
        print(f"筛选数据时发生错误: {e}")
        return pd.DataFrame()

    # 3. 检查是否有数据
    if filtered_df.empty:
        print("警告: 筛选后没有可处理的数据。")
        return pd.DataFrame(columns=['connector_id', 'net_name', 'shape_name', 'layer'])

    # 4. 保留原始索引（行号）
    filtered_df.reset_index(inplace=True)
    # Excel 行号从1开始，pandas 索引从0开始，加2对齐（1为标题行）
    filtered_df['original_row'] = filtered_df['index'] + 2

    # 5. 只保留所有需要的列均非 NaN 的行
    required_columns = ['REFDES', 'PIN_NUMBER', 'NET_NAME', 'GRAPHIC_DATA_NAME', 'SUBCLASS']
    filtered_df = filtered_df.dropna(subset=required_columns)

    # 6. 检查删除 NaN 后是否还有数据
    if filtered_df.empty:
        print("警告: 删除包含 NaN 的行后没有可处理的数据。")
        return pd.DataFrame(columns=['connector_id', 'net_name', 'shape_name', 'layer'])

    # 7. 构建 connector_id: 由 REFDES 和 PIN_NUMBER 拼接而成
    # 注意：这里我们不再将 NaN 替换为 pd.NA，因为前面已经删除了包含 NaN 的行
    connector_id = filtered_df['REFDES'].astype(str) + '_' + filtered_df['PIN_NUMBER'].astype(str)

    # 8. 构建最终结果 DataFrame
    get_connector_list_re = pd.DataFrame({
        'original_row': filtered_df['original_row'],
        'connector_id': connector_id,
        'net_name': filtered_df['NET_NAME'],
        'shape_name': filtered_df['GRAPHIC_DATA_NAME'],
        'layer': filtered_df['SUBCLASS']
    })

    # 9. 将原始行号设置为最终的索引并排序
    get_connector_list_re.set_index('original_row', inplace=True)
    get_connector_list_re.sort_index(inplace=True)
    get_connector_list_re.index.name = None # 移除索引列的标题

    return get_connector_list_re

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="从 Excel 文件提取连接器清单。")
    parser.add_argument('-f', '--full', action='store_true', help="完整显示所有行和列。")
    args = parser.parse_args()

    start_time = time.time()
    result_df = get_connector_list()
    title = "🔍 criteria_32_2 - 获取连接器清单"

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