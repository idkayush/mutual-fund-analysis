from pathlib import Path
import warnings

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import nbformat as nbf
from scipy.stats import linregress


BASE_DIR = Path(".")
PROCESSED_DIR = BASE_DIR / "data" / "processed"
RAW_DIR = BASE_DIR / "data" / "raw"
NOTEBOOK_DIR = BASE_DIR / "notebooks"
REPORTS_DIR = BASE_DIR / "reports"
CHART_DIR = REPORTS_DIR / "charts"

NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
CHART_DIR.mkdir(parents=True, exist_ok=True)

RF_ANNUAL = 0.065
TRADING_DAYS = 252


def load_data():
    fund_master = pd.read_csv(PROCESSED_DIR / "01_fund_master_cleaned.csv")
    nav_history = pd.read_csv(PROCESSED_DIR / "02_nav_history_cleaned.csv")
    benchmark = pd.read_csv(PROCESSED_DIR / "10_benchmark_indices_cleaned.csv")

    fund_master["amfi_code"] = fund_master["amfi_code"].astype(int)
    nav_history["amfi_code"] = nav_history["amfi_code"].astype(int)

    nav_history["date"] = pd.to_datetime(nav_history["date"], errors="coerce")
    benchmark["date"] = pd.to_datetime(benchmark["date"], errors="coerce")

    nav_history = nav_history.dropna(subset=["date", "nav"])
    benchmark = benchmark.dropna(subset=["date", "close_value"])

    return fund_master, nav_history, benchmark


def compute_daily_returns(nav_history):
    nav_history = nav_history.sort_values(["amfi_code", "date"]).copy()
    nav_history["daily_return"] = nav_history.groupby("amfi_code")["nav"].pct_change()
    return nav_history


def get_cagr_for_period(group, years):
    group = group.sort_values("date").dropna(subset=["nav"])

    if group.empty:
        return np.nan

    end_date = group["date"].max()
    start_target = end_date - pd.DateOffset(years=years)

    eligible_start = group[group["date"] <= start_target]

    if eligible_start.empty:
        return np.nan

    start_row = eligible_start.iloc[-1]
    end_row = group.iloc[-1]

    start_nav = start_row["nav"]
    end_nav = end_row["nav"]

    if start_nav <= 0 or end_nav <= 0:
        return np.nan

    actual_years = (end_row["date"] - start_row["date"]).days / 365.25

    if actual_years <= 0:
        return np.nan

    return (end_nav / start_nav) ** (1 / actual_years) - 1


def compute_cagr_table(nav_history, fund_master):
    rows = []

    for amfi_code, group in nav_history.groupby("amfi_code"):
        rows.append({
            "amfi_code": amfi_code,
            "cagr_1yr": get_cagr_for_period(group, 1),
            "cagr_3yr": get_cagr_for_period(group, 3),
            "cagr_5yr": get_cagr_for_period(group, 5),
        })

    cagr_df = pd.DataFrame(rows)
    cagr_df = cagr_df.merge(
        fund_master[["amfi_code", "scheme_name", "fund_house", "category", "sub_category", "expense_ratio_pct"]],
        on="amfi_code",
        how="left"
    )

    return cagr_df


