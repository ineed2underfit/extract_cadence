
import pandas as pd
try:
    df = pd.read_excel('parsed_tables_250804.xlsx', sheet_name='SYM_NAME')
    # 筛选出 R, C, L 元器件，并查看其 COMP_DEVICE_TYPE
    rcl_filter = df['REFDES'].str.startswith(('R', 'C', 'L'), na=False)
    print("--- Sample data from SYM_NAME sheet for R, C, L components ---")
    print(df[rcl_filter][['REFDES', 'COMP_DEVICE_TYPE']].dropna().head(30))
except FileNotFoundError:
    print("Error: 'parsed_tables_250804.xlsx' not found.")
except Exception as e:
    print(f"An error occurred: {e}")
