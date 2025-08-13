import pandas as pd
import sys

def list_excel_sheets(file_path):
    """
    Lists all sheet names in a given Excel file.
    """
    try:
        # Using openpyxl engine is recommended for .xlsx files
        xls = pd.ExcelFile(file_path, engine='openpyxl')
        sheet_names = xls.sheet_names
        
        print("\n--- Available Worksheets --- gateways")
        if not sheet_names:
            print("No worksheets found in the file.")
        else:
            print("The following worksheets were found in the Excel file:")
            for name in sheet_names:
                print(f"- {name}")
        print("--------------------------")

    except FileNotFoundError:
        print(f"Error: The file was not found at '{file_path}'")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred while reading the Excel file: {e}")
        sys.exit(1)

if __name__ == '__main__':
    EXCEL_FILE_PATH = r'../final_scripts/parsed_tables_250804.xlsx'
    print(f"Checking for worksheets in: {EXCEL_FILE_PATH}")
    list_excel_sheets(EXCEL_FILE_PATH)
    print("\nScript finished.")
