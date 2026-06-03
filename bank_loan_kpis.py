"""
Bank Loan Analysis — KPI Calculation in Python
================================================
Phase 3: Calculates all KPIs from loan_cleaned.csv
and exports results to Excel for Power BI use.

Usage:
    pip install pandas numpy openpyxl
    python bank_loan_kpis.py
"""

import pandas as pd
import numpy as np
import warnings
import os

warnings.filterwarnings("ignore")

CSV_PATH   = "loan_cleaned.csv"
OUTPUT_DIR = "kpi_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Load cleaned data ─────────────────────────
print("Loading loan_cleaned.csv ...")
df = pd.read_csv(CSV_PATH, low_memory=False)
print(f"Loaded: {df.shape[0]:,} rows × {df.shape[1]} cols\n")

# Ensure date columns parsed
for col in ["issue_date_parsed", "issue_d"]:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")

# Ensure year/month columns exist
if "issue_year" not in df.columns and "issue_date_parsed" in df.columns:
    df["issue_year"]  = df["issue_date_parsed"].dt.year
    df["issue_month"] = df["issue_date_parsed"].dt.month

results = {}   # store all KPI DataFrames here

# ─────────────────────────────────────────────
# KPI 1 — Summary Dashboard (single-row)
# ─────────────────────────────────────────────
print("Calculating KPI 1: Summary dashboard ...")

good = df[df["loan_category"] == "Good"]
bad  = df[df["loan_category"] == "Bad"]

summary = pd.DataFrame([{
    "total_applications"  : len(df),
    "good_loan_count"     : len(good),
    "bad_loan_count"      : len(bad),
    "good_loan_pct"       : round(len(good) / len(df) * 100, 2),
    "bad_loan_pct"        : round(len(bad)  / len(df) * 100, 2),
    "total_funded_M"      : round(df["funded_amnt"].sum() / 1e6, 2),
    "total_received_M"    : round(df["total_pymnt"].sum() / 1e6, 2),
    "net_M"               : round((df["total_pymnt"].sum() - df["funded_amnt"].sum()) / 1e6, 2),
    "collection_rate_pct" : round(df["total_pymnt"].sum() / df["funded_amnt"].sum() * 100, 2),
    "avg_int_rate"        : round(df["int_rate_num"].mean() if "int_rate_num" in df.columns else df["int_rate"].mean(), 2),
    "avg_dti"             : round(df["dti"].mean(), 2),
    "avg_loan_amount"     : round(df["funded_amnt"].mean(), 2),
}])

results["1_Summary"] = summary
print(summary.T.to_string(header=False))

# ─────────────────────────────────────────────
# KPI 2 — Good Loan KPIs
# ─────────────────────────────────────────────
print("\nCalculating KPI 2: Good loan KPIs ...")

good_kpis = pd.DataFrame([{
    "good_applications"    : len(good),
    "good_pct"             : round(len(good) / len(df) * 100, 2),
    "good_funded_M"        : round(good["funded_amnt"].sum() / 1e6, 2),
    "good_received_M"      : round(good["total_pymnt"].sum() / 1e6, 2),
    "good_avg_int_rate"    : round(good["int_rate_num"].mean() if "int_rate_num" in df.columns else good["int_rate"].mean(), 2),
    "good_avg_dti"         : round(good["dti"].mean(), 2),
}])
results["2_Good_Loans"] = good_kpis
print(good_kpis.T.to_string(header=False))

# ─────────────────────────────────────────────
# KPI 3 — Bad Loan KPIs
# ─────────────────────────────────────────────
print("\nCalculating KPI 3: Bad loan KPIs ...")

bad_kpis = pd.DataFrame([{
    "bad_applications"     : len(bad),
    "bad_pct"              : round(len(bad) / len(df) * 100, 2),
    "bad_funded_M"         : round(bad["funded_amnt"].sum() / 1e6, 2),
    "bad_received_M"       : round(bad["total_pymnt"].sum() / 1e6, 2),
    "bad_loan_loss_M"      : round((bad["funded_amnt"].sum() - bad["total_pymnt"].sum()) / 1e6, 2),
    "bad_avg_int_rate"     : round(bad["int_rate_num"].mean() if "int_rate_num" in df.columns else bad["int_rate"].mean(), 2),
    "bad_avg_dti"          : round(bad["dti"].mean(), 2),
}])
results["3_Bad_Loans"] = bad_kpis
print(bad_kpis.T.to_string(header=False))

