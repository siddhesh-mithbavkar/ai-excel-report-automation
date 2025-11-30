# 🚀 AI-Powered Excel Data Analysis & Reporting Tool  
### Instant Dashboards • Data Quality Insights • AI Summary • PDF/Word Export  
Built using **Python, Streamlit, Pandas, Altair, ReportLab & Groq LLM**

---

## 📸 Screenshots
(Add your screenshots inside `/assets` folder and update the paths below)

![Dashboard Screenshot](assets/screenshot1.png)
![AI Summary Screenshot](assets/screenshot2.png)

---

## 🌟 Overview

This project is an **AI-powered data analysis tool** designed to make Excel reporting fast, automated, and business-friendly.  
You can upload **any Excel file**, and the tool will:

- Auto-detect headers  
- Clean percentage & date fields  
- Generate KPI dashboards  
- Visualize trends & distributions  
- Perform data quality analysis  
- Produce AI-written business summaries  
- Export to **PDF** and **Word**  

This is ideal for:

- Data Analysts  
- MIS Executives  
- BI Developers  
- Students building portfolios  
- Freelancers automating client reports  
- Anyone working with Excel data daily  

---

# ✨ Features

### 📂 Upload ANY Excel File
- Reads `.xlsx` / `.xls`  
- Detects header row automatically  
- Handles messy or multi-line headers  
- Cleans numeric, percentage & date columns  

---

### 📊 Interactive Dashboard (Auto-Generated)

Includes:

- KPI Cards  
  - Total rows  
  - Total columns  
  - Missing value %  
  - Duplicate %  
  - Metric totals, average, min, max  
- Metric Distribution (Histogram)  
- Category-wise Breakdown (Top N values)  
- Time-Series Trend  
- Modern Power BI–style UI  

---

### 🧪 Data Quality Insights

- Missing values per column  
- Duplicate record check  
- Numeric column summary  
- Smart interpretation (e.g., high missing values in exit date = active employees)

---

### 🤖 AI Summary Generation (Groq LLM)

Automatically generates a business-ready summary:

- Dataset overview  
- KPI interpretation  
- Category insights  
- Data quality comments  
- Recommendations  
- Next-step analysis suggestions  

Model used:

- `llama3-8b-instant` via Groq API

---

### 📄 Export to PDF & Word

Exports AI summary into:

- `AI_Report.pdf`  
- `AI_Report.docx`  

Useful for:

- Monthly reporting  
- Email attachments  
- Client deliverables  
- Management reviews  

---

## 🛠 Tech Stack

| Area | Technology |
|------|------------|
| Frontend UI | Streamlit |
| Backend / Logic | Python |
| Data | Pandas, NumPy |
| Charts | Altair |
| AI Engine | Groq LLM |
| Export | ReportLab, python-docx |
| File Handling | openpyxl |
| Environment | python-dotenv |

---


## 🔑 Environment Variables

Create a .env file in the project folder and add:
GROQ_API_KEY=your_api_key_here

## ▶️ Run the App
streamlit run app.py

After running, the app will open in your browser:
http://localhost:8501