def compute_risk_metrics(nav_returns):
    rows = []

    rf_daily = RF_ANNUAL / TRADING_DAYS

    for amfi_code, group in nav_returns.groupby("amfi_code"):
        group = group.sort_values("date").dropna(subset=["daily_return"])

        if group.empty:
            continue

        returns = group["daily_return"]

        mean_daily = returns.mean()
        std_daily = returns.std()

        sharpe = np.nan
        if std_daily and std_daily > 0:
            sharpe = ((mean_daily - rf_daily) / std_daily) * np.sqrt(TRADING_DAYS)

        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std()

        sortino = np.nan
        if downside_std and downside_std > 0:
            sortino = ((mean_daily - rf_daily) / downside_std) * np.sqrt(TRADING_DAYS)

        group["running_max"] = group["nav"].cummax()
        group["drawdown"] = group["nav"] / group["running_max"] - 1

        max_dd = group["drawdown"].min()
        max_dd_end_date = group.loc[group["drawdown"].idxmin(), "date"]

        peak_group = group[group["date"] <= max_dd_end_date]
        max_dd_start_date = peak_group.loc[peak_group["nav"].idxmax(), "date"]

        rows.append({
            "amfi_code": amfi_code,
            "annualized_return": mean_daily * TRADING_DAYS,
            "annualized_volatility": std_daily * np.sqrt(TRADING_DAYS),
            "sharpe_ratio": sharpe,
            "sortino_ratio": sortino,
            "max_drawdown": max_dd,
            "max_drawdown_start_date": max_dd_start_date,
            "max_drawdown_end_date": max_dd_end_date,
        })

    return pd.DataFrame(rows)


def prepare_benchmark_returns(benchmark):
    benchmark_pivot = benchmark.pivot_table(
        index="date",
        columns="index_name",
        values="close_value",
        aggfunc="mean"
    ).sort_index()

    benchmark_returns = benchmark_pivot.pct_change().dropna()
    return benchmark_pivot, benchmark_returns


def compute_alpha_beta(nav_returns, fund_master, benchmark_returns):
    alpha_beta_rows = []

    nav_pivot = nav_returns.pivot_table(
        index="date",
        columns="amfi_code",
        values="daily_return",
        aggfunc="mean"
    ).sort_index()

    benchmark_name = None

    for possible_name in ["NIFTY100", "NIFTY 100", "Nifty 100"]:
        if possible_name in benchmark_returns.columns:
            benchmark_name = possible_name
            break

    if benchmark_name is None:
        benchmark_name = benchmark_returns.columns[0]

    benchmark_series = benchmark_returns[benchmark_name].dropna()

    for amfi_code in nav_pivot.columns:
        fund_series = nav_pivot[amfi_code].dropna()

        joined = pd.concat([fund_series, benchmark_series], axis=1, join="inner").dropna()
        joined.columns = ["fund_return", "benchmark_return"]

        if len(joined) < 30:
            alpha = np.nan
            beta = np.nan
            r_value = np.nan
            p_value = np.nan
        else:
            result = linregress(joined["benchmark_return"], joined["fund_return"])
            alpha = result.intercept * TRADING_DAYS
            beta = result.slope
            r_value = result.rvalue
            p_value = result.pvalue

        alpha_beta_rows.append({
            "amfi_code": amfi_code,
            "benchmark_used": benchmark_name,
            "alpha_annualized": alpha,
            "beta": beta,
            "r_squared": r_value ** 2 if not pd.isna(r_value) else np.nan,
            "p_value": p_value,
        })

    alpha_beta_df = pd.DataFrame(alpha_beta_rows)
    alpha_beta_df = alpha_beta_df.merge(
        fund_master[["amfi_code", "scheme_name", "fund_house", "category", "sub_category"]],
        on="amfi_code",
        how="left"
    )

    return alpha_beta_df


def compute_tracking_error(nav_returns, benchmark_returns):
    nav_pivot = nav_returns.pivot_table(
        index="date",
        columns="amfi_code",
        values="daily_return",
        aggfunc="mean"
    ).sort_index()

    tracking_rows = []

    benchmark_cols = []
    for col in benchmark_returns.columns:
        if "NIFTY50" in col.upper().replace(" ", "") or "NIFTY100" in col.upper().replace(" ", ""):
            benchmark_cols.append(col)

    if not benchmark_cols:
        benchmark_cols = benchmark_returns.columns.tolist()[:2]

    for amfi_code in nav_pivot.columns:
        fund_series = nav_pivot[amfi_code].dropna()

        for benchmark_name in benchmark_cols:
            benchmark_series = benchmark_returns[benchmark_name].dropna()

            joined = pd.concat([fund_series, benchmark_series], axis=1, join="inner").dropna()
            joined.columns = ["fund_return", "benchmark_return"]

            if len(joined) < 30:
                tracking_error = np.nan
            else:
                tracking_error = (joined["fund_return"] - joined["benchmark_return"]).std() * np.sqrt(TRADING_DAYS)

            tracking_rows.append({
                "amfi_code": amfi_code,
                "benchmark": benchmark_name,
                "tracking_error": tracking_error,
            })

    return pd.DataFrame(tracking_rows)


