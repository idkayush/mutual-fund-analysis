from pathlib import Path
import sqlite3
import pandas as pd
import numpy as np
from sqlalchemy import create_engine


RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
SQL_DIR = Path("sql")
REPORTS_DIR = Path("reports")

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
SQL_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = "bluestock_mf.db"


def read_csv(filename):
    path = RAW_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return pd.read_csv(path)


def save_cleaned(df, filename):
    output_path = PROCESSED_DIR / filename
    df.to_csv(output_path, index=False)
    print(f"Saved cleaned file: {output_path} | Shape: {df.shape}")


def clean_fund_master():
    df = read_csv("01_fund_master.csv")

    df = df.drop_duplicates()
    df["launch_date"] = pd.to_datetime(df["launch_date"], errors="coerce")
    df["amfi_code"] = df["amfi_code"].astype(int)

    text_cols = [
        "fund_house", "scheme_name", "category", "sub_category",
        "plan", "benchmark", "fund_manager", "risk_category",
        "sebi_category_code"
    ]

    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    df = df[df["expense_ratio_pct"].between(0.1, 2.5)]
    df = df[df["exit_load_pct"] >= 0]
    df = df[df["min_sip_amount"] > 0]
    df = df[df["min_lumpsum_amount"] > 0]

    save_cleaned(df, "01_fund_master_cleaned.csv")
    return df


def clean_nav_history():
    df = read_csv("02_nav_history.csv")

    df = df.drop_duplicates()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
    df["amfi_code"] = df["amfi_code"].astype(int)

    df = df.dropna(subset=["amfi_code", "date"])
    df = df.sort_values(["amfi_code", "date"])

    df = df[df["nav"] > 0]

    cleaned_parts = []

    for amfi_code, group in df.groupby("amfi_code"):
        group = group.sort_values("date")
        full_dates = pd.date_range(group["date"].min(), group["date"].max(), freq="D")

        group = group.set_index("date").reindex(full_dates)
        group.index.name = "date"
        group["amfi_code"] = amfi_code
        group["nav"] = group["nav"].ffill()

        group = group.reset_index()
        cleaned_parts.append(group)

    cleaned_df = pd.concat(cleaned_parts, ignore_index=True)
    cleaned_df = cleaned_df.dropna(subset=["nav"])
    cleaned_df = cleaned_df.sort_values(["amfi_code", "date"])

    save_cleaned(cleaned_df, "02_nav_history_cleaned.csv")
    return cleaned_df


def clean_aum_by_fund_house():
    df = read_csv("03_aum_by_fund_house.csv")

    df = df.drop_duplicates()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["fund_house"] = df["fund_house"].astype(str).str.strip()

    df["aum_lakh_crore"] = pd.to_numeric(df["aum_lakh_crore"], errors="coerce")
    df["aum_crore"] = pd.to_numeric(df["aum_crore"], errors="coerce")
    df["num_schemes"] = pd.to_numeric(df["num_schemes"], errors="coerce")

    df = df.dropna(subset=["date", "fund_house"])
    df = df[(df["aum_lakh_crore"] > 0) & (df["aum_crore"] > 0) & (df["num_schemes"] > 0)]

    save_cleaned(df, "03_aum_by_fund_house_cleaned.csv")
    return df


def clean_monthly_sip_inflows():
    df = read_csv("04_monthly_sip_inflows.csv")

    df = df.drop_duplicates()
    df["month"] = pd.to_datetime(df["month"], errors="coerce")

    numeric_cols = [
        "sip_inflow_crore", "active_sip_accounts_crore",
        "new_sip_accounts_lakh", "sip_aum_lakh_crore",
        "yoy_growth_pct"
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["month"])
    df = df[df["sip_inflow_crore"] > 0]

    save_cleaned(df, "04_monthly_sip_inflows_cleaned.csv")
    return df


def clean_category_inflows():
    df = read_csv("05_category_inflows.csv")

    df = df.drop_duplicates()
    df["month"] = pd.to_datetime(df["month"], errors="coerce")
    df["category"] = df["category"].astype(str).str.strip()
    df["net_inflow_crore"] = pd.to_numeric(df["net_inflow_crore"], errors="coerce")

    df = df.dropna(subset=["month", "category", "net_inflow_crore"])

    save_cleaned(df, "05_category_inflows_cleaned.csv")
    return df


