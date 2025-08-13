import pandas as pd

def compare_excel_columns(file_path, sheet_name, col1, col2):
    """
    Compares two columns in an Excel sheet and prints the rows where they differ.

    Args:
        file_path (str): The path to the Excel file.
        sheet_name (str): The name of the worksheet.
        col1 (str): The name of the first column to compare.
        col2 (str): The name of the second column to compare.
    """
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name)

        if col1 not in df.columns or col2 not in df.columns:
            print(f"Error: One or both columns '{col1}', '{col2}' not found in sheet '{sheet_name}'.")
            return

        # Fill NaN values to prevent comparison issues and ensure consistency
        df[col1] = df[col1].fillna('')
        df[col2] = df[col2].fillna('')

        diff_rows = df[df[col1] != df[col2]]

        if diff_rows.empty:
            print(f"In sheet '{sheet_name}', all values in column '{col1}' and '{col2}' are the same.")
        else:
            print(f"In sheet '{sheet_name}', found {len(diff_rows)} rows where column '{col1}' and '{col2}' differ:")
            print("="*80)
            # Create a new DataFrame for display with the original index
            display_df = pd.DataFrame()
            display_df['Original_Index'] = diff_rows.index + 2  # +2 to account for header and 0-based index
            display_df[col1] = diff_rows[col1]
            display_df[col2] = diff_rows[col2]
            print(display_df.to_string(index=False))
            print("="*80)

    except FileNotFoundError:
        print(f"Error: File not found at '{file_path}'")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    file_path = r'/final_scripts/parsed_tables_250804.xlsx'
    sheet_name = 'SYM_NAME'
    column1 = 'GRAPHIC_DATA_NAME'
    column2 = 'PAD_SHAPE_NAME'

    print(f"Comparing columns '{column1}' and '{column2}' in sheet '{sheet_name}'...")
    compare_excel_columns(file_path, sheet_name, column1, column2)