def build_scorecard(cagr_df, risk_df, alpha_beta_df, fund_master):
    scorecard = fund_master[
        ["amfi_code", "scheme_name", "fund_house", "category", "sub_category", "expense_ratio_pct"]
    ].copy()

    scorecard = scorecard.merge(
        cagr_df[["amfi_code", "cagr_1yr", "cagr_3yr", "cagr_5yr"]],
        on="amfi_code",
        how="left"
    )

    scorecard = scorecard.merge(
        risk_df[[
            "amfi_code", "annualized_return", "annualized_volatility",
            "sharpe_ratio", "sortino_ratio", "max_drawdown",
            "max_drawdown_start_date", "max_drawdown_end_date"
        ]],
        on="amfi_code",
        how="left"
    )

    scorecard = scorecard.merge(
        alpha_beta_df[["amfi_code", "alpha_annualized", "beta", "r_squared"]],
        on="amfi_code",
        how="left"
    )

    scorecard["return_rank_score"] = scorecard["cagr_3yr"].rank(pct=True) * 100
    scorecard["sharpe_rank_score"] = scorecard["sharpe_ratio"].rank(pct=True) * 100
    scorecard["alpha_rank_score"] = scorecard["alpha_annualized"].rank(pct=True) * 100

    scorecard["expense_rank_score"] = scorecard["expense_ratio_pct"].rank(
        ascending=False,
        pct=True
    ) * 100

    scorecard["max_dd_rank_score"] = scorecard["max_drawdown"].rank(
        ascending=True,
        pct=True
    ) * 100

    scorecard["fund_score"] = (
        0.30 * scorecard["return_rank_score"] +
        0.25 * scorecard["sharpe_rank_score"] +
        0.20 * scorecard["alpha_rank_score"] +
        0.15 * scorecard["expense_rank_score"] +
        0.10 * scorecard["max_dd_rank_score"]
    )

    scorecard = scorecard.sort_values("fund_score", ascending=False)

    return scorecard


def create_benchmark_comparison_chart(scorecard, nav_history, benchmark):
    top_5_codes = scorecard.head(5)["amfi_code"].tolist()

    max_date = nav_history["date"].max()
    start_date = max_date - pd.DateOffset(years=3)

    nav_top = nav_history[
        (nav_history["amfi_code"].isin(top_5_codes)) &
        (nav_history["date"] >= start_date)
    ].copy()

    top_names = scorecard.set_index("amfi_code")["scheme_name"].to_dict()
    nav_top["name"] = nav_top["amfi_code"].map(top_names)

    nav_pivot = nav_top.pivot_table(
        index="date",
        columns="name",
        values="nav",
        aggfunc="mean"
    ).sort_index()

    benchmark_filtered = benchmark[
        (benchmark["date"] >= start_date) &
        (benchmark["index_name"].isin(["NIFTY50", "NIFTY100", "NIFTY 50", "NIFTY 100"]))
    ].copy()

    benchmark_pivot = benchmark_filtered.pivot_table(
        index="date",
        columns="index_name",
        values="close_value",
        aggfunc="mean"
    ).sort_index()

    combined = pd.concat([nav_pivot, benchmark_pivot], axis=1).sort_index()
    combined = combined.ffill().dropna(how="all")

    indexed = combined / combined.iloc[0] * 100

    plt.figure(figsize=(16, 9))

    for col in indexed.columns:
        plt.plot(indexed.index, indexed[col], label=col, linewidth=2)

    plt.title("Top 5 Funds vs NIFTY 50 and NIFTY 100 - 3 Year Indexed Performance")
    plt.xlabel("Date")
    plt.ylabel("Indexed Value, Base = 100")
    plt.legend(loc="best", fontsize=8)
    plt.grid(True, alpha=0.3)

    chart_path = CHART_DIR / "benchmark_comparison_top5_vs_nifty.png"
    plt.tight_layout()
    plt.savefig(chart_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"Saved benchmark comparison chart: {chart_path}")


