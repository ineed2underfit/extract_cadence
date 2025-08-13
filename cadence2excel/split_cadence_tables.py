#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cadence PCB数据文件表格分割工具
从Cadence导出的txt文件中分割出不同的表格
"""

import os
import re
from typing import List, Dict, Tuple

def parse_cadence_file(file_path: str) -> Dict[str, List[str]]:
    """
    解析Cadence PCB数据文件，按表格分割
    
    Args:
        file_path: 输入文件路径
        
    Returns:
        dict: 键为表格名称，值为该表格的所有行
    """
    tables = {}
    current_table = None
    current_table_lines = []
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
                
            # 表格标题行 (A!开头)
            if line.startswith('A!'):
                # 保存上一个表格
                if current_table and current_table_lines:
                    tables[current_table] = current_table_lines
                
                # 开始新表格
                headers = line[2:].split('!')  # 移除A!前缀
                table_name = f"table_{len(tables)+1:02d}_{headers[0].lower()}"
                current_table = table_name
                current_table_lines = [line]
                
            # 文件信息行或数据行
            elif line.startswith(('J!', 'S!')) and current_table:
                current_table_lines.append(line)
    
    # 保存最后一个表格
    if current_table and current_table_lines:
        tables[current_table] = current_table_lines
    
    return tables

def save_table_to_csv(table_name: str, lines: List[str], output_dir: str):
    """
    将表格数据保存为CSV文件
    
    Args:
        table_name: 表格名称
        lines: 表格行数据
        output_dir: 输出目录
    """
    import csv
    
    csv_file = os.path.join(output_dir, f"{table_name}.csv")
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        for line in lines:
            if line.startswith('A!'):
                # 标题行
                headers = line[2:].split('!')
                writer.writerow(headers)
            elif line.startswith('S!'):
                # 数据行
                data = line[2:].split('!')
                writer.writerow(data)
            # J!行通常是文件信息，可以跳过或单独处理

def save_table_to_txt(table_name: str, lines: List[str], output_dir: str):
    """
    将表格数据保存为txt文件
    
    Args:
        table_name: 表格名称  
        lines: 表格行数据
        output_dir: 输出目录
    """
    txt_file = os.path.join(output_dir, f"{table_name}.txt")
    
    with open(txt_file, 'w', encoding='utf-8') as f:
        for line in lines:
            f.write(line + '\n')

def analyze_table_structure(tables: Dict[str, List[str]]) -> None:
    """
    分析表格结构并打印统计信息
    
    Args:
        tables: 解析出的表格字典
    """
    print("=" * 60)
    print("Cadence PCB数据文件分析结果")
    print("=" * 60)
    
    for table_name, lines in tables.items():
        header_line = next((line for line in lines if line.startswith('A!')), None)
        data_lines = [line for line in lines if line.startswith('S!')]
        
        if header_line:
            headers = header_line[2:].split('!')
            print(f"\n表格: {table_name}")
            print(f"  列数: {len(headers)}")
            print(f"  数据行数: {len(data_lines)}")
            print(f"  列名: {', '.join(headers[:5])}{'...' if len(headers) > 5 else ''}")

def main():
    input_file = "cds_routed.brd.txt"
    output_dir = "split_tables"
    
    # 检查输入文件
    if not os.path.exists(input_file):
        print(f"错误: 找不到输入文件 {input_file}")
        return
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    print("正在解析Cadence PCB数据文件...")
    tables = parse_cadence_file(input_file)
    
    # 分析表格结构
    analyze_table_structure(tables)
    
    # 保存表格
    print(f"\n正在保存表格到 {output_dir} 目录...")
    for table_name, lines in tables.items():
        # 保存为txt格式
        save_table_to_txt(table_name, lines, output_dir)
        # 保存为csv格式
        save_table_to_csv(table_name, lines, output_dir)
    
    print(f"\n完成! 共分割出 {len(tables)} 个表格")
    print(f"文件保存在: {os.path.abspath(output_dir)}")

if __name__ == "__main__":
    main()