import pandas as pd
import json

def generate_kpis(excel_path="data.xlsx", kpi_path="kpis.json"):
    df = pd.read_excel(excel_path)

    kpis = {}

    # Basic info
    kpis["total_rows"] = len(df)
    kpis["total_columns"] = len(df.columns)
    kpis["columns"] = list(df.columns)

    # Missing values
    kpis["missing_values"] = df.isnull().sum().to_dict()

    # Data types
    kpis["data_types"] = {col: str(dtype) for col, dtype in df.dtypes.items()}

    # Numeric summary
    numeric_summary = {}
    numeric_cols = df.select_dtypes(include="number").columns

    for col in numeric_cols:
        series = df[col].dropna()
        if series.empty:
            continue
        numeric_summary[col] = {
            "min": float(series.min()),
            "max": float(series.max()),
            "mean": float(series.mean()),
            "median": float(series.median()),
        }

    kpis["numeric_summary"] = numeric_summary

    # Categorical summary (object / category)
    categorical_summary = {}
    cat_cols = df.select_dtypes(include=["object", "category"]).columns

    for col in cat_cols:
        vc = df[col].value_counts().head(5)
        categorical_summary[col] = {
            "unique_values": int(df[col].nunique(dropna=True)),
            "top_values": vc.to_dict(),
        }

    kpis["categorical_summary"] = categorical_summary

    # Date-like columns (auto-detect)
    date_summary = {}
    for col in df.columns:
        try:
            dt = pd.to_datetime(df[col], errors="coerce", dayfirst=True)
        except Exception:
            continue

        non_null = dt.notna().sum()
        if non_null == 0:
            continue

        # Consider it a real date column only if at least 50% rows are valid dates
        if non_null / len(dt) < 0.5:
            continue

        date_summary[col] = {
            "start_date": str(dt.min().date()),
            "end_date": str(dt.max().date()),
        }

    kpis["date_summary"] = date_summary

    # Save KPIs
    with open(kpi_path, "w", encoding="utf-8") as f:
        json.dump(kpis, f, indent=4)

    print(f"[OK] Generic KPIs saved to {kpi_path}")
