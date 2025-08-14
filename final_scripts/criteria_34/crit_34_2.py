import pandas as pd
import time
import sys
import re
import argparse
import numpy as np
import os


# 获取该网络上的连接的所有元件及其参数
def get_connected_components_on_net_re():
    """
    从 NET_NAME_SORT 工作表中提取网络上的连接元器件信息。
    """
    # 1. 从 Excel 文件读取数据
    # 使用相对于当前脚本文件位置的路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    excel_file = os.path.join(os.path.dirname(script_dir), 'parsed_tables_250804.xlsx')
    try:
        df = pd.read_excel(excel_file, sheet_name='NET_NAME_SORT', engine='openpyxl')
    except FileNotFoundError:
        print(f"错误：无法找到文件 '{excel_file}'。请确保文件在正确位置。")
        return pd.DataFrame()
    except Exception as e:
        print(f"读取 Excel 文件时发生错误: {e}")
        return pd.DataFrame()

    # 2. 保留原始索引作为\"身份证\"
    df.reset_index(inplace=True)
    df.rename(columns={'index': '_original_index'}, inplace=True)

    # 3. 一次性、安全地构建最终 DataFrame
    get_connected_components_on_net_re = pd.DataFrame({
        'original_row': df['_original_index'] + 2,
        # 确保 REFDES 和 PIN_NUMBER 在拼接前都是字符串
        'component_id': df['REFDES'].astype(str) + '_' + df['PIN_NUMBER'].astype(str),
        'net_name': df['NET_NAME']
    })

    # 4. 设置并排序最终的 Excel 行号索引
    get_connected_components_on_net_re.set_index('original_row', inplace=True)
    get_connected_components_on_net_re.sort_index(inplace=True)
    get_connected_components_on_net_re.index.name = None
    
    return get_connected_components_on_net_re


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="从 Cadence 导出的 Excel 文件中提取网络上的连接元器件信息。")
    parser.add_argument('-f', '--full', action='store_true', help="完整显示所有行和列。")
    args = parser.parse_args()

    start_time = time.time()
    result_df = get_connected_components_on_net_re()
    title = "🔍 criteria_34_2 - 获取该网络上连接的所有元件"

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
    # 只有在成功执行后才打印时间
    if result_df is not None:
        print(f"Total script runtime: {end_time - start_time:.2f} seconds\n")