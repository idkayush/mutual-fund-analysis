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