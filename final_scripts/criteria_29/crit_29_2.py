import pandas as pd
import argparse
import time
import os

def get_connector_pin_list():
    """
    从 Excel 文件中提取连接器引脚列表信息。

    读取 'parsed_tables_250804.xlsx' 文件中的 'SYM_NAME' 工作表，
    按以下规则提取数据：
    1. connector_id: REFDES 列中以 XP 开头的值（与 CLASS、SUBCLASS 无关）
    2. pin_id: 由 REFDES 和 PIN_NUMBER 的值用下划线 _ 拼接而成（仅当 CLASS 为 PIN 且 SUBCLASS 为 TOP 或 BOTTOM 时）
    3. net_name: NET_NAME 列的值
    4. layer: SUBCLASS 列的值

    返回:
        pandas.DataFrame: 包含以下字段的 DataFrame，并以原始行号为索引：
                          - connector_id (str): REFDES 列的值（以XP开头）。
                          - pin_id (str): 由 REFDES 和 PIN_NUMBER 的值用下划线 _ 拼接而成。
                          - net_name (str): NET_NAME 列的值。
                          - layer (str): SUBCLASS 列的值。
    """
    # 构建相对于脚本文件所在目录的绝对路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    excel_file = os.path.join(script_dir, '..', 'parsed_tables_250804.xlsx')
    
    try:
        df = pd.read_excel(excel_file, sheet_name='SYM_NAME', engine='openpyxl')
    except FileNotFoundError:
        print(f"错误：无法找到文件 '{excel_file}'。请确保文件在正确的目录中。")
        return pd.DataFrame()
    except Exception as e:
        print(f"读取 Excel 文件时发生错误: {e}")
        return pd.DataFrame()

    # 保留原始行号，以便追溯
    df.reset_index(inplace=True)
    df.rename(columns={'index': '_original_index'}, inplace=True)

    # 1. 构建 connector_id: REFDES 列中以 XP 开头的值（与 CLASS、SUBCLASS 无关）
    connector_id = df['REFDES'].where(df['REFDES'].str.startswith('XP', na=False))

    # 2. 构建 pin_id: 由 REFDES 和 PIN_NUMBER 的值用下划线 _ 拼接而成
    # 仅当 CLASS 为 PIN 且 SUBCLASS 为 TOP 或 BOTTOM 时才生成
    pin_condition = (df['CLASS'] == 'PIN') & (df['SUBCLASS'].isin(['TOP', 'BOTTOM']))
    pin_id = df['REFDES'].astype(str) + '_' + df['PIN_NUMBER'].astype(str)
    pin_id = pin_id.where(pin_condition, pd.NA)

    # 3. 构建 net_name: 直接使用 NET_NAME 列的值
    net_name = df['NET_NAME']

    # 4. 构建 layer: 直接使用 SUBCLASS 列的值
    layer = df['SUBCLASS']

    # 5. 构建最终结果 DataFrame
    get_connector_pin_list_re = pd.DataFrame({
        'original_row': df['_original_index'] + 2,
        'connector_id': connector_id,
        'pin_id': pin_id,
        'net_name': net_name,
        'layer': layer
    })
    
    # 6. 过滤掉 connector_id 和 pin_id 都为空的行
    get_connector_pin_list_re = get_connector_pin_list_re[
        ~(get_connector_pin_list_re['connector_id'].isna() & get_connector_pin_list_re['pin_id'].isna())
    ]
    
    # 7. 保持原始数据行顺序，不重新编号或排序
    get_connector_pin_list_re.set_index('original_row', inplace=True)
    get_connector_pin_list_re.index.name = None # 清除索引名称

    return get_connector_pin_list_re

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="从 Excel 文件提取连接器引脚清单。")
    parser.add_argument('-f', '--full', action='store_true', help="完整显示所有行和列。")
    args = parser.parse_args()

    start_time = time.time()
    result_df = get_connector_pin_list()
    title = "🔍 criteria_29_2 - 获取连接器引脚清单"

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