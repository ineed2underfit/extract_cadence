import pandas as pd
import time
import argparse
import os
import sys
from itertools import product
import re

# 添加上级目录到Python路径，以便导入criteria_32_1和criteria_32_2
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from criteria_32_1 import get_test_point_list
from criteria_32_2 import get_connector_list


def judge_io_connector_in_tp_network():
    """
    判断IO连接器是否在测试点网络中。

    通过比较测试点和连接器的网络名称(net_name)，找出具有相同网络名称的测试点和连接器的所有配对组合。

    返回:
        pandas.DataFrame: 包含以下字段的 DataFrame：
                          - testpoint_id (str): 测试点ID
                          - component_id (str): 连接器ID
                          - net_name (str): 网络名称
                          - matching_pairs (str): 测试点ID和连接器ID的拼接字符串，格式为 "testpoint_id - component_id"
    """
    # 获取测试点数据
    try:
        tp_df = get_test_point_list()
        if tp_df.empty:
            print("警告: 未获取到测试点数据。")
            return pd.DataFrame(columns=['testpoint_id', 'component_id', 'net_name', 'matching_pairs'])
    except Exception as e:
        print(f"获取测试点数据时发生错误: {e}")
        return pd.DataFrame(columns=['testpoint_id', 'component_id', 'net_name', 'matching_pairs'])

    # 获取连接器数据
    try:
        connector_df = get_connector_list()
        if connector_df.empty:
            print("警告: 未获取到连接器数据。")
            return pd.DataFrame(columns=['testpoint_id', 'component_id', 'net_name', 'matching_pairs'])
    except Exception as e:
        print(f"获取连接器数据时发生错误: {e}")
        return pd.DataFrame(columns=['testpoint_id', 'component_id', 'net_name', 'matching_pairs'])

    # 重命名列以便处理
    tp_data = tp_df[['testpoint_id', 'net_name']].copy()
    connector_data = connector_df[['connector_id', 'net_name']].copy()
    connector_data.rename(columns={'connector_id': 'component_id'}, inplace=True)

    # 按照net_name分组并执行笛卡尔积操作
    result_rows = []
    
    # 获取所有共同的net_name
    common_net_names = set(tp_data['net_name'].dropna().unique()) & set(connector_data['net_name'].dropna().unique())
    
    for net_name in common_net_names:
        # 获取该net_name下的所有testpoint_id
        tp_ids = tp_data[tp_data['net_name'] == net_name]['testpoint_id'].tolist()
        
        # 获取该net_name下的所有component_id
        component_ids = connector_data[connector_data['net_name'] == net_name]['component_id'].tolist()
        
        # 对两个列表进行笛卡尔积操作
        for tp_id, comp_id in product(tp_ids, component_ids):
            matching_pair = f"{tp_id} - {comp_id}"
            result_rows.append({
                'testpoint_id': tp_id,
                'component_id': comp_id,
                'net_name': net_name,
                'matching_pairs': matching_pair
            })
    
    # 创建最终的DataFrame
    judge_io_connector_in_tp_network_re = pd.DataFrame(result_rows)
    
    # 如果没有结果，返回空的DataFrame
    if judge_io_connector_in_tp_network_re.empty:
        return pd.DataFrame(columns=['testpoint_id', 'component_id', 'net_name', 'matching_pairs'])
    
    # 去除重复行
    judge_io_connector_in_tp_network_re.drop_duplicates(inplace=True)
    
    # 按网络名称排序：先数字开头的，后字母开头的
    def sort_key(net_name):
        # 如果网络名称以数字开头，返回(0, net_name)，否则返回(1, net_name)
        # 这样数字开头的会排在前面
        if re.match(r'^\d', net_name):
            return (0, net_name)
        else:
            return (1, net_name)
    
    # 应用排序
    judge_io_connector_in_tp_network_re['sort_key'] = judge_io_connector_in_tp_network_re['net_name'].apply(sort_key)
    judge_io_connector_in_tp_network_re.sort_values(by=['sort_key', 'net_name', 'testpoint_id', 'component_id'], inplace=True)
    judge_io_connector_in_tp_network_re.drop(columns=['sort_key'], inplace=True)
    
    # 重置索引
    judge_io_connector_in_tp_network_re.reset_index(drop=True, inplace=True)
    
    return judge_io_connector_in_tp_network_re


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="判断IO连接器是否在测试点网络中。")
    parser.add_argument('-f', '--full', action='store_true', help="完整显示所有行和列。")
    args = parser.parse_args()

    start_time = time.time()
    result_df = judge_io_connector_in_tp_network()
    title = "🔍 criteria_32_3 - 判断测试点所在网络的IO连接器存在性"

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
            print(f"\n[{result_df.shape[0]} rows x {result_df.shape[1]} columns]")

    end_time = time.time()
    if result_df is not None:
        print(f"Total script runtime: {end_time - start_time:.2f} seconds\n")
    else:
        print("未能生成结果。")