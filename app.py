import os
import json

import streamlit as st
import pandas as pd
import altair as alt
from groq import Groq
from dotenv import load_dotenv

from export_pdf import generate_pdf
from export_docx import generate_docx


# ----------------- GLOBAL STYLE ----------------- #

def set_custom_style():
    st.markdown(
        """
        <style>
        /* Overall background */
        .stApp {
            background: linear-gradient(135deg, #e0ebff 0%, #f5f7ff 40%, #ffffff 100%);
            font-family: "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* Centered page title */
        .main-title {
            text-align: center;
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 4px;
        }

        .main-subtitle {
            text-align: center;
            font-size: 14px;
            color: #4b5563;
            margin-bottom: 20px;
        }

        /* Section headers */
        .section-header {
            font-size: 20px;
            font-weight: 600;
            margin: 10px 0 4px 0;
            color: #111827;
        }

        .section-subtext {
            font-size: 12px;
            color: #6b7280;
            margin-bottom: 8px;
        }

        /* Make side bar a bit nicer */
        [data-testid="stSidebar"] {
            background: #0f172a;
            color: #e5e7eb;
        }
        [data-testid="stSidebar"] * {
            color: #e5e7eb !important;
        }

        /* Reduce padding on top */
        .block-container {
            padding-top: 1rem;
            padding-bottom: 3rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(label, value, subtext="", color="#4f46e5"):
    st.markdown(
        f"""
        <div style="
            background:{color};
            padding:14px 18px;
            border-radius:22px;
            text-align:center;
            color:white;
            box-shadow:0 10px 20px rgba(15,23,42,0.18);
        ">
            <div style="font-size:12px; opacity:0.9;">{label}</div>
            <div style="font-size:24px; font-weight:700; margin:4px 0 2px 0;">{value}</div>
            <div style="font-size:11px; opacity:0.85;">{subtext}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ----------------- HELPERS ----------------- #

def load_excel_auto_header(file):
    """
    Auto-detect the real header row in messy Excel files.
    Skips title rows like 'Excel Sample Data', etc.
    """
    df_raw = pd.read_excel(file, header=None)

    for i in range(len(df_raw)):
        row = df_raw.iloc[i]
        non_empty = row.notna().sum()
        # assume header row has at least 2 non-empty cells
        if non_empty >= 2:
            return pd.read_excel(file, header=i)

    # fallback if nothing detected
    return pd.read_excel(file)


def add_percent_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect columns stored as '78%' strings and create numeric versions.
    Example: 'Progress' -> 'Progress (numeric)' with 0.78.
    """
    df = df.copy()
    for col in df.select_dtypes(include=["object"]).columns:
        s = df[col].dropna().astype(str).str.strip()
        if len(s) == 0:
            continue

        pct_mask = s.str.match(r"^\d+(\.\d+)?%$")

        if pct_mask.mean() >= 0.8:
            numeric = pd.to_numeric(
                s.str.rstrip("%"), errors="coerce"
            ) / 100.0
            df[f"{col} (numeric)"] = numeric

    return df


# ----------------- PAGE CONFIG ----------------- #

st.set_page_config(page_title="AI Report Automation", layout="wide")
set_custom_style()

st.markdown('<div class="main-title">AI Data Dashboard & Summary</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="main-subtitle">Upload any Excel file, choose a main metric and see an auto-built dashboard, data quality view, and AI written report.</div>',
    unsafe_allow_html=True,
)

# ----------------- FILE UPLOAD ----------------- #

with st.container():
    uploaded_file = st.file_uploader("📂 Upload Excel file", type=["xlsx", "xls"])

if uploaded_file is None:
    st.info("Upload an Excel file to get started.")
    st.stop()

# Load & clean Excel
df_raw = load_excel_auto_header(uploaded_file)
df = add_percent_numeric_columns(df_raw)

st.success("File loaded successfully!")

# Detect column types
numeric_cols = df.select_dtypes(include="number").columns.tolist()
cat_cols = []
for col in df.select_dtypes(include=["object", "category"]).columns:
    nunique = df[col].nunique(dropna=True)
    if 1 < nunique < len(df) * 0.8:
        cat_cols.append(col)

date_cols = []
for col in df.columns:
    try:
        dt = pd.to_datetime(df[col], errors="coerce", dayfirst=True)
    except Exception:
        continue
    non_null = dt.notna().sum()
    if non_null == 0:
        continue
    if non_null / len(dt) >= 0.4:
        date_cols.append(col)

if not numeric_cols:
    st.error("No numeric columns detected. This dashboard needs at least one numeric column.")
    st.stop()

# ----------------- SIDEBAR: CONTROLS ----------------- #

st.sidebar.title("⚙️ Controls")

metric_col = st.sidebar.selectbox("Main numeric metric", numeric_cols)

dim_options = ["None"] + cat_cols
dim_col = st.sidebar.selectbox("Primary category", dim_options)

date_options = ["None"] + date_cols
date_col_selected = st.sidebar.selectbox("Date column", date_options)

# Optional filter on chosen category
filtered_df = df.copy()
if dim_col != "None":
    unique_vals = sorted(filtered_df[dim_col].dropna().unique().tolist())
    selected_vals = st.sidebar.multiselect(
        f"Filter {dim_col}", options=["(All)"] + unique_vals, default="(All)"
    )
    if "(All)" not in selected_vals:
        filtered_df = filtered_df[filtered_df[dim_col].isin(selected_vals)]

if filtered_df.empty:
    st.warning("No data after applying filters.")
    st.stop()

# ----------------- HIGH-LEVEL DATASET KPIs ----------------- #

total_rows = len(filtered_df)
total_cols = len(filtered_df.columns)
total_cells = int(filtered_df.size)

missing_cells = int(filtered_df.isna().sum().sum())
missing_pct = (missing_cells / total_cells * 100) if total_cells > 0 else 0

duplicate_rows = int(filtered_df.duplicated().sum())
duplicate_pct = (duplicate_rows / total_rows * 100) if total_rows > 0 else 0

st.markdown('<div class="section-header">Dataset Overview</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-subtext">Quick snapshot of dataset size and basic health after applying filters.</div>',
    unsafe_allow_html=True,
)

row1 = st.columns(4)
with row1[0]:
    kpi_card("Rows", f"{total_rows:,}", "Records after filters", "#6366f1")
with row1[1]:
    kpi_card("Columns", f"{total_cols}", "Total features", "#8b5cf6")
with row1[2]:
    kpi_card("Missing Cells", f"{missing_pct:.1f}%", f"{missing_cells:,} cells", "#f97316")
with row1[3]:
    kpi_card("Duplicate Rows", f"{duplicate_pct:.1f}%", f"{duplicate_rows:,} rows", "#ec4899")

st.markdown("<hr>", unsafe_allow_html=True)

# ----------------- METRIC-SPECIFIC KPIs ----------------- #

metric_series = filtered_df[metric_col].dropna()
metric_total = metric_series.sum()
metric_mean = metric_series.mean()
metric_min = metric_series.min()
metric_max = metric_series.max()

st.markdown('<div class="section-header">Metric Focus</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="section-subtext">Key stats for the selected metric <b>{metric_col}</b>.</div>',
    unsafe_allow_html=True,
)

row2 = st.columns(4)
with row2[0]:
    kpi_card(f"Total {metric_col}", f"{metric_total:,.2f}", "", "#22c55e")
with row2[1]:
    kpi_card(f"Average {metric_col}", f"{metric_mean:,.2f}", "", "#0ea5e9")
with row2[2]:
    kpi_card(f"Min {metric_col}", f"{metric_min:,.2f}", "", "#facc15")
with row2[3]:
    kpi_card(f"Max {metric_col}", f"{metric_max:,.2f}", "", "#ef4444")

st.markdown("<hr>", unsafe_allow_html=True)

# ----------------- DATA PREVIEW ----------------- #

with st.expander("🔍 Preview Data (first 20 rows)", expanded=False):
    st.dataframe(filtered_df.head(20), use_container_width=True)

# ===================== SECTION: DATA QUALITY INSIGHTS ===================== #

st.markdown('<div class="section-header">Data Quality Insights</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-subtext">Check numeric ranges and missing-value patterns before deeper analysis.</div>',
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)

with col1:
    st.write("**Numeric Columns Summary**")
    num_cols_present = filtered_df.select_dtypes(include="number").columns.tolist()
    if num_cols_present:
        st.dataframe(filtered_df[num_cols_present].describe().T)
    else:
        st.info("No numeric columns to summarise.")

with col2:
    missing_series = filtered_df.isnull().sum()

    if missing_series.any():
        st.write("**Missing Value Analysis**")

        total_missing = int(missing_series.sum())
        total_cells_f = int(filtered_df.size)
        missing_pct_overall = (total_missing / total_cells_f * 100) if total_cells_f > 0 else 0

        non_zero = missing_series[missing_series > 0].sort_values(ascending=False)

        st.write(
            f"- Total missing cells: **{total_missing}** "
            f"({missing_pct_overall:.1f}% of all values)"
        )
        st.write(f"- Columns with missing values: **{len(non_zero)}**")

        for col_name, miss_count in non_zero.items():
            col_pct = miss_count / len(filtered_df) * 100 if len(filtered_df) > 0 else 0
            st.write(
                f"  • **{col_name}** → {miss_count} rows missing "
                f"({col_pct:.1f}% of rows)"
            )

        most_missing_col = non_zero.index[0]
        most_missing_pct = (
            non_zero.iloc[0] / len(filtered_df) * 100 if len(filtered_df) > 0 else 0
        )

        st.markdown("---")
        st.write("**Interpretation:**")

        if most_missing_pct > 70 and len(non_zero) == 1:
            st.info(
                f"Most missing data is concentrated in **{most_missing_col}** "
                f"({most_missing_pct:.1f}% of rows). "
                "This often means that field only applies to a subset of records "
                "(e.g., exit date, closure date). The rest of the dataset is mostly complete."
            )
        elif missing_pct_overall < 5:
            st.info(
                "Overall missing data is **very low** (<5%). "
                "The dataset is in good shape for most analyses."
            )
        elif missing_pct_overall < 15:
            st.info(
                "There is **moderate** missing data. "
                "Consider imputing or filtering high-missing columns for more accurate models."
            )
        else:
            st.info(
                "Missing data is **relatively high** in multiple columns. "
                "You may need to clean or drop some columns/rows."
            )
    else:
        st.write("No missing values detected. ✅")

st.markdown("<hr>", unsafe_allow_html=True)

# ===================== SECTION: DASHBOARD CHARTS ===================== #

st.markdown('<div class="section-header">Dashboard Views</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-subtext">Visual breakdown of the selected metric across distribution, category, and time.</div>',
    unsafe_allow_html=True,
)

# --- Metric distribution ---
st.write("#### Distribution of Selected Metric")
hist_df = metric_series.to_frame(name=metric_col)
if not hist_df.empty:
    metric_chart = (
        alt.Chart(hist_df)
        .mark_bar()
        .encode(
            x=alt.X(f"{metric_col}:Q", bin=alt.Bin(maxbins=30), title=metric_col),
            y=alt.Y("count():Q", title="Count of rows"),
        )
        .properties(height=260)
    )
    st.altair_chart(metric_chart, use_container_width=True)
else:
    st.info("No valid numeric data to plot distribution.")

# --- Metric by category ---
if dim_col != "None":
    st.write(f"#### {metric_col} by {dim_col}")
    cat_df = (
        filtered_df.groupby(dim_col)[metric_col]
        .sum()
        .reset_index()
        .sort_values(metric_col, ascending=False)
        .head(15)
    )
    if not cat_df.empty:
        cat_chart = (
            alt.Chart(cat_df)
            .mark_bar()
            .encode(
                x=alt.X(f"{metric_col}:Q", title=f"Total {metric_col}"),
                y=alt.Y(f"{dim_col}:N", sort="-x", title=dim_col),
                tooltip=[dim_col, metric_col],
            )
            .properties(height=320)
        )
        st.altair_chart(cat_chart, use_container_width=True)
    else:
        st.info("Not enough data to plot category breakdown.")
else:
    st.info("Select a category in the sidebar to see a breakdown by category.")

# --- Time trend ---
if date_col_selected != "None":
    st.write(f"#### {metric_col} over Time ({date_col_selected})")
    dt = pd.to_datetime(filtered_df[date_col_selected], errors="coerce", dayfirst=True)
    ts_df = pd.DataFrame({"date": dt, "value": filtered_df[metric_col]})
    ts_df = ts_df.dropna(subset=["date", "value"])

    if not ts_df.empty:
        ts_agg = (
            ts_df.groupby("date")["value"]
            .sum()
            .reset_index()
            .sort_values("date")
        )

        line_chart = (
            alt.Chart(ts_agg)
            .mark_area(line={'color': '#2563eb'}, opacity=0.35)
            .encode(
                x=alt.X("date:T", title=date_col_selected),
                y=alt.Y("value:Q", title=f"{metric_col} (sum)"),
                tooltip=["date", "value"],
            )
            .properties(height=280)
        )
        st.altair_chart(line_chart, use_container_width=True)
    else:
        st.info("Not enough valid date/metric data to plot a time series.")
else:
    st.info("Select a date column in the sidebar to see a time trend.")

st.markdown("<hr>", unsafe_allow_html=True)

# ===================== SECTION: AI SUMMARY + EXPORT ===================== #

st.markdown('<div class="section-header">AI Summary & Export</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-subtext">Generate a business-friendly summary for the selected metric and layout, and download it as PDF/Word.</div>',
    unsafe_allow_html=True,
)

if st.button("✨ Generate AI Summary & Report"):
    with st.spinner("Calling AI and building report..."):

        # Build KPIs dict
        kpis = {}
        kpis["total_rows"] = total_rows
        kpis["total_columns"] = total_cols
        kpis["metric_column"] = metric_col
        kpis["category_column"] = dim_col if dim_col != "None" else None
        kpis["date_column"] = date_col_selected if date_col_selected != "None" else None
        kpis["metric_total"] = float(metric_total)
        kpis["metric_mean"] = float(metric_mean)
        kpis["metric_min"] = float(metric_min)
        kpis["metric_max"] = float(metric_max)
        kpis["missing_cells"] = missing_cells
        kpis["missing_pct"] = missing_pct
        kpis["duplicate_rows"] = duplicate_rows
        kpis["duplicate_pct"] = duplicate_pct
        kpis["missing_values"] = filtered_df.isnull().sum().to_dict()
        kpis["data_types"] = {col: str(dtype) for col, dtype in filtered_df.dtypes.items()}

        categorical_summary = {}
        if dim_col != "None":
            vc = filtered_df[dim_col].value_counts().head(10)
            categorical_summary[dim_col] = {
                "unique_values": int(filtered_df[dim_col].nunique(dropna=True)),
                "top_values": vc.to_dict(),
            }

        kpis["categorical_summary"] = categorical_summary

        with open("kpis.json", "w", encoding="utf-8") as f:
            json.dump(kpis, f, indent=4)

        # Build AI prompt
        prompt = f"""
You are an experienced data analyst. You are given summary information about a dataset
and a selected numeric metric that the user cares about.

DATASET OVERVIEW:
- Total rows: {kpis['total_rows']}
- Total columns: {kpis['total_columns']}
- Selected metric column: {kpis['metric_column']}
- Selected category column: {kpis['category_column']}
- Selected date column: {kpis['date_column']}

METRIC STATS:
- Total {metric_col}: {kpis['metric_total']:.2f}
- Average {metric_col}: {kpis['metric_mean']:.2f}
- Min {metric_col}: {kpis['metric_min']:.2f}
- Max {metric_col}: {kpis['metric_max']:.2f}

DATA QUALITY:
- Missing cells: {kpis['missing_cells']} ({kpis['missing_pct']:.1f}% of all values)
- Duplicate rows: {kpis['duplicate_rows']} ({kpis['duplicate_pct']:.1f}% of rows)

MISSING VALUES PER COLUMN:
"""
        for col, missing in kpis["missing_values"].items():
            prompt += f"- {col}: {missing} missing\n"

        if categorical_summary:
            prompt += "\nCATEGORY SUMMARY:\n"
            for col, info in categorical_summary.items():
                prompt += f"- {col}: {info['unique_values']} unique values; top values:\n"
                for val, count in info["top_values"].items():
                    prompt += f"    • '{val}' → {count} rows\n"

        prompt += f"""
TASK:
Using the information above, write a clear, non-technical summary for a business user.

1. Describe what the dataset looks like overall.
2. Explain how the selected metric "{metric_col}" behaves (scale, spread, high/low values).
3. If a category column is selected, comment on any dominant categories based on the metric.
4. Comment briefly on data quality (missing values, duplicates) and whether it's a concern.
5. Suggest 3–5 possible analytical questions or next steps the user could explore using this dataset.

Keep the tone concise, professional, and easy to understand.
"""

        load_dotenv()
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            st.error("GROQ_API_KEY not found in .env file. Please add it to .env and restart.")
            st.stop()

        client = Groq(api_key=api_key)

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are an expert data analyst."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=700,
        )

        summary = response.choices[0].message.content

        st.markdown("### 📄 AI Summary")
        st.write(summary)

        generate_pdf("ai_summary.txt", "AI_Report.pdf")
        generate_docx("ai_summary.txt", "AI_Report.docx")

        with open("AI_Report.pdf", "rb") as f:
            st.download_button(
                "⬇ Download PDF Report", f, file_name="AI_Report.pdf"
            )

        with open("AI_Report.docx", "rb") as f:
            st.download_button(
                "⬇ Download Word Report", f, file_name="AI_Report.docx"
            )
