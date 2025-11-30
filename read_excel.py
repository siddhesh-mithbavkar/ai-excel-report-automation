import pandas as pd

# Load Excel file
file_path = "Orders.xlsx"   # Change this to your file name
df = pd.read_excel(file_path)

# Show first 5 rows
print("Preview of your data:")
print(df.head())

# Show shape (rows, columns)
print("\nRows and Columns:", df.shape)

# Show columns
print("\nColumns:")
print(df.columns.tolist())



