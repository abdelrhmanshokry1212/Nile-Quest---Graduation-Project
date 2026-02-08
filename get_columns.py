
import pandas as pd

try:
    df = pd.read_excel('Cairo_Giza_1000_Real_POIs.xlsx')
    with open('column_names.txt', 'w') as f:
        f.write(str(df.columns.tolist()))
        f.write("\n\nCategories:\n")
        f.write(str(df['Category'].unique().tolist()))
except Exception as e:
    with open('column_names.txt', 'w') as f:
        f.write(f"Error: {e}")
