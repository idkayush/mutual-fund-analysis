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