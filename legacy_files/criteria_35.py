import pandas as pd
import os
import sys
import time
import argparse

def get_component_pins_info():
    """
    从 Excel 文件中提取元器件焊盘信息。

    提取规则:
    1. 从 'parsed_tables_new.xlsx' 文件读取数据。
    2. 仅提取 CLASS 列为 'PIN' 且 SUBCLASS 列为 'TOP' 或 'BOTTOM' 的行。
    3. 如果同一个 PIN 同时出现在 TOP 和 BOTTOM，两者都保留。
    4. 构建并返回一个包含特定列的 DataFrame。

    Returns:
        pandas.DataFrame: 包含处理后焊盘信息的 DataFrame，列包括:
                          'component_id', 'pin_id', 'PAD_STACK_NAME',
                          'PAD_SHAPE_NAME', 'x', 'y', 'layer'。
    """
    # 构建文件路径
    # The Excel file is in the same directory as the script.
    # We construct an absolute path to it to ensure it's found regardless of where the script is run from.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'parsed_tables_250804.xlsx')

    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"错误: Excel 文件 '{file_path}' 未找到。")

    # 读取 Excel 文件中名为 'SYM_NAME' 的工作表
    try:
        df = pd.read_excel(file_path, sheet_name='SYM_NAME')
    except Exception as e:
        raise IOError(f"读取 Excel 文件时出错: {e}")

    # 筛选条件
    # 1. CLASS 列为 'PIN'
    # 2. SUBCLASS 列为 'TOP' 或 'BOTTOM'
    filtered_df = df[
        (df['CLASS'] == 'PIN') &
        (df['SUBCLASS'].isin(['TOP', 'BOTTOM']))
    ].copy()

    # 创建新的 DataFrame
    get_component_pins_info_re = pd.DataFrame()

    # 填充新 DataFrame 的列
    get_component_pins_info_re['component_id'] = filtered_df['REFDES'].astype(str)
    # PIN_NUMBER 可能为数字，需要转为字符串再拼接
    get_component_pins_info_re['pin_id'] = filtered_df['REFDES'].astype(str) + '_' + filtered_df['PIN_NUMBER'].astype(str)
    get_component_pins_info_re['PAD_STACK_NAME'] = filtered_df['PAD_STACK_NAME'].astype(str)
    get_component_pins_info_re['PAD_SHAPE_NAME'] = filtered_df['PAD_SHAPE_NAME'].astype(str)
    get_component_pins_info_re['x'] = filtered_df['PIN_X'].astype(float)
    get_component_pins_info_re['y'] = filtered_df['PIN_Y'].astype(float)
    get_component_pins_info_re['layer'] = filtered_df['SUBCLASS'].astype(str)

    return get_component_pins_info_re

if __name__ == '__main__':
    # --- 记录开始时间 ---
    start_time = time.time()

    # --- 使用 argparse 处理命令行参数 ---
    parser = argparse.ArgumentParser(description="从 Excel 文件提取元器件焊盘/管脚清单。")
    parser.add_argument('-f', '--full', action='store_true', help="显示完整的输出，而不是省略版本。")
    args = parser.parse_args()

    try:
        component_pads_df = get_component_pins_info()

        if args.full:
            # --- 完整模式 ---
            print("--- criteria_35 获取元器件焊盘/管脚清单 ---")
            print("--- (Full Mode) ---")
            pd.set_option('display.max_rows', None)
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', 1000)
        else:
            # --- 默认省略模式 ---
            print("--- criteria_35 获取元器件焊盘/管脚清单 ---")
            print("--- (Default Mode, use -f or --full to show all) ---")
            # 在此模式下，使用 pandas 的默认显示设置

        # 打印 DataFrame
        print(component_pads_df)

        # 如果是完整模式，手动补上摘要信息
        if args.full:
            print(f"\n[{component_pads_df.shape[0]} rows x {component_pads_df.shape[1]} columns]")

    except (FileNotFoundError, IOError) as e:
        print(e)
    except Exception as e:
        print(f"发生未知错误: {e}")
    finally:
        # --- 计算并打印总运行时间 ---
        end_time = time.time()
        print(f"Total script runtime: {end_time - start_time:.2f} seconds\n")
