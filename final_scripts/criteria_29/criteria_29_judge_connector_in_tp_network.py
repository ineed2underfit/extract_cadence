import pandas as pd
import numpy as np
import argparse
import time
import os
import sys
from itertools import product

# 动态地将父目录添加到 sys.path，以便导入兄弟模块
try:
    # 获取当前脚本所在的目录 (criteria_29)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 获取父目录 (final_scripts)
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)
    
    # 从兄弟目录 criteria_29 中导入所需函数
    from criteria_29.criteria_29_get_test_point_list import get_test_point_list
    from criteria_29.criteria_29_get_connector_pin_list import get_connector_pin_list
except (ImportError, NameError) as e:
    print(f"错误：无法导入依赖的函数: {e}")
    print("请确保 get_test_point_list 和 get_connector_pin_list 脚本存在于同一个 criteria_29 文件夹下。")
    # 在无法导入时提供一个虚拟函数，以便程序能继续执行并提示错误
    def get_test_point_list(): return pd.DataFrame()
    def get_connector_pin_list(): return pd.DataFrame()

import re

def judge_io_connector_in_tp_network():
    """
    判断测试点网络中的IO连接器，找出共享相同net_name的测试点和连接器引脚的所有配对。
    """
    # 1. 获取数据源
    print("步骤 1/3: 获取测试点数据...")
    tp_df = get_test_point_list()
    if tp_df.empty:
        print("警告: 未获取到测试点数据，无法继续。")
        return pd.DataFrame()

    print("步骤 2/3: 获取连接器引脚数据...")
    pin_df = get_connector_pin_list()
    if pin_df.empty:
        print("警告: 未获取到连接器引脚数据，无法继续。")
        return pd.DataFrame()

    # 2. 准备数据用于匹配
    tp_data = tp_df[['testpoint_id', 'net_name']]
    pin_data = pin_df[['pin_id', 'net_name']]

    # 3. 效仿参考脚本，通过循环和笛卡尔积进行匹配
    print("步骤 3/3: 匹配测试点和连接器引脚...")
    result_rows = []
    
    common_net_names = set(tp_data['net_name'].dropna().unique()) & set(pin_data['net_name'].dropna().unique())
    
    for net_name in common_net_names:
        tp_ids = tp_data[tp_data['net_name'] == net_name]['testpoint_id'].tolist()
        pin_ids = pin_data[pin_data['net_name'] == net_name]['pin_id'].tolist()
        
        if not tp_ids or not pin_ids:
            continue

        for tp_id, pin_id in product(tp_ids, pin_ids):
            result_rows.append({
                'testpoint_id': tp_id,
                'pin_id': pin_id,
                'net_name': net_name,
            })

    # 4. 创建并格式化最终的DataFrame
    if not result_rows:
        print("完成：未发现任何共享网络节点的测试点和连接器引脚。")
        return pd.DataFrame()

    judge_io_connector_in_tp_network_re = pd.DataFrame(result_rows)

    # 5. 创建 matching_pairs 列
    tp_id_str = judge_io_connector_in_tp_network_re['testpoint_id'].astype(str)
    pin_id_str = judge_io_connector_in_tp_network_re['pin_id'].astype(str)
    judge_io_connector_in_tp_network_re['matching_pairs'] = tp_id_str + ' - ' + pin_id_str

    # 6. 去除完全重复的行
    judge_io_connector_in_tp_network_re.drop_duplicates(inplace=True)

    # 7. 按网络名称排序：先数字开头的，后字母开头的
    def sort_key(net_name):
        if isinstance(net_name, str) and re.match(r'^\d', net_name):
            return (0, net_name)
        else:
            return (1, str(net_name))
    
    judge_io_connector_in_tp_network_re['sort_key'] = judge_io_connector_in_tp_network_re['net_name'].apply(sort_key)
    # 增加 testpoint_id 和 pin_id 作为次要和三次要排序键，确保整体顺序稳定
    judge_io_connector_in_tp_network_re.sort_values(by=['sort_key', 'testpoint_id', 'pin_id'], inplace=True)
    judge_io_connector_in_tp_network_re.drop(columns=['sort_key'], inplace=True)

    # 8. 重置索引为从0开始的自增序号
    final_df = judge_io_connector_in_tp_network_re.reset_index(drop=True)
    
    return final_df

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="判断IO连接器是否在测试点网络中，并找出所有匹配对。" )
    parser.add_argument('-f', '--full', action='store_true', help="完整显示所有行和列。" )
    args = parser.parse_args()

    start_time = time.time()
    result_df = judge_io_connector_in_tp_network()
    title = "🔗 criteria_29 - 测试点与连接器引脚匹配列表"

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
