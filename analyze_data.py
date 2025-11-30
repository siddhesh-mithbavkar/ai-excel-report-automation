import pandas as pd

file_path = "Orders.xlsx"
df = pd.read_excel(file_path)

print("=== BASIC DATA ANALYSIS ===\n")

# 1. Total rows
print("Total Rows:", len(df))

# 2. Unique Order IDs
if "Order ID" in df.columns:
    print("Unique Order IDs:", df["Order ID"].nunique())

# 3. Unique Customers
if "CustomerName" in df.columns:
    print("Unique Customers:", df["CustomerName"].nunique())

# 4. Orders by State
if "State" in df.columns:
    print("\nOrders by State:")
    print(df["State"].value_counts())

# 5. Orders by City
if "City" in df.columns:
    print("\nOrders by City:")
    print(df["City"].value_counts().head(10))

# 6. Date range
if "Order Date" in df.columns:
    df["Order Date"] = pd.to_datetime(df["Order Date"], dayfirst=True, errors="coerce")
    print("\nDate Range:")
    print("From:", df["Order Date"].min())
    print("To:", df["Order Date"].max())

# 7. Missing values
print("\nMissing Values:")
print(df.isnull().sum())

# 8. Data Types
print("\nColumn Data Types:")
print(df.dtypes)