def clean_industry_folio_count():
    df = read_csv("06_industry_folio_count.csv")

    df = df.drop_duplicates()
    df["month"] = pd.to_datetime(df["month"], errors="coerce")

    numeric_cols = [
        "total_folios_crore", "equity_folios_crore",
        "debt_folios_crore", "hybrid_folios_crore",
        "others_folios_crore"
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["month"])
    df = df[df["total_folios_crore"] > 0]

    save_cleaned(df, "06_industry_folio_count_cleaned.csv")
    return df


def clean_scheme_performance():
    df = read_csv("07_scheme_performance.csv")

    df = df.drop_duplicates()
    df["amfi_code"] = df["amfi_code"].astype(int)

    numeric_cols = [
        "return_1yr_pct", "return_3yr_pct", "return_5yr_pct",
        "benchmark_3yr_pct", "alpha", "beta", "sharpe_ratio",
        "sortino_ratio", "std_dev_ann_pct", "max_drawdown_pct",
        "aum_crore", "expense_ratio_pct", "morningstar_rating"
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["performance_anomaly_flag"] = False

    return_cols = ["return_1yr_pct", "return_3yr_pct", "return_5yr_pct"]
    for col in return_cols:
        df.loc[df[col].isna(), "performance_anomaly_flag"] = True
        df.loc[(df[col] < -100) | (df[col] > 100), "performance_anomaly_flag"] = True

    df.loc[~df["expense_ratio_pct"].between(0.1, 2.5), "performance_anomaly_flag"] = True

    df = df[df["expense_ratio_pct"].between(0.1, 2.5)]
    df = df[df["aum_crore"] > 0]

    text_cols = ["scheme_name", "fund_house", "category", "plan", "risk_grade"]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    save_cleaned(df, "07_scheme_performance_cleaned.csv")
    return df


def clean_investor_transactions():
    df = read_csv("08_investor_transactions.csv")

    df = df.drop_duplicates()
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    df["amfi_code"] = df["amfi_code"].astype(int)
    df["amount_inr"] = pd.to_numeric(df["amount_inr"], errors="coerce")

    transaction_map = {
        "sip": "SIP",
        "sips": "SIP",
        "lumpsum": "Lumpsum",
        "lump sum": "Lumpsum",
        "redemption": "Redemption",
        "redeem": "Redemption"
    }

    df["transaction_type"] = (
        df["transaction_type"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map(transaction_map)
        .fillna(df["transaction_type"])
    )

    valid_transaction_types = ["SIP", "Lumpsum", "Redemption"]
    df = df[df["transaction_type"].isin(valid_transaction_types)]

    df["kyc_status"] = df["kyc_status"].astype(str).str.strip().str.title()
    valid_kyc_status = ["Verified", "Pending", "Rejected"]
    df = df[df["kyc_status"].isin(valid_kyc_status)]

    text_cols = [
        "investor_id", "state", "city", "city_tier",
        "age_group", "gender", "payment_mode"
    ]

    for col in text_cols:
        df[col] = df[col].astype(str).str.strip()

    df = df.dropna(subset=["transaction_date", "amfi_code", "amount_inr"])
    df = df[df["amount_inr"] > 0]

    save_cleaned(df, "08_investor_transactions_cleaned.csv")
    return df


def clean_portfolio_holdings():
    df = read_csv("09_portfolio_holdings.csv")

    df = df.drop_duplicates()
    df["portfolio_date"] = pd.to_datetime(df["portfolio_date"], errors="coerce")
    df["amfi_code"] = df["amfi_code"].astype(int)

    numeric_cols = ["weight_pct", "market_value_cr", "current_price_inr"]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    text_cols = ["stock_symbol", "stock_name", "sector"]

    for col in text_cols:
        df[col] = df[col].astype(str).str.strip()

    df = df.dropna(subset=["portfolio_date", "amfi_code"])
    df = df[(df["weight_pct"] >= 0) & (df["market_value_cr"] >= 0) & (df["current_price_inr"] > 0)]

    save_cleaned(df, "09_portfolio_holdings_cleaned.csv")
    return df


def clean_benchmark_indices():
    df = read_csv("10_benchmark_indices.csv")

    df = df.drop_duplicates()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["index_name"] = df["index_name"].astype(str).str.strip()
    df["close_value"] = pd.to_numeric(df["close_value"], errors="coerce")

    df = df.dropna(subset=["date", "index_name", "close_value"])
    df = df[df["close_value"] > 0]

    save_cleaned(df, "10_benchmark_indices_cleaned.csv")
    return df


def create_dim_date(*date_series_list):
    all_dates = []

    for series in date_series_list:
        if series is not None:
            all_dates.extend(pd.to_datetime(series, errors="coerce").dropna().tolist())

    unique_dates = sorted(set(all_dates))

    dim_date = pd.DataFrame({"date": unique_dates})
    dim_date["date_id"] = dim_date["date"].dt.strftime("%Y%m%d").astype(int)
    dim_date["year"] = dim_date["date"].dt.year
    dim_date["quarter"] = dim_date["date"].dt.quarter
    dim_date["month"] = dim_date["date"].dt.month
    dim_date["month_name"] = dim_date["date"].dt.month_name()
    dim_date["day"] = dim_date["date"].dt.day

    return dim_date[["date_id", "date", "year", "quarter", "month", "month_name", "day"]]


def write_schema_sql():
    schema_sql = """
DROP TABLE IF EXISTS fact_aum;
DROP TABLE IF EXISTS fact_performance;
DROP TABLE IF EXISTS fact_transactions;
DROP TABLE IF EXISTS fact_nav;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_fund;

CREATE TABLE dim_fund (
    amfi_code INTEGER PRIMARY KEY,
    fund_house TEXT NOT NULL,
    scheme_name TEXT NOT NULL,
    category TEXT,
    sub_category TEXT,
    plan TEXT,
    launch_date TEXT,
    benchmark TEXT,
    expense_ratio_pct REAL,
    exit_load_pct REAL,
    min_sip_amount INTEGER,
    min_lumpsum_amount INTEGER,
    fund_manager TEXT,
    risk_category TEXT,
    sebi_category_code TEXT
);

CREATE TABLE dim_date (
    date_id INTEGER PRIMARY KEY,
    date TEXT NOT NULL,
    year INTEGER,
    quarter INTEGER,
    month INTEGER,
    month_name TEXT,
    day INTEGER
);

CREATE TABLE fact_nav (
    nav_id INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code INTEGER NOT NULL,
    date_id INTEGER NOT NULL,
    nav REAL NOT NULL CHECK(nav > 0),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (date_id) REFERENCES dim_date(date_id)
);

CREATE TABLE fact_transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id TEXT NOT NULL,
    transaction_date_id INTEGER NOT NULL,
    amfi_code INTEGER NOT NULL,
    transaction_type TEXT NOT NULL CHECK(transaction_type IN ('SIP', 'Lumpsum', 'Redemption')),
    amount_inr REAL NOT NULL CHECK(amount_inr > 0),
    state TEXT,
    city TEXT,
    city_tier TEXT,
    age_group TEXT,
    gender TEXT,
    annual_income_lakh REAL,
    payment_mode TEXT,
    kyc_status TEXT CHECK(kyc_status IN ('Verified', 'Pending', 'Rejected')),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (transaction_date_id) REFERENCES dim_date(date_id)
);

CREATE TABLE fact_performance (
    performance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code INTEGER NOT NULL,
    return_1yr_pct REAL,
    return_3yr_pct REAL,
    return_5yr_pct REAL,
    benchmark_3yr_pct REAL,
    alpha REAL,
    beta REAL,
    sharpe_ratio REAL,
    sortino_ratio REAL,
    std_dev_ann_pct REAL,
    max_drawdown_pct REAL,
    aum_crore REAL,
    expense_ratio_pct REAL CHECK(expense_ratio_pct BETWEEN 0.1 AND 2.5),
    morningstar_rating INTEGER,
    risk_grade TEXT,
    performance_anomaly_flag INTEGER,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

CREATE TABLE fact_aum (
    aum_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date_id INTEGER NOT NULL,
    fund_house TEXT NOT NULL,
    aum_lakh_crore REAL,
    aum_crore REAL,
    num_schemes INTEGER,
    FOREIGN KEY (date_id) REFERENCES dim_date(date_id)
);
"""
    schema_path = SQL_DIR / "schema.sql"
    schema_path.write_text(schema_sql.strip(), encoding="utf-8")
    print(f"Saved schema SQL: {schema_path}")


def write_queries_sql():
    queries_sql = """
-- 1. Top 5 funds by AUM
SELECT 
    f.scheme_name,
    f.fund_house,
    p.aum_crore
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
ORDER BY p.aum_crore DESC
LIMIT 5;

-- 2. Average NAV per month
SELECT
    d.year,
    d.month,
    f.scheme_name,
    ROUND(AVG(n.nav), 4) AS avg_nav
FROM fact_nav n
JOIN dim_date d ON n.date_id = d.date_id
JOIN dim_fund f ON n.amfi_code = f.amfi_code
GROUP BY d.year, d.month, f.scheme_name
ORDER BY d.year, d.month, f.scheme_name;

-- 3. SIP YoY growth
SELECT
    strftime('%Y-%m', month) AS month,
    sip_inflow_crore,
    yoy_growth_pct
FROM monthly_sip_inflows
ORDER BY month;

-- 4. Transactions by state
SELECT
    state,
    COUNT(*) AS total_transactions,
    SUM(amount_inr) AS total_amount
FROM fact_transactions
GROUP BY state
ORDER BY total_amount DESC;

-- 5. Funds with expense ratio below 1%
SELECT
    scheme_name,
    fund_house,
    category,
    expense_ratio_pct
FROM dim_fund
WHERE expense_ratio_pct < 1
ORDER BY expense_ratio_pct ASC;

-- 6. Top states by SIP amount
SELECT
    state,
    SUM(amount_inr) AS sip_amount
FROM fact_transactions
WHERE transaction_type = 'SIP'
GROUP BY state
ORDER BY sip_amount DESC
LIMIT 10;

-- 7. Average return by category
SELECT
    f.category,
    ROUND(AVG(p.return_1yr_pct), 2) AS avg_1yr_return,
    ROUND(AVG(p.return_3yr_pct), 2) AS avg_3yr_return,
    ROUND(AVG(p.return_5yr_pct), 2) AS avg_5yr_return
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
GROUP BY f.category;

-- 8. Highest Sharpe ratio funds
SELECT
    f.scheme_name,
    f.fund_house,
    p.sharpe_ratio
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
ORDER BY p.sharpe_ratio DESC
LIMIT 10;

-- 9. Monthly transaction value by transaction type
SELECT
    d.year,
    d.month,
    t.transaction_type,
    SUM(t.amount_inr) AS total_amount
FROM fact_transactions t
JOIN dim_date d ON t.transaction_date_id = d.date_id
GROUP BY d.year, d.month, t.transaction_type
ORDER BY d.year, d.month, t.transaction_type;

-- 10. Fund houses by total AUM
SELECT
    fund_house,
    SUM(aum_crore) AS total_aum_crore
FROM fact_aum
GROUP BY fund_house
ORDER BY total_aum_crore DESC;
"""
    queries_path = SQL_DIR / "queries.sql"
    queries_path.write_text(queries_sql.strip(), encoding="utf-8")
    print(f"Saved analytical queries: {queries_path}")


def write_data_dictionary():
    dictionary_md = """
# Data Dictionary - Bluestock Mutual Fund Analytics

## Source Files

| File | Description |
|---|---|
| 01_fund_master.csv | Master list of mutual fund schemes and metadata |
| 02_nav_history.csv | Historical NAV values by AMFI code and date |
| 03_aum_by_fund_house.csv | AUM trend by fund house |
| 04_monthly_sip_inflows.csv | Monthly SIP inflows and SIP account data |
| 05_category_inflows.csv | Monthly inflows by fund category |
| 06_industry_folio_count.csv | Industry folio counts by category |
| 07_scheme_performance.csv | Scheme-level return and risk metrics |
| 08_investor_transactions.csv | Investor transaction-level data |
| 09_portfolio_holdings.csv | Fund portfolio stock holdings |
| 10_benchmark_indices.csv | Benchmark index historical values |

## Key Business Definitions

| Column | Definition |
|---|---|
| amfi_code | Unique AMFI scheme identifier for a mutual fund scheme |
| fund_house | Asset Management Company managing the scheme |
| scheme_name | Name of the mutual fund scheme |
| category | Broad asset class such as Equity or Debt |
| sub_category | SEBI-style category such as Large Cap, Small Cap, Gilt, ELSS |
| plan | Regular or Direct plan |
| launch_date | Date on which the scheme was launched |
| benchmark | Index used for comparing fund performance |
| expense_ratio_pct | Annual expense charged by the fund as percentage |
| exit_load_pct | Exit load percentage charged on early redemption |
| min_sip_amount | Minimum amount required for SIP investment |
| min_lumpsum_amount | Minimum amount required for lumpsum investment |
| fund_manager | Fund manager responsible for the scheme |
| risk_category | Risk classification of the scheme |
| nav | Net Asset Value of the fund on a given date |
| transaction_type | Type of investor transaction: SIP, Lumpsum, or Redemption |
| amount_inr | Transaction amount in Indian Rupees |
| kyc_status | Investor KYC status: Verified, Pending, or Rejected |
| aum_crore | Assets under management in crore |
| return_1yr_pct | One-year return percentage |
| return_3yr_pct | Three-year return percentage |
| return_5yr_pct | Five-year return percentage |
| alpha | Fund excess return compared with benchmark |
| beta | Sensitivity of fund returns to market movement |
| sharpe_ratio | Risk-adjusted return measure |
| sortino_ratio | Downside-risk-adjusted return measure |
| std_dev_ann_pct | Annualized standard deviation |
| max_drawdown_pct | Maximum decline from peak to trough |
| morningstar_rating | Rating score assigned to scheme |
| stock_symbol | Listed stock symbol in fund holding |
| stock_name | Name of stock held by the fund |
| sector | Industry sector of stock |
| weight_pct | Portfolio allocation percentage |
| close_value | Benchmark index closing value |

## SQLite Star Schema

### dim_fund
Dimension table containing mutual fund scheme metadata.

### dim_date
Calendar dimension table for date-based analytics.

### fact_nav
Fact table containing historical NAV values.

### fact_transactions
Fact table containing investor transaction records.

### fact_performance
Fact table containing scheme performance and risk metrics.

### fact_aum
Fact table containing AUM by fund house over time.

## Data Cleaning Rules Applied

- Parsed date and month fields into datetime format.
- Removed duplicate records.
- Validated NAV values greater than zero.
- Forward-filled NAV values for missing dates caused by weekends and holidays.
- Standardized transaction types into SIP, Lumpsum, and Redemption.
- Validated transaction amounts greater than zero.
- Validated KYC status values.
- Checked expense ratio range between 0.1% and 2.5%.
- Flagged abnormal performance return values.
"""
    dictionary_path = REPORTS_DIR / "data_dictionary.md"
    dictionary_path.write_text(dictionary_md.strip(), encoding="utf-8")
    print(f"Saved data dictionary: {dictionary_path}")


def load_to_sqlite(
    fund_master,
    nav_history,
    aum_by_fund_house,
    monthly_sip_inflows,
    category_inflows,
    industry_folio_count,
    scheme_performance,
    investor_transactions,
    portfolio_holdings,
    benchmark_indices
):
    engine = create_engine(f"sqlite:///{DB_PATH}")

    dim_date = create_dim_date(
        nav_history["date"],
        investor_transactions["transaction_date"],
        aum_by_fund_house["date"],
        monthly_sip_inflows["month"],
        category_inflows["month"],
        industry_folio_count["month"],
        portfolio_holdings["portfolio_date"],
        benchmark_indices["date"],
        fund_master["launch_date"]
    )

    save_cleaned(dim_date, "dim_date_cleaned.csv")

    date_map = dict(zip(dim_date["date"].dt.strftime("%Y-%m-%d"), dim_date["date_id"]))

    fact_nav = nav_history.copy()
    fact_nav["date_id"] = fact_nav["date"].dt.strftime("%Y-%m-%d").map(date_map)
    fact_nav = fact_nav[["amfi_code", "date_id", "nav"]]

    fact_transactions = investor_transactions.copy()
    fact_transactions["transaction_date_id"] = fact_transactions["transaction_date"].dt.strftime("%Y-%m-%d").map(date_map)
    fact_transactions = fact_transactions[
        [
            "investor_id", "transaction_date_id", "amfi_code", "transaction_type",
            "amount_inr", "state", "city", "city_tier", "age_group",
            "gender", "annual_income_lakh", "payment_mode", "kyc_status"
        ]
    ]

    fact_performance = scheme_performance.copy()
    fact_performance["performance_anomaly_flag"] = fact_performance["performance_anomaly_flag"].astype(int)
    fact_performance = fact_performance[
        [
            "amfi_code", "return_1yr_pct", "return_3yr_pct", "return_5yr_pct",
            "benchmark_3yr_pct", "alpha", "beta", "sharpe_ratio",
            "sortino_ratio", "std_dev_ann_pct", "max_drawdown_pct",
            "aum_crore", "expense_ratio_pct", "morningstar_rating",
            "risk_grade", "performance_anomaly_flag"
        ]
    ]

    fact_aum = aum_by_fund_house.copy()
    fact_aum["date_id"] = fact_aum["date"].dt.strftime("%Y-%m-%d").map(date_map)
    fact_aum = fact_aum[["date_id", "fund_house", "aum_lakh_crore", "aum_crore", "num_schemes"]]

    write_schema_sql()
    write_queries_sql()
    write_data_dictionary()

    with engine.begin() as conn:
        schema_sql = (SQL_DIR / "schema.sql").read_text(encoding="utf-8")
        raw_conn = conn.connection
        raw_conn.executescript(schema_sql)

    fund_master.to_sql("dim_fund", engine, if_exists="append", index=False)
    dim_date.to_sql("dim_date", engine, if_exists="append", index=False)
    fact_nav.to_sql("fact_nav", engine, if_exists="append", index=False)
    fact_transactions.to_sql("fact_transactions", engine, if_exists="append", index=False)
    fact_performance.to_sql("fact_performance", engine, if_exists="append", index=False)
    fact_aum.to_sql("fact_aum", engine, if_exists="append", index=False)

    monthly_sip_inflows.to_sql("monthly_sip_inflows", engine, if_exists="replace", index=False)
    category_inflows.to_sql("category_inflows", engine, if_exists="replace", index=False)
    industry_folio_count.to_sql("industry_folio_count", engine, if_exists="replace", index=False)
    portfolio_holdings.to_sql("portfolio_holdings", engine, if_exists="replace", index=False)
    benchmark_indices.to_sql("benchmark_indices", engine, if_exists="replace", index=False)

    print("\nSQLite database created:", DB_PATH)

    tables_to_check = {
        "dim_fund": len(fund_master),
        "dim_date": len(dim_date),
        "fact_nav": len(fact_nav),
        "fact_transactions": len(fact_transactions),
        "fact_performance": len(fact_performance),
        "fact_aum": len(fact_aum),
        "monthly_sip_inflows": len(monthly_sip_inflows),
        "category_inflows": len(category_inflows),
        "industry_folio_count": len(industry_folio_count),
        "portfolio_holdings": len(portfolio_holdings),
        "benchmark_indices": len(benchmark_indices),
    }

    print("\nROW COUNT VERIFICATION")

    with sqlite3.connect(DB_PATH) as conn:
        for table, expected_count in tables_to_check.items():
            actual_count = pd.read_sql_query(f"SELECT COUNT(*) AS count FROM {table}", conn)["count"].iloc[0]
            print(f"{table}: expected={expected_count}, actual={actual_count}")


def main():
    print("Starting Day 2 cleaning and SQLite loading pipeline...\n")

    fund_master = clean_fund_master()
    nav_history = clean_nav_history()
    aum_by_fund_house = clean_aum_by_fund_house()
    monthly_sip_inflows = clean_monthly_sip_inflows()
    category_inflows = clean_category_inflows()
    industry_folio_count = clean_industry_folio_count()
    scheme_performance = clean_scheme_performance()
    investor_transactions = clean_investor_transactions()
    portfolio_holdings = clean_portfolio_holdings()
    benchmark_indices = clean_benchmark_indices()

    load_to_sqlite(
        fund_master,
        nav_history,
        aum_by_fund_house,
        monthly_sip_inflows,
        category_inflows,
        industry_folio_count,
        scheme_performance,
        investor_transactions,
        portfolio_holdings,
        benchmark_indices
    )

    print("\nDay 2 completed successfully.")


if __name__ == "__main__":
    main()