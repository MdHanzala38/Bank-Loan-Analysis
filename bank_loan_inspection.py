"""
Bank Loan Dataset - Load & Inspect
====================================
Run this script after downloading your dataset from Kaggle.
Works with Lending Club dataset and most bank loan CSVs.

Usage:
    pip install pandas numpy matplotlib seaborn
    python bank_loan_inspection.py
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import warnings
import os

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# CONFIGURATION — update this path to your file
# ─────────────────────────────────────────────
CSV_PATH = "loan.csv"          # change to your actual file path
SAMPLE_ROWS = None             # set e.g. 200_000 to load a sample for large files
OUTPUT_DIR = "loan_inspection_output"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─────────────────────────────────────────────
# STEP 1 — Load the dataset
# ─────────────────────────────────────────────
print("=" * 60)
print("STEP 1: Loading dataset")
print("=" * 60)

df = pd.read_csv(
    CSV_PATH,
    nrows=SAMPLE_ROWS,
    low_memory=False
)

print(f"✅ Loaded: {df.shape[0]:,} rows × {df.shape[1]} columns")
print(f"   Memory usage: {df.memory_usage(deep=True).sum() / 1e6:.1f} MB\n")

# ─────────────────────────────────────────────
# STEP 2 — Basic shape & dtypes
# ─────────────────────────────────────────────
print("=" * 60)
print("STEP 2: Column types overview")
print("=" * 60)

type_counts = df.dtypes.value_counts()
for dtype, count in type_counts.items():
    print(f"   {str(dtype):<12} → {count} columns")

print("\nFirst 5 rows:")
print(df.head())

# ─────────────────────────────────────────────
# STEP 3 — Missing values analysis
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 3: Missing values")
print("=" * 60)

missing = (
    df.isnull()
    .sum()
    .rename("missing_count")
    .to_frame()
)
missing["missing_pct"] = (missing["missing_count"] / len(df) * 100).round(2)
missing = missing[missing["missing_count"] > 0].sort_values("missing_pct", ascending=False)

print(f"Columns with missing values: {len(missing)} / {df.shape[1]}")
print(missing.head(20).to_string())

# Flag columns to drop (>40% missing)
drop_candidates = missing[missing["missing_pct"] > 40].index.tolist()
print(f"\n⚠️  Columns with >40% missing (consider dropping): {len(drop_candidates)}")
for col in drop_candidates[:10]:
    print(f"   - {col} ({missing.loc[col, 'missing_pct']}% missing)")

# ─────────────────────────────────────────────
# STEP 4 — Key column summary (loan-specific)
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 4: Key columns summary")
print("=" * 60)

key_numeric = [c for c in [
    "loan_amnt", "funded_amnt", "funded_amnt_inv",
    "total_pymnt", "int_rate", "dti", "annual_inc",
    "installment", "open_acc", "revol_util"
] if c in df.columns]

key_categorical = [c for c in [
    "loan_status", "grade", "sub_grade", "purpose",
    "home_ownership", "emp_length", "term",
    "addr_state", "verification_status"
] if c in df.columns]

if key_numeric:
    print("\nNumeric columns:")
    print(df[key_numeric].describe().round(2).T[
        ["count", "mean", "min", "50%", "max"]
    ].rename(columns={"50%": "median"}).to_string())

if key_categorical:
    print("\nCategorical columns — top value counts:")
    for col in key_categorical:
        vc = df[col].value_counts(dropna=False)
        top = vc.head(5).to_dict()
        print(f"\n  {col} ({df[col].nunique()} unique):")
        for val, cnt in top.items():
            pct = cnt / len(df) * 100
            print(f"    {str(val):<30} {cnt:>8,}  ({pct:.1f}%)")

# ─────────────────────────────────────────────
# STEP 5 — Good vs Bad loan classification
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 5: Good vs Bad loan classification")
print("=" * 60)

if "loan_status" in df.columns:
    good_statuses  = ["Fully Paid", "Current"]
    bad_statuses   = ["Charged Off", "Default", "Late (31-120 days)",
                      "Late (16-30 days)", "In Grace Period", "Does not meet the credit policy. Status:Charged Off"]

    df["loan_category"] = np.where(
        df["loan_status"].isin(good_statuses), "Good",
        np.where(df["loan_status"].isin(bad_statuses), "Bad", "Other")
    )

    cat_counts = df["loan_category"].value_counts()
    total = len(df)
    print("Loan category breakdown:")
    for cat, cnt in cat_counts.items():
        print(f"   {cat:<8} → {cnt:>8,}  ({cnt/total*100:.1f}%)")
else:
    print("⚠️  'loan_status' column not found — skipping classification.")
    print("   Check your column names with: print(df.columns.tolist())")

# ─────────────────────────────────────────────
# STEP 6 — Date parsing (issue_d / issue_date)
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 6: Date parsing")
print("=" * 60)

date_col = next((c for c in ["issue_d", "issue_date", "date"] if c in df.columns), None)

if date_col:
    df[date_col] = pd.to_datetime(df[date_col], format="mixed", errors="coerce")
    df["issue_year"]  = df[date_col].dt.year
    df["issue_month"] = df[date_col].dt.month
    df["issue_quarter"] = df[date_col].dt.to_period("Q").astype(str)

    print(f"✅ Parsed '{date_col}' successfully")
    print(f"   Date range: {df[date_col].min().date()} → {df[date_col].max().date()}")
    print(f"   Years covered: {sorted(df['issue_year'].dropna().astype(int).unique().tolist())}")
else:
    print("⚠️  No date column found. Check for 'issue_d' or 'issue_date' in your dataset.")

# ─────────────────────────────────────────────
# STEP 7 — Quick KPIs
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 7: Quick KPIs")
print("=" * 60)

def kpi(col, agg="sum"):
    if col not in df.columns:
        return "N/A"
    val = df[col].sum() if agg == "sum" else df[col].mean()
    return f"${val:,.0f}" if agg == "sum" else f"{val:.2f}%"

total_apps    = f"{len(df):,}"
funded        = kpi("funded_amnt")
received      = kpi("total_pymnt")
avg_int_rate  = f"{df['int_rate'].mean():.2f}%" if "int_rate" in df.columns else "N/A"
avg_dti       = f"{df['dti'].mean():.2f}" if "dti" in df.columns else "N/A"

print(f"   Total applications : {total_apps}")
print(f"   Total funded       : {funded}")
print(f"   Total received     : {received}")
print(f"   Avg interest rate  : {avg_int_rate}")
print(f"   Avg DTI            : {avg_dti}")

# ─────────────────────────────────────────────
# STEP 8 — Visualisations (saved to output dir)
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 8: Generating charts → saved to", OUTPUT_DIR)
print("=" * 60)

sns.set_theme(style="whitegrid", palette="muted")

# 8a — Loan status distribution
if "loan_status" in df.columns:
    fig, ax = plt.subplots(figsize=(10, 4))
    vc = df["loan_status"].value_counts()
    bars = ax.barh(vc.index, vc.values, color=sns.color_palette("muted", len(vc)))
    ax.set_title("Loan Status Distribution", fontsize=14, fontweight="bold")
    ax.set_xlabel("Number of Loans")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    for bar in bars:
        ax.text(bar.get_width() + vc.max() * 0.01, bar.get_y() + bar.get_height() / 2,
                f"{bar.get_width():,.0f}", va="center", fontsize=9)
    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "01_loan_status.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"   ✅ {path}")

# 8b — Good vs Bad pie chart
if "loan_category" in df.columns:
    fig, ax = plt.subplots(figsize=(5, 5))
    cat = df["loan_category"].value_counts()
    colors = {"Good": "#4CAF50", "Bad": "#F44336", "Other": "#9E9E9E"}
    ax.pie(cat, labels=cat.index, autopct="%1.1f%%",
           colors=[colors.get(c, "#999") for c in cat.index],
           startangle=90, wedgeprops=dict(edgecolor="white", linewidth=2))
    ax.set_title("Good vs Bad Loans", fontsize=14, fontweight="bold")
    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "02_good_vs_bad.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"   ✅ {path}")

# 8c — Monthly application trend
if "issue_year" in df.columns and "issue_month" in df.columns:
    trend = (
        df.groupby(["issue_year", "issue_month"])
        .size()
        .reset_index(name="count")
    )
    trend["period"] = pd.to_datetime(
        trend["issue_year"].astype(str) + "-" + trend["issue_month"].astype(str).str.zfill(2)
    )
    trend = trend.sort_values("period")
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(trend["period"], trend["count"], linewidth=2, color="#1976D2")
    ax.fill_between(trend["period"], trend["count"], alpha=0.15, color="#1976D2")
    ax.set_title("Monthly Loan Applications Over Time", fontsize=14, fontweight="bold")
    ax.set_ylabel("Applications")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "03_monthly_trend.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"   ✅ {path}")

# 8d — Missing values heatmap (top 20 columns)
fig, ax = plt.subplots(figsize=(12, 4))
top_missing = missing.head(20)
ax.barh(top_missing.index, top_missing["missing_pct"], color="#EF5350")
ax.axvline(40, color="black", linestyle="--", linewidth=1, label="40% threshold")
ax.set_title("Missing Data % — Top 20 Columns", fontsize=14, fontweight="bold")
ax.set_xlabel("Missing %")
ax.legend()
plt.tight_layout()
path = os.path.join(OUTPUT_DIR, "04_missing_values.png")
plt.savefig(path, dpi=150)
plt.close()
print(f"   ✅ {path}")

# 8e — Interest rate distribution by loan category
if "int_rate" in df.columns and "loan_category" in df.columns:
    fig, ax = plt.subplots(figsize=(10, 4))
    for cat, color in [("Good", "#4CAF50"), ("Bad", "#F44336")]:
        subset = df[df["loan_category"] == cat]["int_rate"].dropna()
        if len(subset) > 0:
            subset.plot.kde(ax=ax, label=cat, color=color, linewidth=2)
    ax.set_title("Interest Rate Distribution: Good vs Bad Loans", fontsize=14, fontweight="bold")
    ax.set_xlabel("Interest Rate (%)")
    ax.legend()
    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "05_int_rate_by_category.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"   ✅ {path}")

# ─────────────────────────────────────────────
# DONE
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("✅ Inspection complete!")
print(f"   Charts saved to: ./{OUTPUT_DIR}/")
print("   Next step: Run the data cleaning script (Phase 2)")
print("=" * 60)
