from pathlib import Path
import warnings

warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import nbformat as nbf


BASE_DIR = Path(".")
PROCESSED_DIR = BASE_DIR / "data" / "processed"
RAW_DIR = BASE_DIR / "data" / "raw"
NOTEBOOK_DIR = BASE_DIR / "notebooks"
CHART_DIR = BASE_DIR / "reports" / "charts"

NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)
CHART_DIR.mkdir(parents=True, exist_ok=True)


def load_csv(processed_name, raw_name):
    processed_path = PROCESSED_DIR / processed_name
    raw_path = RAW_DIR / raw_name

    if processed_path.exists():
        return pd.read_csv(processed_path)

    if raw_path.exists():
        return pd.read_csv(raw_path)

    raise FileNotFoundError(f"Could not find {processed_name} or {raw_name}")


def save_plotly(fig, filename):
    png_path = CHART_DIR / filename
    html_path = CHART_DIR / filename.replace(".png", ".html")

    fig.write_html(html_path)

    try:
        fig.write_image(png_path, width=1400, height=800, scale=2)
        print(f"Saved: {png_path}")
    except Exception as e:
        print(f"Could not save PNG for {filename}. HTML saved instead.")
        print("Install/upgrade kaleido if needed: pip install -U kaleido")
        print("Error:", e)


def save_matplotlib(filename):
    path = CHART_DIR / filename
    plt.tight_layout()
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {path}")


def prepare_data():
    fund_master = load_csv("01_fund_master_cleaned.csv", "01_fund_master.csv")
    nav_history = load_csv("02_nav_history_cleaned.csv", "02_nav_history.csv")
    aum = load_csv("03_aum_by_fund_house_cleaned.csv", "03_aum_by_fund_house.csv")
    sip = load_csv("04_monthly_sip_inflows_cleaned.csv", "04_monthly_sip_inflows.csv")
    category_inflows = load_csv("05_category_inflows_cleaned.csv", "05_category_inflows.csv")
    folio = load_csv("06_industry_folio_count_cleaned.csv", "06_industry_folio_count.csv")
    performance = load_csv("07_scheme_performance_cleaned.csv", "07_scheme_performance.csv")
    transactions = load_csv("08_investor_transactions_cleaned.csv", "08_investor_transactions.csv")
    holdings = load_csv("09_portfolio_holdings_cleaned.csv", "09_portfolio_holdings.csv")
    benchmark = load_csv("10_benchmark_indices_cleaned.csv", "10_benchmark_indices.csv")

    nav_history["date"] = pd.to_datetime(nav_history["date"], errors="coerce")
    aum["date"] = pd.to_datetime(aum["date"], errors="coerce")
    sip["month"] = pd.to_datetime(sip["month"], errors="coerce")
    category_inflows["month"] = pd.to_datetime(category_inflows["month"], errors="coerce")
    folio["month"] = pd.to_datetime(folio["month"], errors="coerce")
    transactions["transaction_date"] = pd.to_datetime(transactions["transaction_date"], errors="coerce")
    holdings["portfolio_date"] = pd.to_datetime(holdings["portfolio_date"], errors="coerce")
    benchmark["date"] = pd.to_datetime(benchmark["date"], errors="coerce")

    return {
        "fund_master": fund_master,
        "nav_history": nav_history,
        "aum": aum,
        "sip": sip,
        "category_inflows": category_inflows,
        "folio": folio,
        "performance": performance,
        "transactions": transactions,
        "holdings": holdings,
        "benchmark": benchmark,
    }


