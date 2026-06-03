# Bank Loan Analysis Dashboard
Dataset Kaggle Link [https://www.kaggle.com/datasets/wordsforthewise/lending-club]
Powerbi File Drive Link [https://drive.google.com/drive/folders/1LWgzNCIH6nYqYuOvSkuBo-ZYiBtmEKpX?usp=drive_link]
An end-to-end data analysis project analysing 2.2 million bank loan records to identify risk patterns, calculate KPIs, and build an interactive Power BI dashboard.

## Project Overview

This project analyses Lending Club loan data (2007–2018) to answer key business questions:
- What percentage of loans are good vs bad?
- Which customer segments have the highest default rates?
- How have loan applications and funding trended over time?
- What factors drive loan defaults?

## Tools Used

| Tool | Purpose |
|---|---|
| Python (pandas, numpy) | Data cleaning and preparation |
| MySQL | Data storage and SQL analysis |
| Power BI | Interactive dashboard |
| GitHub | Version control |

## Project Structure

```
bank-loan-analysis/
├── data/
│   └── data_source.md          # Kaggle dataset link
├── python/
│   ├── bank_loan_inspection.py # Data inspection
│   ├── bank_loan_cleaning.py   # Data cleaning
│   └── bank_loan_kpis.py       # KPI calculation
├── sql/
│   └── bank_loan_complete.sql  # All SQL queries
├── dax/
│   └── bank_loan_dax_measures.dax  # Power BI DAX measures
├── dashboard/
│   └── bank_loan_dashboard.pbix    # Power BI dashboard
└── README.md
```

## Dataset

- Source: Lending Club Loan Data (Kaggle)
- Size: 2,260,668 rows × 145 columns
- Period: 2007–2018
- Link: https://www.kaggle.com/datasets/wordsforthewise/lending-club

## Data Cleaning (Python)

- Dropped 46 columns with >40% missing values (145 → 105 columns)
- Parsed date columns from "Jan-2015" format to datetime
- Converted interest rate strings to numeric (stripped %)
- Mapped employment length to numeric values
- Capped outliers using IQR method
- Classified loans into Good / Bad / Other categories

**Good loan:** Fully Paid, Current
**Bad loan:** Charged Off, Default, Late (31-120 days), Late (16-30 days), In Grace Period

## Key KPIs

| KPI | Value |
|---|---|
| Total Applications | 2,260,668 |
| Total Funded Amount | $33.9bn |
| Total Amount Received | $26.3bn |
| Good Loan % | 86.8% |
| Bad Loan % | 13.1% |
| Bad Loan Loss | $2.19bn |
| Avg Interest Rate | 13.09% |
| Avg DTI | 18.48 |

## Key Insights

1. **Grade is the strongest predictor** — Grade A loans default at ~4%, Grade G at ~36%
2. **60-month loans are riskier** — bad rate nearly double that of 36-month loans (~21% vs ~10%)
3. **Small business loans** have the highest bad rate among all loan purposes
4. **DTI > 30** borrowers default at nearly twice the rate of DTI < 10 borrowers
5. **Renters default more** than mortgage holders or owners
6. **Verification paradox** — verified income borrowers show higher bad rates due to selection bias

## Dashboard Pages

### Page 1 — Summary
- 5 KPI cards with MoM trends
- Good vs Bad loan donut chart
- Good/Bad loan breakdown cards
- Loan status breakdown table

### Page 2 — Overview
- Monthly trend line chart (2007–2018)
- Filled map by US state
- Bad rate by grade bar chart
- Applications by purpose bar chart
- Applications by home ownership donut
- Applications by employment length bar chart

### Page 3 — Details
- 7 interactive slicers (grade, status, purpose, state, term, ownership, year)
- Drill-down loan records table with conditional formatting
- Bad rate by grade chart
- Bad rate by home ownership chart

## How to Run

### Python Scripts
```bash
pip install pandas numpy matplotlib seaborn openpyxl sqlalchemy
cd python/
python bank_loan_inspection.py
python bank_loan_cleaning.py
python bank_loan_kpis.py
```

### SQL Queries
```sql
USE bank_loans;
SOURCE sql/bank_loan_complete.sql;
```

### Power BI Dashboard
1. Open `dashboard/bank_loan_dashboard.pbix` in Power BI Desktop
2. Update data source path if needed: Transform Data → Data source settings
3. Click Refresh

## Project Phases

| Phase | Description |
|---|---|
| 1 | Data collection and understanding |
| 2 | Data cleaning and preparation |
| 3 | KPI calculation |
| 4 | Exploratory and trend analysis |
| 5 | Power BI dashboard development |

## Internship

This project was completed as the final task of a Data Analysis internship at **SyntecxHub**.

---
