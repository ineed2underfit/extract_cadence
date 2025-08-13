import pandas as pd
import os
from pathlib import Path

def read_excel_robust(file_path, sheet_name='SYM_NAME'):
    """
    健壮的Excel文件读取函数
    
    Args:
        file_path (str): Excel文件路径
        sheet_name (str): 工作表名称，默认'SYM_NAME'
        
    Returns:
        pandas.DataFrame: 读取的数据，失败时返回空DataFrame
    """
    # 转换为Path对象以便更好地处理路径
    file_path = Path(file_path)
    
    # 检查文件是否存在
    if not file_path.exists():
        print(f"❌ 错误：文件 '{file_path}' 不存在")
        return pd.DataFrame()
    
    # 检查文件扩展名
    if file_path.suffix.lower() not in ['.xlsx', '.xls']:
        print(f"❌ 错误：'{file_path}' 不是有效的Excel文件")
        return pd.DataFrame()
    
    try:
        # 尝试使用openpyxl引擎读取xlsx文件
        if file_path.suffix.lower() == '.xlsx':
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
        else:
            # 对于xls文件使用xlrd引擎
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='xlrd')
            
        print(f"✅ 成功读取文件 '{file_path}'，工作表 '{sheet_name}'")
        print(f"📊 数据维度: {df.shape[0]} 行 × {df.shape[1]} 列")
        
        return df
        
    except FileNotFoundError:
        print(f"❌ 错误：文件 '{file_path}' 未找到")
        return pd.DataFrame()
    except ValueError as e:
        if "Worksheet" in str(e):
            print(f"❌ 错误：工作表 '{sheet_name}' 不存在于文件 '{file_path}' 中")
            # 尝试列出所有可用的工作表
            try:
                xl = pd.ExcelFile(file_path)
                print(f"📋 可用工作表: {xl.sheet_names}")
            except:
                pass
        else:
            print(f"❌ 数据格式错误: {e}")
        return pd.DataFrame()
    except PermissionError:
        print(f"❌ 错误：无权限访问文件 '{file_path}'（文件可能正在被其他程序使用）")
        return pd.DataFrame()
    except Exception as e:
        print(f"❌ 读取Excel文件时发生未知错误: {type(e).__name__}: {e}")
        return pd.DataFrame()

def get_excel_info(file_path):
    """
    获取Excel文件的基本信息
    
    Args:
        file_path (str): Excel文件路径
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        print(f"❌ 文件 '{file_path}' 不存在")
        return
    
    try:
        xl = pd.ExcelFile(file_path)
        print(f"📄 文件: {file_path}")
        print(f"📋 工作表数量: {len(xl.sheet_names)}")
        print(f"📝 工作表列表: {xl.sheet_names}")
        
        # 显示每个工作表的基本信息
        for sheet in xl.sheet_names:
            try:
                df = pd.read_excel(xl, sheet_name=sheet, nrows=0)  # 只读取表头
                print(f"   └─ '{sheet}': {len(df.columns)} 列")
            except:
                print(f"   └─ '{sheet}': 无法读取")
                
    except Exception as e:
        print(f"❌ 获取文件信息失败: {e}")

if __name__ == "__main__":
    # 测试函数
    test_file = "../final_scripts/parsed_tables_250804.xlsx"
    print("🔍 Excel文件信息:")
    get_excel_info(test_file)
    
    print("\n📖 读取测试:")
    df = read_excel_robust(test_file, 'SYM_NAME')
    if not df.empty:
        print(f"✅ 读取成功，前5行预览:")
        print(df.head())