# ─────────────────────────────────────────────
# KPI 4 — Monthly Trend with MoM change
# ─────────────────────────────────────────────
print("\nCalculating KPI 4: Monthly trend ...")

int_col = "int_rate_num" if "int_rate_num" in df.columns else "int_rate"

monthly = (
    df.groupby(["issue_year", "issue_month"])
    .agg(
        applications    = ("funded_amnt", "count"),
        funded_M        = ("funded_amnt", lambda x: round(x.sum() / 1e6, 2)),
        received_M      = ("total_pymnt", lambda x: round(x.sum() / 1e6, 2)),
        avg_int_rate    = (int_col, lambda x: round(x.mean(), 2)),
        avg_dti         = ("dti", lambda x: round(x.mean(), 2)),
        good_loans      = ("loan_category", lambda x: (x == "Good").sum()),
        bad_loans       = ("loan_category", lambda x: (x == "Bad").sum()),
    )
    .reset_index()
    .sort_values(["issue_year", "issue_month"])
)

monthly["bad_loan_rate_pct"] = round(monthly["bad_loans"] / monthly["applications"] * 100, 2)
monthly["apps_mom_change_pct"] = monthly["applications"].pct_change().mul(100).round(2)
monthly["funded_mom_change_pct"] = monthly["funded_M"].pct_change().mul(100).round(2)

results["4_Monthly_Trend"] = monthly
print(monthly.tail(6).to_string(index=False))

# ─────────────────────────────────────────────
# KPI 5 — Yearly Summary
# ─────────────────────────────────────────────
print("\nCalculating KPI 5: Yearly summary ...")

yearly = (
    df.groupby("issue_year")
    .agg(
        applications   = ("funded_amnt", "count"),
        funded_M       = ("funded_amnt", lambda x: round(x.sum() / 1e6, 2)),
        received_M     = ("total_pymnt", lambda x: round(x.sum() / 1e6, 2)),
        avg_int_rate   = (int_col, lambda x: round(x.mean(), 2)),
        avg_dti        = ("dti", lambda x: round(x.mean(), 2)),
        good_loans     = ("loan_category", lambda x: (x == "Good").sum()),
        bad_loans      = ("loan_category", lambda x: (x == "Bad").sum()),
    )
    .reset_index()
)
yearly["good_pct"] = round(yearly["good_loans"] / yearly["applications"] * 100, 2)
yearly["bad_pct"]  = round(yearly["bad_loans"]  / yearly["applications"] * 100, 2)

results["5_Yearly_Trend"] = yearly
print(yearly.to_string(index=False))

# ─────────────────────────────────────────────
# KPI 6 — By Loan Grade
# ─────────────────────────────────────────────
print("\nCalculating KPI 6: By grade ...")

by_grade = (
    df.groupby("grade")
    .agg(
        total_loans    = ("funded_amnt", "count"),
        funded_M       = ("funded_amnt", lambda x: round(x.sum() / 1e6, 2)),
        avg_int_rate   = (int_col, lambda x: round(x.mean(), 2)),
        avg_dti        = ("dti", lambda x: round(x.mean(), 2)),
        good_loans     = ("loan_category", lambda x: (x == "Good").sum()),
        bad_loans      = ("loan_category", lambda x: (x == "Bad").sum()),
    )
    .reset_index()
)
by_grade["bad_rate_pct"] = round(by_grade["bad_loans"] / by_grade["total_loans"] * 100, 2)

results["6_By_Grade"] = by_grade
print(by_grade.to_string(index=False))

# ─────────────────────────────────────────────
# KPI 7 — By Purpose
# ─────────────────────────────────────────────
print("\nCalculating KPI 7: By purpose ...")