def generate_charts(data):
    fund_master = data["fund_master"]
    nav_history = data["nav_history"]
    aum = data["aum"]
    sip = data["sip"]
    category_inflows = data["category_inflows"]
    folio = data["folio"]
    performance = data["performance"]
    transactions = data["transactions"]
    holdings = data["holdings"]

    charts = []

    nav_merged = nav_history.merge(
        fund_master[["amfi_code", "scheme_name", "fund_house", "category", "sub_category"]],
        on="amfi_code",
        how="left"
    )

    nav_merged = nav_merged[
        (nav_merged["date"] >= "2022-01-01") &
        (nav_merged["date"] <= "2026-12-31")
    ]

    fig = px.line(
        nav_merged,
        x="date",
        y="nav",
        color="scheme_name",
        title="Daily NAV Trend for All 40 Schemes (2022–2026)",
        labels={"nav": "NAV", "date": "Date", "scheme_name": "Scheme"}
    )
    fig.add_vrect(
        x0="2023-01-01",
        x1="2023-12-31",
        fillcolor="green",
        opacity=0.12,
        layer="below",
        line_width=0,
        annotation_text="2023 Bull Run",
        annotation_position="top left"
    )
    fig.add_vrect(
        x0="2024-06-01",
        x1="2024-06-15",
        fillcolor="red",
        opacity=0.15,
        layer="below",
        line_width=0,
        annotation_text="2024 Correction",
        annotation_position="top right"
    )
    fig.add_vrect(
        x0="2024-10-01",
        x1="2024-11-30",
        fillcolor="red",
        opacity=0.10,
        layer="below",
        line_width=0
    )
    save_plotly(fig, "01_nav_trend_all_40_schemes.png")
    charts.append("01_nav_trend_all_40_schemes.png")

    nav_indexed = nav_merged.sort_values(["amfi_code", "date"]).copy()
    nav_indexed["base_nav"] = nav_indexed.groupby("amfi_code")["nav"].transform("first")
    nav_indexed["indexed_nav"] = (nav_indexed["nav"] / nav_indexed["base_nav"]) * 100

    fig = px.line(
        nav_indexed,
        x="date",
        y="indexed_nav",
        color="scheme_name",
        title="Indexed NAV Growth for All Schemes, Base = 100",
        labels={"indexed_nav": "Indexed NAV", "date": "Date"}
    )
    save_plotly(fig, "02_indexed_nav_growth_all_schemes.png")
    charts.append("02_indexed_nav_growth_all_schemes.png")

    aum["year"] = aum["date"].dt.year
    aum_yearly = aum[(aum["year"] >= 2022) & (aum["year"] <= 2025)].copy()

    plt.figure(figsize=(14, 7))
    sns.barplot(data=aum_yearly, x="year", y="aum_lakh_crore", hue="fund_house")
    plt.title("AUM Growth by Fund House, 2022–2025")
    plt.xlabel("Year")
    plt.ylabel("AUM ₹ Lakh Crore")
    plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.annotate(
        "SBI dominance: ₹12.5L Cr",
        xy=(3, 12.5),
        xytext=(2.3, 13.2),
        arrowprops=dict(arrowstyle="->")
    )
    save_matplotlib("03_aum_growth_by_fund_house.png")
    charts.append("03_aum_growth_by_fund_house.png")

    fig = px.line(
        sip,
        x="month",
        y="sip_inflow_crore",
        markers=True,
        title="Monthly SIP Inflow Trend, Jan 2022 – Dec 2025",
        labels={"sip_inflow_crore": "SIP Inflow ₹ Crore", "month": "Month"}
    )

    high_row = sip.loc[sip["sip_inflow_crore"].idxmax()]
    fig.add_annotation(
        x=high_row["month"],
        y=high_row["sip_inflow_crore"],
        text=f"All-time high: ₹{int(high_row['sip_inflow_crore']):,} Cr",
        showarrow=True,
        arrowhead=2
    )
    save_plotly(fig, "04_sip_inflow_time_series.png")
    charts.append("04_sip_inflow_time_series.png")

    heatmap_data = category_inflows.copy()
    heatmap_data["month_str"] = heatmap_data["month"].dt.strftime("%Y-%m")
    pivot = heatmap_data.pivot_table(
        index="category",
        columns="month_str",
        values="net_inflow_crore",
        aggfunc="sum"
    )

    plt.figure(figsize=(18, 8))
    sns.heatmap(pivot, cmap="YlGnBu", linewidths=0.2)
    plt.title("Category Inflow Heatmap")
    plt.xlabel("Month")
    plt.ylabel("Category")
    save_matplotlib("05_category_inflow_heatmap.png")
    charts.append("05_category_inflow_heatmap.png")

    age_counts = transactions["age_group"].value_counts().reset_index()
    age_counts.columns = ["age_group", "count"]

    fig = px.pie(
        age_counts,
        values="count",
        names="age_group",
        title="Investor Age Group Distribution"
    )
    save_plotly(fig, "06_age_group_distribution_pie.png")
    charts.append("06_age_group_distribution_pie.png")

    sip_transactions = transactions[transactions["transaction_type"] == "SIP"].copy()

    plt.figure(figsize=(12, 7))
    sns.boxplot(data=sip_transactions, x="age_group", y="amount_inr")
    plt.title("SIP Amount Distribution by Age Group")
    plt.xlabel("Age Group")
    plt.ylabel("SIP Amount ₹")
    save_matplotlib("07_sip_amount_boxplot_by_age_group.png")
    charts.append("07_sip_amount_boxplot_by_age_group.png")

    gender_counts = transactions["gender"].value_counts().reset_index()
    gender_counts.columns = ["gender", "count"]

    fig = px.pie(
        gender_counts,
        values="count",
        names="gender",
        title="Investor Gender Split"
    )
    save_plotly(fig, "08_gender_split.png")
    charts.append("08_gender_split.png")

    state_sip = (
        sip_transactions.groupby("state", as_index=False)["amount_inr"]
        .sum()
        .sort_values("amount_inr", ascending=True)
    )

    plt.figure(figsize=(12, 8))
    sns.barplot(data=state_sip, y="state", x="amount_inr")
    plt.title("SIP Amount by State")
    plt.xlabel("Total SIP Amount ₹")
    plt.ylabel("State")
    save_matplotlib("09_sip_amount_by_state.png")
    charts.append("09_sip_amount_by_state.png")

    city_tier_counts = transactions["city_tier"].value_counts().reset_index()
    city_tier_counts.columns = ["city_tier", "count"]

    fig = px.pie(
        city_tier_counts,
        values="count",
        names="city_tier",
        title="T30 vs B30 City Tier Split"
    )
    save_plotly(fig, "10_city_tier_split.png")
    charts.append("10_city_tier_split.png")

    fig = px.line(
        folio,
        x="month",
        y="total_folios_crore",
        markers=True,
        title="Industry Folio Count Growth",
        labels={"total_folios_crore": "Total Folios Crore", "month": "Month"}
    )

    first_row = folio.sort_values("month").iloc[0]
    last_row = folio.sort_values("month").iloc[-1]

    fig.add_annotation(
        x=first_row["month"],
        y=first_row["total_folios_crore"],
        text=f"Start: {first_row['total_folios_crore']} Cr",
        showarrow=True
    )
    fig.add_annotation(
        x=last_row["month"],
        y=last_row["total_folios_crore"],
        text=f"Latest: {last_row['total_folios_crore']} Cr",
        showarrow=True
    )
    save_plotly(fig, "11_folio_count_growth.png")
    charts.append("11_folio_count_growth.png")

    selected_codes = fund_master["amfi_code"].head(10).tolist()
    nav_selected = nav_history[nav_history["amfi_code"].isin(selected_codes)].copy()
    nav_pivot = nav_selected.pivot_table(index="date", columns="amfi_code", values="nav")
    returns = nav_pivot.pct_change().dropna()
    corr = returns.corr()

    code_name_map = fund_master.set_index("amfi_code")["scheme_name"].to_dict()
    corr = corr.rename(index=code_name_map, columns=code_name_map)

    plt.figure(figsize=(13, 10))
    sns.heatmap(corr, annot=False, cmap="coolwarm", center=0)
    plt.title("Daily NAV Return Correlation Matrix for 10 Selected Funds")
    save_matplotlib("12_nav_return_correlation_matrix.png")
    charts.append("12_nav_return_correlation_matrix.png")

    sector_weights = (
        holdings.groupby("sector", as_index=False)["weight_pct"]
        .sum()
        .sort_values("weight_pct", ascending=False)
    )

    fig = px.pie(
        sector_weights,
        values="weight_pct",
        names="sector",
        hole=0.45,
        title="Sector Allocation Donut Across Equity Fund Holdings"
    )
    save_plotly(fig, "13_sector_allocation_donut.png")
    charts.append("13_sector_allocation_donut.png")

    perf_category = (
        performance.groupby("category", as_index=False)[
            ["return_1yr_pct", "return_3yr_pct", "return_5yr_pct"]
        ]
        .mean()
    )

    perf_melted = perf_category.melt(
        id_vars="category",
        var_name="return_period",
        value_name="avg_return_pct"
    )

    plt.figure(figsize=(12, 7))
    sns.barplot(data=perf_melted, x="category", y="avg_return_pct", hue="return_period")
    plt.title("Average Returns by Category")
    plt.xlabel("Category")
    plt.ylabel("Average Return %")
    save_matplotlib("14_average_returns_by_category.png")
    charts.append("14_average_returns_by_category.png")

    top_sharpe = performance.sort_values("sharpe_ratio", ascending=False).head(10)

    plt.figure(figsize=(12, 7))
    sns.barplot(data=top_sharpe, y="scheme_name", x="sharpe_ratio")
    plt.title("Top 10 Funds by Sharpe Ratio")
    plt.xlabel("Sharpe Ratio")
    plt.ylabel("Scheme")
    save_matplotlib("15_top_10_funds_by_sharpe_ratio.png")
    charts.append("15_top_10_funds_by_sharpe_ratio.png")

    monthly_txn = transactions.copy()
    monthly_txn["month"] = monthly_txn["transaction_date"].dt.to_period("M").astype(str)
    monthly_txn_summary = (
        monthly_txn.groupby(["month", "transaction_type"], as_index=False)["amount_inr"]
        .sum()
    )

    fig = px.line(
        monthly_txn_summary,
        x="month",
        y="amount_inr",
        color="transaction_type",
        markers=True,
        title="Monthly Transaction Value by Type"
    )
    save_plotly(fig, "16_monthly_transaction_value_by_type.png")
    charts.append("16_monthly_transaction_value_by_type.png")

    expense_data = performance.copy()

    plt.figure(figsize=(12, 7))
    sns.histplot(expense_data["expense_ratio_pct"], bins=20, kde=True)
    plt.title("Expense Ratio Distribution")
    plt.xlabel("Expense Ratio %")
    plt.ylabel("Count")
    save_matplotlib("17_expense_ratio_distribution.png")
    charts.append("17_expense_ratio_distribution.png")

    return charts


