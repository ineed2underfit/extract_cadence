
import pandas as pd

print("--- 诊断脚本开始 ---")
excel_file = 'parsed_tables_250804.xlsx'
sheet_name = 'SYM_TYPE'
refdes_to_find = 'C207'

try:
    df = pd.read_excel(excel_file, sheet_name=sheet_name)
    
    # 使用 .index 获取原始的、从0开始的 pandas 索引
    c207_rows = df[df['REFDES'] == refdes_to_find]
    
    if not c207_rows.empty:
        print(f"在工作表 '{sheet_name}' 中找到了 '{refdes_to_find}'。")
        for index in c207_rows.index:
            # Excel 行号 = pandas 索引 + 1 (标题行) + 1 (从1开始计数) = 索引 + 2
            excel_row = index + 2
            print(f" -> 位于 Pandas 索引: {index}，对应的 Excel 原始行号是: {excel_row}")
    else:
        print(f"在 '{sheet_name}' 中未找到 '{refdes_to_find}'。")

except Exception as e:
    print(f"读取或处理文件时发生错误: {e}")

print("--- 诊断脚本结束 ---")
