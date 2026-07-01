# Power BI Data Model Relationships

Load the CSVs in `dashboard/powerbi_export/` or connect to `bluestock_mf.db`.

Recommended relationships:

| From table | From column | To table | To column | Cardinality |
|---|---|---|---|---|
| dim_fund | amfi_code | fact_nav | amfi_code | 1:* |
| dim_fund | amfi_code | fact_transactions | amfi_code | 1:* |
| dim_fund | amfi_code | fact_performance | amfi_code | 1:* |
| dim_fund | amfi_code | portfolio_holdings | amfi_code | 1:* |
| dim_date | date_id | fact_nav | date_id | 1:* |
| dim_date | date_id | fact_transactions | transaction_date_id | 1:* |
| dim_date | date_id | fact_aum | date_id | 1:* |

Additional standalone tables:
- monthly_sip_inflows
- category_inflows
- industry_folio_count
- benchmark_indices