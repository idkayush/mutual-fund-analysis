from pathlib import Path
import pandas as pd


RAW_DIR = Path("data/raw")


def load_all_csv_files():
    csv_files = list(RAW_DIR.glob("*.csv"))

    if not csv_files:
        print("No CSV files found in data/raw.")
        return {}

    datasets = {}

    print(f"Found {len(csv_files)} CSV files.\n")

    for file_path in csv_files:
        print("=" * 100)
        print(f"File: {file_path.name}")

        try:
            df = pd.read_csv(file_path)
            datasets[file_path.stem] = df

            print("\nShape:")
            print(df.shape)

            print("\nData Types:")
            print(df.dtypes)

            print("\nFirst 5 Rows:")
            print(df.head())

            print("\nMissing Values:")
            print(df.isnull().sum())

            print("\nDuplicate Rows:")
            print(df.duplicated().sum())

            print("\nBasic Anomaly Notes:")

            if df.empty:
                print("- Dataset is empty.")

            missing_cols = df.columns[df.isnull().any()].tolist()
            if missing_cols:
                print(f"- Columns with missing values: {missing_cols}")
            else:
                print("- No missing values found.")

            duplicate_count = df.duplicated().sum()
            if duplicate_count > 0:
                print(f"- Found {duplicate_count} duplicate rows.")
            else:
                print("- No duplicate rows found.")

            possible_date_cols = [
                col for col in df.columns
                if "date" in col.lower() or "month" in col.lower()
            ]

            if possible_date_cols:
                print(f"- Possible date/month columns found: {possible_date_cols}")

            possible_nav_cols = [
                col for col in df.columns
                if "nav" in col.lower()
            ]

            if possible_nav_cols:
                print(f"- Possible NAV columns found: {possible_nav_cols}")

            possible_code_cols = [
                col for col in df.columns
                if "code" in col.lower() or "scheme" in col.lower() or "amfi" in col.lower()
            ]

            if possible_code_cols:
                print(f"- Possible scheme/code columns found: {possible_code_cols}")

        except Exception as e:
            print(f"Error loading {file_path.name}: {e}")

        print("\n")

    return datasets


def find_dataset_key(datasets, keywords):
    for key in datasets:
        lower_key = key.lower()
        if all(keyword in lower_key for keyword in keywords):
            return key
    return None


def explore_fund_master(datasets):
    print("=" * 100)
    print("FUND MASTER EXPLORATION")

    fund_master_key = None

    for key in datasets:
        lower_key = key.lower()
        if "fund_master" in lower_key or "fund" in lower_key and "master" in lower_key:
            fund_master_key = key
            break

    if fund_master_key is None:
        print("fund_master file not found. Please check the filename.")
        return

    fund_master = datasets[fund_master_key]

    print(f"Using file: {fund_master_key}.csv")

    column_aliases = {
        "fund_house": ["fund_house"],
        "category": ["category"],
        "sub_category": ["sub_category"],
        "risk": ["risk_grade", "risk_category"],
        "scheme_code": ["scheme_code", "amfi_code", "code"],
    }

    for display_name, possible_cols in column_aliases.items():
        found_col = None

        for col in possible_cols:
            if col in fund_master.columns:
                found_col = col
                break

        if found_col:
            print(f"\nUnique values in {found_col}:")
            print(fund_master[found_col].dropna().unique())
        else:
            print(f"\nColumn not found for: {display_name}")


def validate_amfi_codes(datasets):
    print("=" * 100)
    print("AMFI CODE VALIDATION")

    fund_master_key = None
    nav_history_key = None

    for key in datasets:
        lower_key = key.lower()

        if "fund_master" in lower_key or ("fund" in lower_key and "master" in lower_key):
            fund_master_key = key

        if "nav_history" in lower_key or ("nav" in lower_key and "history" in lower_key):
            nav_history_key = key

    if fund_master_key is None:
        print("fund_master file not found.")
        return

    if nav_history_key is None:
        print("nav_history file not found.")
        return

    fund_master = datasets[fund_master_key]
    nav_history = datasets[nav_history_key]

    possible_code_cols = ["scheme_code", "amfi_code", "code"]

    fund_code_col = None
    nav_code_col = None

    for col in possible_code_cols:
        if col in fund_master.columns:
            fund_code_col = col
            break

    for col in possible_code_cols:
        if col in nav_history.columns:
            nav_code_col = col
            break

    if fund_code_col is None:
        print("No AMFI/scheme code column found in fund_master.")
        print("Available columns:", list(fund_master.columns))
        return

    if nav_code_col is None:
        print("No AMFI/scheme code column found in nav_history.")
        print("Available columns:", list(nav_history.columns))
        return

    print(f"Using fund_master code column: {fund_code_col}")
    print(f"Using nav_history code column: {nav_code_col}")

    fund_codes = set(fund_master[fund_code_col].dropna().astype(str))
    nav_codes = set(nav_history[nav_code_col].dropna().astype(str))

    missing_in_nav = fund_codes - nav_codes

    print("\nTotal unique codes in fund_master:", len(fund_codes))
    print("Total unique codes in nav_history:", len(nav_codes))
    print("Codes missing in nav_history:", len(missing_in_nav))

    if missing_in_nav:
        print("\nMissing AMFI codes:")
        print(sorted(list(missing_in_nav))[:50])
    else:
        print("\nAll fund_master AMFI codes exist in nav_history.")

    print("\nDATA QUALITY SUMMARY")
    print("- Loaded all available CSV datasets from data/raw.")
    print(f"- fund_master contains {len(fund_codes)} unique AMFI codes.")
    print(f"- nav_history contains {len(nav_codes)} unique AMFI codes.")
    print(f"- {len(missing_in_nav)} fund_master AMFI codes are missing in nav_history.")
    print("- Most datasets have no missing values or duplicate rows.")
    print("- 04_monthly_sip_inflows.csv has missing values in yoy_growth_pct.")
    print("- This is likely because YoY growth cannot be calculated for the first 12 months.")
    print("- Date/month columns are currently stored as object/string and should be converted to datetime in preprocessing.")
    print("- API scheme-code labels show inconsistencies and should be verified before final analysis.")


def main():
    datasets = load_all_csv_files()
    explore_fund_master(datasets)
    validate_amfi_codes(datasets)


if __name__ == "__main__":
    main()