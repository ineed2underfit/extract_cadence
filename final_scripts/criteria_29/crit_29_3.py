import pandas as pd
import argparse
import time
import os
import sys

# 添加上级目录到Python路径，以便导入其他模块
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir, '..'))

# 导入其他两个模块
try:
    from criteria_29 import crit_29_1, crit_29_2
except ImportError:
    try:
        import crit_29_1
        import crit_29_2
    except ImportError:
        print("错误：无法导入 crit_29_1 或 crit_29_2 模块。")
        print("请确保这些模块在正确的路径中。")
        sys.exit(1)

def judge_io_connector_in_tp_network():
    """
    判断 IO 连接器是否在测试点网络中。
    
    该函数将 crit_29_1.py 和 crit_29_2.py 提取的两个 DataFrame 
    按照 net_name 列进行分组，并对每个分组执行笛卡尔积操作。
    
    返回:
        pandas.DataFrame: 包含以下字段的 DataFrame：
                          - testpoint_id (str): 测试点 ID
                          - pin_id (str): 引脚 ID
                          - net_name (str): 网络名称
                          - matching_pairs (str): 由 testpoint_id 和 pin_id 拼接而成
    """
    # 获取两个数据源的数据
    df_tp = crit_29_1.get_test_point_list()
    df_pin = crit_29_2.get_connector_pin_list()
    
    # 检查数据是否为空
    if df_tp.empty or df_pin.empty:
        print("警告：一个或两个数据源为空。")
        return pd.DataFrame(columns=['testpoint_id', 'pin_id', 'net_name', 'matching_pairs'])
    
    # 重置索引以便处理
    df_tp_reset = df_tp.reset_index()
    df_pin_reset = df_pin.reset_index()
    
    # 按 net_name 分组并执行笛卡尔积
    result_list = []
    
    # 获取所有唯一的 net_name
    all_net_names = set(df_tp_reset['net_name']).union(set(df_pin_reset['net_name']))
    
    for net_name in all_net_names:
        # 获取当前 net_name 下的所有 testpoint_id
        tp_records = df_tp_reset[df_tp_reset['net_name'] == net_name]
        # 获取当前 net_name 下的所有 pin_id
        pin_records = df_pin_reset[df_pin_reset['net_name'] == net_name]
        
        # 如果两个数据源都有当前 net_name 的记录，则执行笛卡尔积
        if not tp_records.empty and not pin_records.empty:
            for _, tp_row in tp_records.iterrows():
                for _, pin_row in pin_records.iterrows():
                    testpoint_id = tp_row['testpoint_id']
                    pin_id = pin_row['pin_id']
                    matching_pair = f"{testpoint_id} - {pin_id}" if pd.notna(testpoint_id) and pd.notna(pin_id) else None
                    
                    result_list.append({
                        'testpoint_id': testpoint_id,
                        'pin_id': pin_id,
                        'net_name': net_name,
                        'matching_pairs': matching_pair
                    })
    
    # 创建结果 DataFrame
    judge_io_connector_in_tp_network_re = pd.DataFrame(result_list)
    
    # 如果结果为空，返回空的 DataFrame
    if judge_io_connector_in_tp_network_re.empty:
        return pd.DataFrame(columns=['testpoint_id', 'pin_id', 'net_name', 'matching_pairs'])
    
    # 删除重复行
    judge_io_connector_in_tp_network_re.drop_duplicates(inplace=True)

    # 按网络名称排序：先数字开头，其次字母开头
    def _sort_key(net):
        import re
        return (0, net) if re.match(r'^\d', str(net)) else (1, net)

    judge_io_connector_in_tp_network_re['__sort_key'] = judge_io_connector_in_tp_network_re['net_name'].apply(_sort_key)
    judge_io_connector_in_tp_network_re.sort_values(by=['__sort_key', 'net_name', 'testpoint_id', 'pin_id'], inplace=True)
    judge_io_connector_in_tp_network_re.drop(columns=['__sort_key'], inplace=True)

    # 重置索引
    judge_io_connector_in_tp_network_re.reset_index(drop=True, inplace=True)
    
    return judge_io_connector_in_tp_network_re

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="判断 IO 连接器是否在测试点网络中。")
    parser.add_argument('-f', '--full', action='store_true', help="完整显示所有行和列。")
    args = parser.parse_args()

    start_time = time.time()
    result_df = judge_io_connector_in_tp_network()
    title = "criteria_29_3 - 判断 IO 连接器是否在测试点网络中"

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