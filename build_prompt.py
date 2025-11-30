def build_prompt(kpi_path="kpis.json", prompt_path="summary_prompt.txt"):
    with open(kpi_path, "r", encoding="utf-8") as f:
        kpis = json.load(f)

    total_rows = kpis.get("total_rows")
    total_columns = kpis.get("total_columns")
    columns = kpis.get("columns", [])
    missing_values = kpis.get("missing_values", {})
    data_types = kpis.get("data_types", {})
    numeric_summary = kpis.get("numeric_summary", {})
    categorical_summary = kpis.get("categorical_summary", {})
    date_summary = kpis.get("date_summary", {})

    prompt = f"""
You are an experienced data analyst. You are given profiling information about a tabular dataset.

DATASET OVERVIEW:
- Total rows: {total_rows}
- Total columns: {total_columns}

COLUMNS AND DATA TYPES:
"""
    for col, dtype in data_types.items():
        prompt += f"- {col}: {dtype}\n"

    prompt += "\nMISSING VALUES PER COLUMN:\n"
    for col, missing in missing_values.items():
        prompt += f"- {col}: {missing} missing\n"

    if numeric_summary:
        prompt += "\nNUMERIC COLUMNS SUMMARY (min, max, mean, median):\n"
        for col, stats in numeric_summary.items():
            prompt += (
                f"- {col}: min={stats['min']}, max={stats['max']}, "
                f"mean={stats['mean']}, median={stats['median']}\n"
            )

    if categorical_summary:
        prompt += "\nCATEGORICAL COLUMNS SUMMARY (unique values and top categories):\n"
        for col, info in categorical_summary.items():
            prompt += f"- {col}: {info['unique_values']} unique values; top values:\n"
            for val, count in info["top_values"].items():
                prompt += f"    • '{val}' → {count} rows\n"

    if date_summary:
        prompt += "\nDATE-LIKE COLUMNS (coverage ranges):\n"
        for col, info in date_summary.items():
            prompt += f"- {col}: from {info['start_date']} to {info['end_date']}\n"

    prompt += """

TASK:
Using the information above, write a clear dataset summary and analysis. Specifically:

1. Describe the overall structure of the dataset (rows, columns, important fields).
2. Comment on numeric columns: ranges, central tendencies, and any potential outliers or skewness you can infer.
3. Comment on categorical columns: variety of categories and any dominance patterns in top values.
4. If date-like columns exist, describe the time coverage and possible use-cases (e.g., time-series analysis).
5. Comment on data quality based on missing values and data types.
6. Suggest 3–5 possible analytical questions or use-cases that this dataset could help answer.

Keep the language simple, professional, and non-technical. Focus on interpretation, not just repeating the numbers.
"""

    with open(prompt_path, "w", encoding="utf-8") as f:
        f.write(prompt)

    print(f"[OK] Generic prompt saved to {prompt_path}")
