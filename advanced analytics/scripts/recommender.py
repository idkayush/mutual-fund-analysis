from pathlib import Path
import sqlite3
import pandas as pd

DB_PATH = Path(__file__).resolve().parents[1] / "bluestock_mf.db"
if not DB_PATH.exists():
    DB_PATH = Path("bluestock_mf.db")

RISK_MAP = {
    "low": ["Low"],
    "moderate": ["Moderate", "Moderately High"],
    "high": ["High", "Very High"],
}

def recommend_funds(risk_appetite: str, top_n: int = 3) -> pd.DataFrame:
    risk_key = risk_appetite.strip().lower()
    if risk_key not in RISK_MAP:
        raise ValueError("Risk appetite must be one of: Low, Moderate, High")

    query = """
    SELECT
        f.amfi_code,
        f.scheme_name,
        f.fund_house,
        f.category,
        f.sub_category,
        p.risk_grade,
        p.return_3yr_pct,
        p.sharpe_ratio,
        p.sortino_ratio,
        p.alpha,
        p.beta,
        p.expense_ratio_pct,
        p.aum_crore
    FROM fact_performance p
    JOIN dim_fund f ON p.amfi_code = f.amfi_code
    """
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(query, conn)

    allowed = RISK_MAP[risk_key]
    out = (
        df[df["risk_grade"].isin(allowed)]
        .sort_values("sharpe_ratio", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )
    return out

if __name__ == "__main__":
    risk = input("Enter risk appetite (Low / Moderate / High): ")
    recommendations = recommend_funds(risk, top_n=3)
    if recommendations.empty:
        print("No matching funds found for this risk appetite.")
    else:
        print("\nTop 3 recommended funds:\n")
        print(recommendations.to_string(index=False))
