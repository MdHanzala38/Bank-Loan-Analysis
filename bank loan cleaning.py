"""
Bank Loan Dataset — Data Cleaning & Date Parsing
==================================================
Phase 2 of the Bank Loan Analysis project.
Covers: dropping junk columns, fixing dtypes, handling nulls,
parsing dates, removing duplicates, capping outliers.

Run AFTER bank_loan_inspection.py.

Usage:
    pip install pandas numpy sqlalchemy pymysql
    python bank_loan_cleaning.py
"""

import pandas as pd
import numpy as np
import warnings
import os

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
CSV_PATH    = "loan.csv"          # your raw file
OUTPUT_CSV  = "loan_cleaned.csv"  # cleaned output
SAMPLE_ROWS = None                # e.g. 200_000 for large files

os.makedirs("cleaning_logs", exist_ok=True)

# ─────────────────────────────────────────────
# STEP 1 — Load raw data
# ─────────────────────────────────────────────
print("=" * 60)
print("STEP 1: Loading raw data")
print("=" * 60)

df = pd.read_csv(CSV_PATH, nrows=SAMPLE_ROWS, low_memory=False)
original_shape = df.shape
print(f"Raw shape: {df.shape[0]:,} rows × {df.shape[1]} columns")

# ─────────────────────────────────────────────
# STEP 2 — Drop columns with >40% missing values
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 2: Dropping high-missing columns (>40% null)")
print("=" * 60)

missing_pct = df.isnull().mean() * 100
drop_cols   = missing_pct[missing_pct > 40].index.tolist()

print(f"Dropping {len(drop_cols)} columns:")
for col in drop_cols:
    print(f"   ✗ {col:<45} ({missing_pct[col]:.1f}% missing)")

df.drop(columns=drop_cols, inplace=True)
print(f"\nShape after drop: {df.shape[0]:,} rows × {df.shape[1]} columns")

# ─────────────────────────────────────────────
# STEP 3 — Remove duplicate loan IDs
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 3: Removing duplicate loan IDs")
print("=" * 60)

id_col = next((c for c in ["id", "loan_id", "member_id"] if c in df.columns), None)
if id_col:
    dupes = df.duplicated(subset=[id_col]).sum()
    df.drop_duplicates(subset=[id_col], keep="first", inplace=True)
    print(f"Removed {dupes:,} duplicate rows on '{id_col}'")
else:
    dupes = df.duplicated().sum()
    df.drop_duplicates(inplace=True)
    print(f"No ID column found — removed {dupes:,} fully duplicate rows")

# ─────────────────────────────────────────────
# STEP 4 — Parse & extract date columns
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 4: Parsing dates")
print("=" * 60)

# Lending Club stores dates as "Jan-2015" format
DATE_COLUMNS = [c for c in [
    "issue_d", "issue_date",
    "last_pymnt_d", "last_credit_pull_d",
    "next_pymnt_d", "earliest_cr_line"
] if c in df.columns]

def parse_lc_date(series, col_name):
    """Handle both 'Jan-2015' and standard ISO date formats."""
    parsed = pd.to_datetime(series, format="%b-%Y", errors="coerce")
    if parsed.isnull().mean() > 0.5:                      # fallback to mixed
        parsed = pd.to_datetime(series, format="mixed", errors="coerce")
    null_count = parsed.isnull().sum()
    print(f"   ✅ '{col_name}': parsed OK — {null_count:,} unparseable values set to NaT")
    return parsed

for col in DATE_COLUMNS:
    df[col] = parse_lc_date(df[col], col)

# Extract time features from the primary issue date
issue_col = next((c for c in ["issue_d", "issue_date"] if c in df.columns), None)
if issue_col:
    df["issue_year"]    = df[issue_col].dt.year.astype("Int64")
    df["issue_month"]   = df[issue_col].dt.month.astype("Int64")
    df["issue_quarter"] = df[issue_col].dt.to_period("Q").astype(str)
    df["issue_month_name"] = df[issue_col].dt.strftime("%b")

    print(f"\n   Extracted from '{issue_col}':")
    print(f"   issue_year   → {sorted(df['issue_year'].dropna().astype(int).unique().tolist())}")
    print(f"   Date range   → {df[issue_col].min().date()} to {df[issue_col].max().date()}")

# ─────────────────────────────────────────────
# STEP 5 — Fix data types
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 5: Fixing data types")
print("=" * 60)

# 5a — Strip % from rate columns and convert to float
pct_cols = [c for c in ["int_rate", "revol_util"] if c in df.columns]
for col in pct_cols:
    if df[col].dtype == object:
        df[col] = df[col].str.replace("%", "", regex=False).str.strip().astype(float)
        print(f"   ✅ '{col}': stripped %  → float")
    else:
        print(f"   ✅ '{col}': already numeric")

# 5b — Convert term " 36 months" → integer 36
if "term" in df.columns and df["term"].dtype == object:
    df["term_months"] = df["term"].str.extract(r"(\d+)").astype("Int64")
    print(f"   ✅ 'term': extracted numeric months → 'term_months'")

