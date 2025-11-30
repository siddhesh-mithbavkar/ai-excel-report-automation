import pandas as pd
import json
from dotenv import load_dotenv
from groq import Groq
import os

from export_pdf import generate_pdf
from export_docx import generate_docx


# ---------- STEP 1: Generate KPIs ----------

def generate_kpis(excel_path="Orders.xlsx", kpi_path="kpis.json"):
    df = pd.read_excel(excel_path)

    # convert date correctly
    df["Order Date"] = pd.to_datetime(df["Order Date"], dayfirst=True, errors="coerce")

    kpis = {
        "total_orders": len(df),
        "unique_customers": df["CustomerName"].nunique(),
        "unique_order_ids": df["Order ID"].nunique(),
        "orders_by_state": df["State"].value_counts().to_dict(),
        "orders_by_city": df["City"].value_counts().head(10).to_dict(),
        "date_range": {
            "start_date": str(df["Order Date"].min().date()),
            "end_date": str(df["Order Date"].max().date()),
        },
        "missing_values": df.isnull().sum().to_dict(),
        "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
    }

    with open(kpi_path, "w", encoding="utf-8") as f:
        json.dump(kpis, f, indent=4)

    print(f"[OK] KPIs saved to {kpi_path}")


# ---------- STEP 2: Build Prompt from KPIs ----------

def build_prompt(kpi_path="kpis.json", prompt_path="summary_prompt.txt"):
    with open(kpi_path, "r", encoding="utf-8") as f:
        kpis = json.load(f)

    total_orders = kpis.get("total_orders")
    unique_customers = kpis.get("unique_customers")
    unique_order_ids = kpis.get("unique_order_ids")
    orders_by_state = kpis.get("orders_by_state", {})
    orders_by_city = kpis.get("orders_by_city", {})
    date_range = kpis.get("date_range", {})
    missing_values = kpis.get("missing_values", {})
    data_types = kpis.get("data_types", {})

    start_date = date_range.get("start_date")
    end_date = date_range.get("end_date")

    prompt = f"""
You are an experienced business analyst. Based on the following KPIs from an orders dataset, write a clear, concise business summary and key insights.

DATA SUMMARY:
- Date range: {start_date} to {end_date}
- Total orders: {total_orders}
- Unique customers: {unique_customers}
- Unique order IDs: {unique_order_ids}

ORDERS BY STATE:
"""
    for state, count in orders_by_state.items():
        prompt += f"- {state}: {count} orders\n"

    prompt += "\nTOP CITIES BY ORDERS:\n"
    for city, count in orders_by_city.items():
        prompt += f"- {city}: {count} orders\n"

    prompt += "\nMISSING VALUES PER COLUMN:\n"
    for col, missing in missing_values.items():
        prompt += f"- {col}: {missing} missing\n"

    prompt += "\nDATA TYPES:\n"
    for col, dtype in data_types.items():
        prompt += f"- {col}: {dtype}\n"

    prompt += """

TASK:
Using the information above, write:

1. A short executive summary (3–5 lines) explaining overall performance.
2. 3–5 key insights about states and cities (who performs best, any concentration).
3. Any potential data quality comments (based on missing values or data types).
4. 2–3 business recommendations for the sales/operations team.

Keep the language simple, professional, and non-technical. Do not repeat the raw numbers list; instead, interpret them.
"""

    with open(prompt_path, "w", encoding="utf-8") as f:
        f.write(prompt)

    print(f"[OK] Prompt saved to {prompt_path}")


# ---------- STEP 3: Call Groq AI to Generate Summary ----------

def generate_ai_summary(prompt_path="summary_prompt.txt", summary_path="ai_summary.txt"):
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError("GROQ_API_KEY not found in .env file")

    client = Groq(api_key=api_key)

    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt = f.read()

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are an expert business analyst."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=700,
    )

    summary = response.choices[0].message.content

    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary)

    print(f"[OK] AI summary saved to {summary_path}")


# ---------- MAIN PIPELINE ----------

def main():
    excel_path = input("Enter Excel file name (e.g. data.xlsx): ").strip()


    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"{excel_path} not found in the project folder")

    generate_kpis(excel_path)
    build_prompt()
    generate_ai_summary()
    generate_pdf("ai_summary.txt", "AI_Report.pdf")
    generate_docx("ai_summary.txt", "AI_Report.docx")

    print("\n=== FULL PIPELINE COMPLETED ===")
    print("Generated files: kpis.json, summary_prompt.txt, ai_summary.txt, AI_Report.pdf, AI_Report.docx")


if __name__ == "__main__":
    main()
