# Bluestock Power BI Dashboard Build Guide

## 1. Import data

Use Power BI Desktop → Get Data → Text/CSV and import every CSV from:

`dashboard/powerbi_export/`

Or use the SQLite database at project root:

`bluestock_mf.db`

The package includes verified tables exported from the uploaded SQLite DB.

## 2. Tables to load

- dim_fund
- dim_date
- fact_nav
- fact_transactions
- fact_performance
- fact_aum
- monthly_sip_inflows
- category_inflows
- industry_folio_count
- portfolio_holdings
- benchmark_indices

## 3. Relationships

Use `dashboard/data_model_relationships.md`.

## 4. DAX measures

Copy all measures from:

`dashboard/dax_measures.dax`

## 5. Theme

Power BI Desktop → View → Browse for themes → select:

`dashboard/assets/bluestock_theme.json`

## 6. Dashboard pages

### Page 1 — Industry Overview
KPI cards:
- Total AUM
- SIP Inflows
- Folios
- Schemes

Charts:
- Industry AUM trend 2022–2025
- AUM by AMC

### Page 2 — Fund Performance
Charts:
- Scatter: return vs risk, bubble size = AUM
- Sortable scorecard table
- NAV line vs benchmark
Slicers:
- Fund house
- Category
- Plan

### Page 3 — Investor Analytics
Charts:
- Transaction amount by state
- Donut: SIP/Lumpsum/Redemption split
- Age group vs average SIP amount
- Monthly transaction volume line
Slicers:
- State
- Age group
- City tier

### Page 4 — SIP & Market Trends
Charts:
- SIP inflow + Nifty 50 dual-axis
- Category inflow heatmap using Matrix + conditional formatting
- Top 5 categories by net inflow FY25

## 7. Export requirements

Save as:

`dashboard/bluestock_mf_dashboard.pbix`

Export PDF as:

`reports/Dashboard.pdf`

Export screenshots as:

- `reports/dashboard_screenshots/page1_industry_overview.png`
- `reports/dashboard_screenshots/page2_fund_performance.png`
- `reports/dashboard_screenshots/page3_investor_analytics.png`
- `reports/dashboard_screenshots/page4_sip_market_trends.png`