# 5c — Employment length: "10+ years" → 10
if "emp_length" in df.columns:
    mapping = {
        "< 1 year": 0, "1 year": 1, "2 years": 2, "3 years": 3,
        "4 years": 4, "5 years": 5, "6 years": 6, "7 years": 7,
        "8 years": 8, "9 years": 9, "10+ years": 10
    }
    df["emp_length_years"] = df["emp_length"].map(mapping)
    print(f"   ✅ 'emp_length': mapped to numeric 'emp_length_years'")

# 5d — Downcast numeric columns to save memory
numeric_cols = df.select_dtypes(include=[np.number]).columns
df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, downcast="float")
print(f"   ✅ Downcasted {len(numeric_cols)} numeric columns")

# ─────────────────────────────────────────────
# STEP 6 — Fill missing values
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 6: Handling remaining missing values")
print("=" * 60)

# Numeric: fill with column median
num_cols_with_nulls = [
    c for c in df.select_dtypes(include=[np.number]).columns
    if df[c].isnull().sum() > 0
]
for col in num_cols_with_nulls:
    median = df[col].median()
    df[col].fillna(median, inplace=True)
print(f"   ✅ Filled {len(num_cols_with_nulls)} numeric columns with median")

# Categorical: fill with mode or "Unknown"
cat_cols_with_nulls = [
    c for c in df.select_dtypes(include=["object"]).columns
    if df[c].isnull().sum() > 0
]
for col in cat_cols_with_nulls:
    if df[col].isnull().mean() < 0.1:          # <10% missing → use mode
        mode_val = df[col].mode()[0]
        df[col].fillna(mode_val, inplace=True)
    else:
        df[col].fillna("Unknown", inplace=True)
print(f"   ✅ Filled {len(cat_cols_with_nulls)} categorical columns with mode / 'Unknown'")

# Nuclear option — fill any leftover nulls

for col in df.columns:
    if df[col].isnull().sum() == 0:
        continue
    if pd.api.types.is_datetime64_any_dtype(df[col]):
        df[col].fillna(pd.NaT, inplace=True)          # ← datetime → NaT
    elif df[col].dtype in [np.float32, np.float64, np.int32, np.int64]:
        df[col].fillna(df[col].median(), inplace=True) # ← numeric → median
    else:
        df[col].fillna("Unknown", inplace=True)        # ← text → "Unknown"

print(f"Nulls remaining: {df.isnull().sum().sum():,}")

# ─────────────────────────────────────────────
# STEP 7 — Cap outliers (IQR method)
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 7: Capping outliers (IQR method)")
print("=" * 60)

OUTLIER_COLS = [c for c in [
    "annual_inc", "loan_amnt", "funded_amnt",
    "total_pymnt", "dti", "open_acc", "revol_bal"
] if c in df.columns]

for col in OUTLIER_COLS:
    Q1  = df[col].quantile(0.25)
    Q3  = df[col].quantile(0.75)
    IQR = Q3 - Q1
    lo  = max(0, Q1 - 1.5 * IQR)   # ← never go below 0
    hi  = Q3 + 1.5 * IQR
    n_outliers = ((df[col] < lo) | (df[col] > hi)).sum()
    df[col] = df[col].clip(lower=lo, upper=hi)
    print(f"   ✅ '{col}': capped {n_outliers:,}  [floor={lo:,.0f}, cap={hi:,.0f}]")

# ─────────────────────────────────────────────
# STEP 8 — Add Good / Bad loan label
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 8: Good vs Bad loan label")
print("=" * 60)

if "loan_status" in df.columns:
    good = ["Fully Paid", "Current"]
    bad  = ["Charged Off", "Default", "Late (31-120 days)",
            "Late (16-30 days)", "In Grace Period"]
    df["loan_category"] = np.where(
        df["loan_status"].isin(good), "Good",
        np.where(df["loan_status"].isin(bad), "Bad", "Other")
    )
    print(df["loan_category"].value_counts().to_string())

# ─────────────────────────────────────────────
# STEP 9 — Save cleaned file
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 9: Saving cleaned CSV")
print("=" * 60)

df.to_csv(OUTPUT_CSV, index=False)
print(f"✅ Saved → {OUTPUT_CSV}")
print(f"   Original : {original_shape[0]:,} rows × {original_shape[1]} cols")
print(f"   Cleaned  : {df.shape[0]:,} rows × {df.shape[1]} cols")
print(f"   Remaining nulls: {df.isnull().sum().sum():,}")

# ─────────────────────────────────────────────
# CLEANING SUMMARY LOG
# ─────────────────────────────────────────────
log_lines = [
    "Bank Loan Cleaning Summary",
    f"Original  : {original_shape}",
    f"Final     : {df.shape}",
    f"Cols dropped (>40% null): {len(drop_cols)}",
    f"Null count remaining    : {df.isnull().sum().sum()}",
]
with open("cleaning_logs/cleaning_summary.txt", "w") as f:
    f.write("\n".join(log_lines))

print("\n✅ Cleaning complete! Next: run KPI calculation (Phase 3)")