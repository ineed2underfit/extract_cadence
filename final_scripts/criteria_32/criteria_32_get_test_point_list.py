import pandas as pd
import time
import argparse
import os

def get_test_point_list():
    """
    从 Excel 文件中提取测试点列表信息。
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

    # 1. Apply all filtering conditions
    filtered_df = df[
        (df['SUBCLASS'].isin(['SOLDERMASK_TOP', 'SOLDERMASK_BOTTOM'])) &
        (df['CLASS'] == 'PIN') &
        (df['REFDES'].str.startswith('TP', na=False))
    ].copy()

    # 2. Build the new DataFrame with the required format
    get_test_point_list_re = pd.DataFrame({
        'original_row': filtered_df['_original_index'] + 2,
        'testpoint_id': filtered_df['REFDES'].astype(str),
        'net_name': filtered_df['NET_NAME'].astype(str),
        'shape_name': filtered_df['GRAPHIC_DATA_NAME'].astype(str),
        'x': filtered_df['GRAPHIC_DATA_1'].astype(float),
        'y': filtered_df['GRAPHIC_DATA_2'].astype(float),
        'width': filtered_df['GRAPHIC_DATA_3'].astype(float),
        'height': filtered_df['GRAPHIC_DATA_4'].astype(float),
        'layer': filtered_df['SUBCLASS'].astype(str)
    })
    
    # 仿照模板，将原始行号作为索引，并排序
    get_test_point_list_re.set_index('original_row', inplace=True)
    get_test_point_list_re.sort_index(inplace=True)
    get_test_point_list_re.index.name = None # 清除索引名称

    return get_test_point_list_re

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="从 Excel 文件提取测试点清单。")
    parser.add_argument('-f', '--full', action='store_true', help="完整显示所有行和列。")
    args = parser.parse_args()

    start_time = time.time()
    result_df = get_test_point_list()
    title = "🔍 criteria_32_get_connector_list - 获取测试点清单"

    if result_df is not None and not result_df.empty:
        print("\n==================================================")
        print(f" {title}")
        if args.full:
            print(" Mode: Full Mode (--full)")
            print("==================================================")
            # 设置 pandas 显示选项以完整显示
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