def create_notebook(charts):
    nb = nbf.v4.new_notebook()

    cells = []

    cells.append(nbf.v4.new_markdown_cell(
        "# EDA Analysis - Bluestock Mutual Fund Analytics\n\n"
        "This notebook contains exploratory data analysis for mutual fund NAV, AUM, SIP inflows, investor demographics, geography, folio growth, correlations, and portfolio sector allocation."
    ))

    setup_code = """
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

PROCESSED_DIR = Path("../data/processed")
RAW_DIR = Path("../data/raw")
CHART_DIR = Path("../reports/charts")

fund_master = pd.read_csv(PROCESSED_DIR / "01_fund_master_cleaned.csv")
nav_history = pd.read_csv(PROCESSED_DIR / "02_nav_history_cleaned.csv")
aum = pd.read_csv(PROCESSED_DIR / "03_aum_by_fund_house_cleaned.csv")
sip = pd.read_csv(PROCESSED_DIR / "04_monthly_sip_inflows_cleaned.csv")
category_inflows = pd.read_csv(PROCESSED_DIR / "05_category_inflows_cleaned.csv")
folio = pd.read_csv(PROCESSED_DIR / "06_industry_folio_count_cleaned.csv")
performance = pd.read_csv(PROCESSED_DIR / "07_scheme_performance_cleaned.csv")
transactions = pd.read_csv(PROCESSED_DIR / "08_investor_transactions_cleaned.csv")
holdings = pd.read_csv(PROCESSED_DIR / "09_portfolio_holdings_cleaned.csv")
benchmark = pd.read_csv(PROCESSED_DIR / "10_benchmark_indices_cleaned.csv")

nav_history["date"] = pd.to_datetime(nav_history["date"])
aum["date"] = pd.to_datetime(aum["date"])
sip["month"] = pd.to_datetime(sip["month"])
category_inflows["month"] = pd.to_datetime(category_inflows["month"])
folio["month"] = pd.to_datetime(folio["month"])
transactions["transaction_date"] = pd.to_datetime(transactions["transaction_date"])
holdings["portfolio_date"] = pd.to_datetime(holdings["portfolio_date"])
benchmark["date"] = pd.to_datetime(benchmark["date"])
"""
    cells.append(nbf.v4.new_code_cell(setup_code))

    insights = [
        ("NAV Trend Analysis", "The NAV trend chart shows broad scheme-level growth from 2022 to 2026, with visible market expansion during 2023 and correction windows during 2024.", "01_nav_trend_all_40_schemes.png"),
        ("Indexed NAV Growth", "Indexing NAV to a base of 100 makes cross-scheme growth comparison easier because funds have different absolute NAV scales.", "02_indexed_nav_growth_all_schemes.png"),
        ("AUM Growth", "Fund-house AUM shows strong year-wise expansion, with SBI highlighted as the dominant player at approximately ₹12.5 lakh crore.", "03_aum_growth_by_fund_house.png"),
        ("SIP Inflow Trend", "Monthly SIP inflows show a strong upward trend, reaching the observed peak around Dec 2025.", "04_sip_inflow_time_series.png"),
        ("Category Inflows", "Category-wise inflow intensity varies significantly across months, indicating changing investor preference across fund categories.", "05_category_inflow_heatmap.png"),
        ("Investor Age Distribution", "Investor participation is spread across age groups, showing broad retail participation in mutual fund transactions.", "06_age_group_distribution_pie.png"),
        ("SIP Amount by Age", "SIP ticket sizes differ across age groups, with boxplots showing variation and potential outliers in investor contribution amounts.", "07_sip_amount_boxplot_by_age_group.png"),
        ("Gender Split", "The gender split chart highlights the composition of investors across recorded gender categories.", "08_gender_split.png"),
        ("Geographic SIP Distribution", "State-level SIP contribution shows geographic concentration in specific states.", "09_sip_amount_by_state.png"),
        ("City Tier Split", "The T30 versus B30 split shows how mutual fund transactions are distributed between top cities and beyond-top-30 cities.", "10_city_tier_split.png"),
        ("Folio Growth", "Industry folios show strong growth from the starting value to the latest available value, reflecting expanding investor participation.", "11_folio_count_growth.png"),
        ("NAV Return Correlation", "The correlation matrix shows how similarly selected funds move on a daily return basis.", "12_nav_return_correlation_matrix.png"),
        ("Sector Allocation", "The sector allocation donut shows aggregate sector exposure across portfolio holdings.", "13_sector_allocation_donut.png"),
        ("Returns by Category", "Average returns differ by category and return horizon, highlighting the risk-return profile of fund segments.", "14_average_returns_by_category.png"),
        ("Sharpe Ratio Leaders", "The top Sharpe ratio funds indicate schemes with stronger risk-adjusted performance.", "15_top_10_funds_by_sharpe_ratio.png"),
        ("Transaction Trend", "Monthly transaction value by type shows how SIP, lumpsum, and redemption behaviour varies over time.", "16_monthly_transaction_value_by_type.png"),
        ("Expense Ratio", "The expense ratio distribution confirms whether fund costs mostly fall within the expected 0.1% to 2.5% range.", "17_expense_ratio_distribution.png"),
    ]

    for title, insight, chart in insights:
        cells.append(nbf.v4.new_markdown_cell(
            f"## {title}\n\n"
            f"**Insight:** {insight}\n\n"
            f"**Supporting chart:** `reports/charts/{chart}`"
        ))

    cells.append(nbf.v4.new_markdown_cell(
        "## Key EDA Findings Summary\n\n"
        "1. NAVs generally show upward movement across the 2022–2026 period.\n"
        "2. Indexed NAV comparison makes relative fund performance clearer.\n"
        "3. SBI shows strong AUM dominance in the fund-house comparison.\n"
        "4. SIP inflows show sustained growth and reach a peak near Dec 2025.\n"
        "5. Category inflows vary month by month, showing changing investor preference.\n"
        "6. Investor demographics show participation across multiple age groups.\n"
        "7. SIP amount distribution has visible variation across age groups.\n"
        "8. State-wise SIP contribution is not evenly distributed.\n"
        "9. Folio count growth suggests strong retail mutual fund adoption.\n"
        "10. NAV return correlations indicate that some funds move closely together."
    ))

    nb["cells"] = cells

    notebook_path = NOTEBOOK_DIR / "EDA_Analysis.ipynb"
    with open(notebook_path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)

    print(f"Saved notebook: {notebook_path}")


def main():
    print("Preparing EDA data...")
    data = prepare_data()

    print("Generating charts...")
    charts = generate_charts(data)

    print("Creating notebook...")
    create_notebook(charts)

    print("\nEDA deliverables generated successfully.")
    print(f"Notebook: {NOTEBOOK_DIR / 'EDA_Analysis.ipynb'}")
    print(f"Charts folder: {CHART_DIR}")
    print(f"Total charts generated: {len(charts)}")


if __name__ == "__main__":
    main()