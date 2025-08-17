
import pandas as pd
import numpy as np
import argparse
import time
import os

def get_unique_padwidth(group):
    """辅助函数：在一个分组内，如果所有PADWIDTH值唯一，则返回该值，否则返回NaN。"""
    unique_widths = group['PADWIDTH'].dropna().unique()
    if len(unique_widths) == 1:
        return unique_widths[0]
    else:
        return np.nan

def get_test_point_shape_and_size():
    """
    从Excel文件中提取测试点的形状和尺寸信息。
    """
    # 1. 构建路径并读取数据
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        excel_file_path = os.path.join(os.path.dirname(script_dir), 'parsed_tables_250804.xlsx')
    except NameError:
        excel_file_path = r'E:\pycharm_projects\testability_projects\extract_cadence\final_scripts\parsed_tables_250804.xlsx'

    try:
        sym_name_df = pd.read_excel(excel_file_path, sheet_name='SYM_NAME', engine='openpyxl')
        pad_name_df = pd.read_excel(excel_file_path, sheet_name='PAD_NAME', engine='openpyxl')
    except Exception as e:
        print(f"读取 Excel 文件时发生错误: {e}")
        return pd.DataFrame()

    # 2. 准备基础测试点 DataFrame (来自 SYM_NAME)，并应用所有新筛选条件
    tp_cond = (
        sym_name_df['REFDES'].str.startswith('TP', na=False) &
        sym_name_df['SUBCLASS'].isin(['TOP', 'BOTTOM']) &
        sym_name_df['PAD_SHAPE_NAME'].notna() & (sym_name_df['PAD_SHAPE_NAME'] != '')
    )
    tp_df = sym_name_df[tp_cond].copy()
    if tp_df.empty:
        print("警告: 在 SYM_NAME 表中未找到任何以 TP 开头的测试点。")
        return pd.DataFrame()
    # 保留原始索引用于最终关联
    tp_df['original_excel_row'] = tp_df.index + 2
    tp_df['original_tp_index'] = tp_df.index

    # 3. 准备用于查找的 PAD_NAME DataFrame
    pad_layer_filter = pad_name_df['LAYER'].str.contains('TOP|BOTTOM|DRILL', na=False)
    pad_lookup_df = pad_name_df[pad_layer_filter].copy()
    pad_lookup_df = pad_lookup_df[['PAD_NAME', 'PADSHAPE1', 'PADWIDTH']].rename(columns={
        'PAD_NAME': 'PAD_STACK_NAME',
        'PADSHAPE1': 'PAD_SHAPE_NAME'
    })

    # 4. 合并两个DataFrame以进行匹配
    merged_df = pd.merge(
        tp_df, 
        pad_lookup_df, 
        on=['PAD_STACK_NAME', 'PAD_SHAPE_NAME'], 
        how='left'
    )

    # 5. 分组计算唯一的 PADWIDTH
    # 如果合并后没有数据，则直接返回
    if merged_df.empty:
        # 这种情况理论上不应发生，因为是左合并，但作为安全检查
        return pd.DataFrame()
        
    padwidth_results = merged_df.groupby('original_tp_index').apply(get_unique_padwidth).rename('final_padwidth')

    # 6. 将计算结果连接回原始测试点DataFrame
    final_tp_df = tp_df.set_index('original_tp_index').join(padwidth_results)

    # 7. 构建最终输出DataFrame
    df_re = pd.DataFrame()
    df_re['testpoint_id'] = final_tp_df['REFDES']
    df_re['shape_type'] = final_tp_df['PAD_SHAPE_NAME']

    # 根据形状类型，条件性地填充尺寸列
    square_cond = final_tp_df['PAD_SHAPE_NAME'].isin(['RECTANGLE', 'LINE'])
    circle_cond = final_tp_df['PAD_SHAPE_NAME'].eq('CIRCLE')

    df_re['square_length'] = np.where(square_cond, final_tp_df['final_padwidth'], np.nan)
    df_re['square_width'] = np.where(square_cond, final_tp_df['final_padwidth'], np.nan)
    df_re['round_diameter'] = np.where(circle_cond, final_tp_df['final_padwidth'], np.nan)
    
    # 加入原始行号以便后续操作
    df_re['original_excel_row'] = final_tp_df['original_excel_row']

    # 8. 去重与索引设置
    # 定义内容列，去重操作将基于这些列
    content_columns = ['testpoint_id', 'shape_type', 'square_length', 'square_width', 'round_diameter']
    get_test_point_shape_and_size_re = df_re.drop_duplicates(subset=content_columns, keep='first')
    
    # 设置索引
    get_test_point_shape_and_size_re = get_test_point_shape_and_size_re.set_index('original_excel_row')
    get_test_point_shape_and_size_re.index.name = None

    return get_test_point_shape_and_size_re

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="提取测试点的形状和尺寸信息。 সন")
    parser.add_argument('-f', '--full', action='store_true', help="完整显示所有行和列。")
    args = parser.parse_args()

    start_time = time.time()
    result_df = get_test_point_shape_and_size()
    title = "📐 criteria_43 - 获取测试点形状与尺寸"

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
    if result_df is not None:
        print(f"Total script runtime: {end_time - start_time:.2f} seconds\n")
