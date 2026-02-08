
import pandas as pd

try:
    df = pd.read_excel('Cairo_Giza_1000_Real_POIs.xlsx')
    print("Columns:", df.columns.tolist())
    print("Categories:", df['Category'].unique().tolist())
    print("Sub-categories sample:", df['Sub-category'].head(10).tolist())
except Exception as e:
    print(f"Error reading excel file: {e}")