by_purpose = (
    df.groupby("purpose")
    .agg(
        total_loans    = ("funded_amnt", "count"),
        funded_M       = ("funded_amnt", lambda x: round(x.sum() / 1e6, 2)),
        avg_loan_amnt  = ("funded_amnt", lambda x: round(x.mean(), 2)),
        avg_int_rate   = (int_col, lambda x: round(x.mean(), 2)),
        bad_loans      = ("loan_category", lambda x: (x == "Bad").sum()),
    )
    .reset_index()
    .sort_values("total_loans", ascending=False)
)
by_purpose["bad_rate_pct"] = round(by_purpose["bad_loans"] / by_purpose["total_loans"] * 100, 2)

results["7_By_Purpose"] = by_purpose
print(by_purpose.to_string(index=False))

# ─────────────────────────────────────────────
# KPI 8 — By State (for map visual)
# ─────────────────────────────────────────────
print("\nCalculating KPI 8: By state ...")

by_state = (
    df.groupby("addr_state")
    .agg(
        total_applications = ("funded_amnt", "count"),
        funded_M           = ("funded_amnt", lambda x: round(x.sum() / 1e6, 2)),
        received_M         = ("total_pymnt", lambda x: round(x.sum() / 1e6, 2)),
        avg_int_rate       = (int_col, lambda x: round(x.mean(), 2)),
        bad_loans          = ("loan_category", lambda x: (x == "Bad").sum()),
    )
    .reset_index()
    .sort_values("total_applications", ascending=False)
)
by_state["bad_rate_pct"] = round(by_state["bad_loans"] / by_state["total_applications"] * 100, 2)

results["8_By_State"] = by_state
print(by_state.head(10).to_string(index=False))

# ─────────────────────────────────────────────
# KPI 9 — By Home Ownership
# ─────────────────────────────────────────────
print("\nCalculating KPI 9: By home ownership ...")

by_home = (
    df.groupby("home_ownership")
    .agg(
        total_loans    = ("funded_amnt", "count"),
        avg_loan_amnt  = ("funded_amnt", lambda x: round(x.mean(), 2)),
        avg_income     = ("annual_inc", lambda x: round(x.mean(), 2)),
        avg_dti        = ("dti", lambda x: round(x.mean(), 2)),
        bad_loans      = ("loan_category", lambda x: (x == "Bad").sum()),
    )
    .reset_index()
    .sort_values("total_loans", ascending=False)
)
by_home["bad_rate_pct"] = round(by_home["bad_loans"] / by_home["total_loans"] * 100, 2)

results["9_By_Home_Ownership"] = by_home
print(by_home.to_string(index=False))

# ─────────────────────────────────────────────
# KPI 10 — By Employment Length
# ─────────────────────────────────────────────
print("\nCalculating KPI 10: By employment length ...")

by_emp = (
    df.groupby("emp_length")
    .agg(
        total_loans    = ("funded_amnt", "count"),
        avg_loan_amnt  = ("funded_amnt", lambda x: round(x.mean(), 2)),
        avg_income     = ("annual_inc", lambda x: round(x.mean(), 2)),
        bad_loans      = ("loan_category", lambda x: (x == "Bad").sum()),
    )
    .reset_index()
)
by_emp["bad_rate_pct"] = round(by_emp["bad_loans"] / by_emp["total_loans"] * 100, 2)

results["10_By_Emp_Length"] = by_emp
print(by_emp.to_string(index=False))

# ─────────────────────────────────────────────
# EXPORT — All KPIs to Excel (one sheet per KPI)
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("Exporting all KPIs to Excel ...")

excel_path = os.path.join(OUTPUT_DIR, "bank_loan_kpis.xlsx")
with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
    for sheet_name, data in results.items():
        data.to_excel(writer, sheet_name=sheet_name[:31], index=False)

print(f"✅ Saved → {excel_path}")
print(f"   Sheets: {list(results.keys())}")
print("\n✅ Phase 3 complete! Import bank_loan_kpis.xlsx into Power BI.")
