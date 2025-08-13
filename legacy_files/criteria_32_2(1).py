'''gemini'''
import pandas as pd
import argparse
import time
import os

def get_connector_list_re():
    """
    从 Excel 文件中提取符合特定规则的连接器列表。

    返回:
        pandas.DataFrame: 包含以下字段的 DataFrame:
                          - connector_id (str): 由 REFDES 和 PIN_NUMBER 拼接而成 (例如 XP2_1)。
                          - net_name (str): NET_NAME 列的值。
                          - shape_name (str): GRAPHIC_DATA_NAME 列的值。
                          - layer (str): SUBCLASS 列的值。
    """
    # 1. 构建 Excel 文件的绝对路径
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        excel_file_path = os.path.join(os.path.dirname(script_dir), 'parsed_tables_250804.xlsx')
    except NameError:
        # 在非脚本环境（如Jupyter）中运行时的备用路径
        excel_file_path = r'/final_scripts/parsed_tables_250804.xlsx'


    # 2. 从 Excel 文件读取数据
    try:
        df = pd.read_excel(excel_file_path, sheet_name='SYM_NAME')
    except FileNotFoundError:
        print(f"错误: 未找到 '{excel_file_path}' 文件。")
        return pd.DataFrame()
    except Exception as e:
        print(f"读取 Excel 文件时发生错误: {e}")
        return pd.DataFrame()

    # 3. 筛选行 (REFDES 以 'XP' 开头)
    try:
        filtered_df = df[df['REFDES'].str.startswith('XP', na=False)].copy()
    except KeyError:
        print("错误: 'REFDES' 列不存在。")
        return pd.DataFrame()
    except Exception as e:
        print(f"筛选数据时发生错误: {e}")
        return pd.DataFrame()

    # 4. 检查是否有数据
    if filtered_df.empty:
        print("警告: 筛选后没有可处理的数据 (没有找到 REFDES 以 'XP' 开头的行)。")
        return pd.DataFrame(columns=['connector_id', 'net_name', 'shape_name', 'layer'])

    # 5. 构建 connector_id
    # 将 REFDES 和 PIN_NUMBER 转为字符串以正确处理 NaN
    filtered_df['REFDES_str'] = filtered_df['REFDES'].astype(str)
    filtered_df['PIN_NUMBER_str'] = filtered_df['PIN_NUMBER'].astype(str)
    
    # 当 PIN_NUMBER 是 NaN 时，astype(str) 会变成 'nan'。如果想保持为空，可以先 fillna('')
    # filtered_df['PIN_NUMBER_str'] = filtered_df['PIN_NUMBER'].fillna('').astype(str)

    filtered_df['connector_id'] = filtered_df['REFDES_str'] + '_' + filtered_df['PIN_NUMBER_str']


    # 6. 构建最终结果 DataFrame
    get_connector_list_re = pd.DataFrame({
        'connector_id': filtered_df['connector_id'],
        'net_name': filtered_df['NET_NAME'],
        'shape_name': filtered_df['GRAPHIC_DATA_NAME'],
        'layer': filtered_df['SUBCLASS']
    })
    
    # 7. 确保数据类型正确
    for col in get_connector_list_re.columns:
        get_connector_list_re[col] = get_connector_list_re[col].astype(str)


    return get_connector_list_re

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="从 Excel 文件提取连接器清单 (重构版)。")
    parser.add_argument('-f', '--full', action='store_true', help="完整显示所有行和列。")
    args = parser.parse_args()

    start_time = time.time()
    # 调用更新后的函数
    result_df = get_connector_list_re()
    # 更新标题
    title = "🔍 criteria_32_re - 获取连接器清单 (REFDES+PIN)"

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