def create_extra_charts(scorecard):
    plt.figure(figsize=(14, 8))
    top_10 = scorecard.head(10).sort_values("fund_score")
    plt.barh(top_10["scheme_name"], top_10["fund_score"])
    plt.title("Top 10 Funds by Composite Score")
    plt.xlabel("Fund Score")
    plt.ylabel("Scheme")
    plt.tight_layout()
    plt.savefig(CHART_DIR / "fund_scorecard_top10.png", dpi=300, bbox_inches="tight")
    plt.close()

    plt.figure(figsize=(12, 7))
    plt.hist(scorecard["sharpe_ratio"].dropna(), bins=20)
    plt.title("Sharpe Ratio Distribution")
    plt.xlabel("Sharpe Ratio")
    plt.ylabel("Fund Count")
    plt.tight_layout()
    plt.savefig(CHART_DIR / "sharpe_ratio_distribution.png", dpi=300, bbox_inches="tight")
    plt.close()

    plt.figure(figsize=(12, 7))
    plt.scatter(scorecard["beta"], scorecard["alpha_annualized"])
    plt.title("Alpha vs Beta")
    plt.xlabel("Beta")
    plt.ylabel("Annualized Alpha")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(CHART_DIR / "alpha_vs_beta_scatter.png", dpi=300, bbox_inches="tight")
    plt.close()


def create_notebook():
    notebook_path = NOTEBOOK_DIR / "Performance_Analytics.ipynb"

    nb = nbf.v4.new_notebook()

    cells = []

    cells.append(nbf.v4.new_markdown_cell(
        "# Performance Analytics\n\n"
        "This notebook computes daily returns, CAGR, Sharpe Ratio, Sortino Ratio, Alpha, Beta, Maximum Drawdown, fund scorecard, and benchmark comparison for mutual fund schemes."
    ))

    cells.append(nbf.v4.new_code_cell(
        """
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress

PROCESSED_DIR = Path("../data/processed")
REPORTS_DIR = Path("../reports")
CHART_DIR = REPORTS_DIR / "charts"

fund_master = pd.read_csv(PROCESSED_DIR / "01_fund_master_cleaned.csv")
nav_history = pd.read_csv(PROCESSED_DIR / "02_nav_history_cleaned.csv")
benchmark = pd.read_csv(PROCESSED_DIR / "10_benchmark_indices_cleaned.csv")

scorecard = pd.read_csv(REPORTS_DIR / "fund_scorecard.csv")
alpha_beta = pd.read_csv(REPORTS_DIR / "alpha_beta.csv")

nav_history["date"] = pd.to_datetime(nav_history["date"])
benchmark["date"] = pd.to_datetime(benchmark["date"])

scorecard.head()
"""
    ))

    markdown_sections = [
        ("Daily Returns", "Daily returns were calculated as NAV_t / NAV_t-1 - 1 for every scheme. The return distribution should mostly be centered near zero with limited extreme values."),
        ("CAGR", "CAGR was calculated for 1-year, 3-year, and 5-year windows using the start and end NAV for each period."),
        ("Sharpe Ratio", "Sharpe Ratio ranks schemes by risk-adjusted returns using 6.5% as the annual risk-free rate proxy."),
        ("Sortino Ratio", "Sortino Ratio focuses only on downside volatility and is useful for identifying funds with smoother downside behavior."),
        ("Alpha and Beta", "Alpha and beta were calculated using OLS regression of fund returns against NIFTY 100 returns."),
        ("Maximum Drawdown", "Maximum drawdown identifies the worst fall from a running peak and records the start and end dates of that decline."),
        ("Fund Scorecard", "The composite score combines 3-year return, Sharpe Ratio, Alpha, expense ratio, and max drawdown into a 0–100 fund ranking."),
        ("Benchmark Comparison", "The top 5 funds were compared with NIFTY 50 and NIFTY 100 over the latest 3-year period using indexed performance."),
    ]

    for title, text in markdown_sections:
        cells.append(nbf.v4.new_markdown_cell(f"## {title}\n\n{text}"))

    cells.append(nbf.v4.new_code_cell(
        """
scorecard.sort_values("fund_score", ascending=False).head(10)
"""
    ))

    cells.append(nbf.v4.new_code_cell(
        """
alpha_beta.head(10)
"""
    ))

    cells.append(nbf.v4.new_markdown_cell(
        "## Supporting Charts\n\n"
        "- `reports/charts/benchmark_comparison_top5_vs_nifty.png`\n"
        "- `reports/charts/fund_scorecard_top10.png`\n"
        "- `reports/charts/sharpe_ratio_distribution.png`\n"
        "- `reports/charts/alpha_vs_beta_scatter.png`"
    ))

    nb["cells"] = cells

    with open(notebook_path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)

    print(f"Saved notebook: {notebook_path}")


