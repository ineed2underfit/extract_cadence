import pandas as pd
import time
import argparse
import numpy as np

def get_component_pins_info():
    """
    从 Excel 文件中提取元器件焊盘信息。
    """
    excel_file = '../parsed_tables_250804.xlsx'
    try:
        df = pd.read_excel(excel_file, sheet_name='SYM_NAME', engine='openpyxl')
    except FileNotFoundError:
        print(f"错误：无法找到文件 '{excel_file}'。请确保文件在当前目录中。")
        return pd.DataFrame()
    except Exception as e:
        print(f"读取 Excel 文件时发生错误: {e}")
        return pd.DataFrame()

    df.reset_index(inplace=True)
    df.rename(columns={'index': '_original_index'}, inplace=True)

    # 筛选条件
    filtered_df = df[
        (df['CLASS'] == 'PIN') &
        (df['SUBCLASS'].isin(['TOP', 'BOTTOM']))
    ].copy()

    # 创建新的 DataFrame
    get_component_pins_info_re = pd.DataFrame({
        'original_row': filtered_df['_original_index'] + 2,
        'component_id': filtered_df['REFDES'].astype(str),
        'pin_id': filtered_df['REFDES'].astype(str) + '_' + filtered_df['PIN_NUMBER'].astype(str),
        'PAD_STACK_NAME': filtered_df['PAD_STACK_NAME'].astype(str),
        'PAD_SHAPE_NAME': filtered_df['PAD_SHAPE_NAME'].astype(str),
        'x': filtered_df['PIN_X'].astype(float),
        'y': filtered_df['PIN_Y'].astype(float),
        'layer': filtered_df['SUBCLASS'].astype(str)
    })
    
    get_component_pins_info_re.set_index('original_row', inplace=True)
    get_component_pins_info_re.sort_index(inplace=True)
    get_component_pins_info_re.index.name = None

    return get_component_pins_info_re

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="从 Excel 文件提取元器件焊盘/管脚清单。")
    parser.add_argument('-f', '--full', action='store_true', help="完整显示所有行和列。")
    args = parser.parse_args()

    start_time = time.time()
    result_df = get_component_pins_info()
    title = "🔍 criteria_35_get_component_pins_info - 获取元器件焊管脚清单"

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
