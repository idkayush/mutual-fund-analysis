# Bluestock Mutual Fund Analytics Capstone

## Project Overview

This project analyzes Indian mutual fund data using a complete analytics pipeline covering ETL, data cleaning, SQLite database design, exploratory data analysis, performance analytics, advanced risk analytics, and an interactive Power BI dashboard.

The project focuses on NAV trends, AUM growth, SIP inflows, investor demographics, fund performance, risk metrics, cohort behaviour, and fund recommendation logic.

## Tech Stack

- Python
- Pandas
- NumPy
- SQLAlchemy
- SQLite
- Plotly
- Seaborn
- Matplotlib
- SciPy
- Jupyter Notebook
- Power BI

## Folder Structure

mutual-fund-analysis/
- data/
  - raw/
  - processed/
  - db/
- notebooks/
  - 03_eda_analysis.ipynb
  - 04_performance_analytics.ipynb
  - 05_advanced_analytics.ipynb
- scripts/
  - etl_pipeline.py
  - live_nav_fetch.py
  - compute_metrics.py
  - recommender.py
- sql/
  - schema.sql
  - queries.sql
- dashboard/
  - bluestock_mf_dashboard.pbix
- reports/
  - Dashboard.pdf
  - Final_Report.pdf
  - Presentation.pptx
  - fund_scorecard.csv
  - alpha_beta.csv
  - var_cvar_report.csv
- README.md

## Key Deliverables

| ID | Deliverable | File |
|---|---|---|
| D1 | ETL Pipeline Script | scripts/etl_pipeline.py |
| D2 | SQLite Database Schema | sql/schema.sql, sql/queries.sql |
| D3 | EDA Notebook | notebooks/03_eda_analysis.ipynb |
| D4 | Performance Metrics | notebooks/04_performance_analytics.ipynb, reports/fund_scorecard.csv |
| D5 | Interactive Dashboard | dashboard/bluestock_mf_dashboard.pbix |
| D6 | Advanced Analytics | notebooks/05_advanced_analytics.ipynb, reports/var_cvar_report.csv |
| D7 | Final Report and Slides | reports/Final_Report.pdf, reports/Presentation.pptx |

## Key Analyses Performed

- Cleaned and validated NAV, transaction, AUM, SIP, performance, portfolio, and benchmark datasets.
- Designed a SQLite star schema with fund, date, NAV, transaction, performance, and AUM tables.
- Built 15+ EDA charts covering NAV trends, SIP inflows, investor demographics, folio growth, category inflows, and sector allocation.
- Computed CAGR, Sharpe Ratio, Sortino Ratio, Alpha, Beta, Tracking Error, and Maximum Drawdown.
- Built a composite fund scorecard using return, risk-adjusted performance, alpha, expense ratio, and drawdown.
- Computed Historical VaR and CVaR at 95 percent confidence.
- Performed investor cohort analysis and SIP continuity analysis.
- Built a simple rule-based fund recommender using risk appetite and Sharpe Ratio.
- Created a 4-page interactive Power BI dashboard.

## Dashboard Pages

1. Industry Overview
2. Fund Performance
3. Investor Analytics
4. SIP and Market Trends

## Important Notes

- SQLite database files are excluded from GitHub using .gitignore.
- Database schema and analytical queries are available in the sql folder.
- Final dashboard exports are available in the reports folder.

## GitHub Repository

https://github.com/idkayush/mutual-fund-analysis