def main():
    print("Loading data...")
    fund_master, nav_history, benchmark = load_data()

    print("Computing daily returns...")
    nav_returns = compute_daily_returns(nav_history)

    return_summary = nav_returns["daily_return"].describe()
    print("\nDaily return distribution:")
    print(return_summary)

    print("\nComputing CAGR...")
    cagr_df = compute_cagr_table(nav_history, fund_master)

    print("Computing risk metrics...")
    risk_df = compute_risk_metrics(nav_returns)

    print("Preparing benchmark returns...")
    benchmark_pivot, benchmark_returns = prepare_benchmark_returns(benchmark)

    print("Computing alpha and beta...")
    alpha_beta_df = compute_alpha_beta(nav_returns, fund_master, benchmark_returns)

    print("Computing tracking error...")
    tracking_error_df = compute_tracking_error(nav_returns, benchmark_returns)

    print("Building fund scorecard...")
    scorecard = build_scorecard(cagr_df, risk_df, alpha_beta_df, fund_master)

    scorecard = scorecard.merge(
        tracking_error_df.pivot_table(
            index="amfi_code",
            columns="benchmark",
            values="tracking_error",
            aggfunc="mean"
        ).reset_index(),
        on="amfi_code",
        how="left"
    )

    fund_scorecard_path = REPORTS_DIR / "fund_scorecard.csv"
    alpha_beta_path = REPORTS_DIR / "alpha_beta.csv"

    scorecard.to_csv(fund_scorecard_path, index=False)
    alpha_beta_df.to_csv(alpha_beta_path, index=False)

    print(f"Saved fund scorecard: {fund_scorecard_path}")
    print(f"Saved alpha beta file: {alpha_beta_path}")

    print("Creating benchmark comparison chart...")
    create_benchmark_comparison_chart(scorecard, nav_history, benchmark)

    print("Creating extra charts...")
    create_extra_charts(scorecard)

    print("Creating notebook...")
    create_notebook()

    print("\nPerformance analytics completed successfully.")
    print("Deliverables:")
    print("- notebooks/Performance_Analytics.ipynb")
    print("- reports/fund_scorecard.csv")
    print("- reports/alpha_beta.csv")
    print("- reports/charts/benchmark_comparison_top5_vs_nifty.png")


if __name__ == "__main__":
    main()