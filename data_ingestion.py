from pathlib import Path
import pandas as pd

RAW_DIR = Path("data/raw")

def load_all_csv_files():
    csv_files=list(RAW_DIR.glob("*.csv"))

    if not csv_files:
        print("NO CSV files fount in data/raw.")
        return{}
    
    datasets={}

    print(f"Found {len(csv_files)} CSV files.\n")

    for file_path in csv_files:
        print("="*100)
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
                if "date" in col.lower()
            ]

            if possible_date_cols:
                print(f"- Possible date columns found: {possible_date_cols}")

            possible_nav_cols = [
                col for col in df.columns
                if "nav" in col.lower()
            ]

            if possible_nav_cols:
                print(f"- Possible NAV columns found: {possible_nav_cols}")

            possible_code_cols = [
                col for col in df.columns
                if "code" in col.lower() or "scheme" in col.lower()
            ]

            if possible_code_cols:
                print(f"- Possible scheme/code columns found: {possible_code_cols}")

        except Exception as e:
            print(f"Error loading {file_path.name}: {e}")

        print("\n")

    return datasets


def explore_fund_master(datasets):
    print("=" * 100)
    print("FUND MASTER EXPLORATION")

    fund_master_key = None

    for key in datasets:
        if "fund" in key.lower() and "master" in key.lower():
            fund_master_key = key
            break

    if fund_master_key is None:
        print("fund_master file not found. Please check the filename.")
        return

    fund_master = datasets[fund_master_key]

    print(f"Using file: {fund_master_key}.csv")

    columns_to_check = [
        "fund_house",
        "category",
        "sub_category",
        "risk_grade",
        "scheme_code"
    ]

    for col in columns_to_check:
        if col in fund_master.columns:
            print(f"\nUnique values in {col}:")
            print(fund_master[col].dropna().unique())
        else:
            print(f"\nColumn not found: {col}")


def validate_amfi_codes(datasets):
    print("=" * 100)
    print("AMFI CODE VALIDATION")

    fund_master_key = None
    nav_history_key = None

    for key in datasets:
        lower_key = key.lower()

        if "fund" in lower_key and "master" in lower_key:
            fund_master_key = key

        if "nav" in lower_key and "history" in lower_key:
            nav_history_key = key

    if fund_master_key is None:
        print("fund_master file not found.")
        return

    if nav_history_key is None:
        print("nav_history file not found.")
        return

    fund_master = datasets[fund_master_key]
    nav_history = datasets[nav_history_key]

    possible_fund_code_cols = [
        col for col in fund_master.columns
        if "scheme" in col.lower() and "code" in col.lower()
    ]

    possible_nav_code_cols = [
        col for col in nav_history.columns
        if "scheme" in col.lower() and "code" in col.lower()
    ]

    if not possible_fund_code_cols:
        print("No scheme code column found in fund_master.")
        return

    if not possible_nav_code_cols:
        print("No scheme code column found in nav_history.")
        return

    fund_code_col = possible_fund_code_cols[0]
    nav_code_col = possible_nav_code_cols[0]

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
        print(list(missing_in_nav)[:50])
    else:
        print("\nAll fund_master scheme codes exist in nav_history.")

    print("\nDATA QUALITY SUMMARY")
    print("- CSV files loaded successfully from data/raw.")
    print(f"- fund_master contains {len(fund_codes)} unique AMFI scheme codes.")
    print(f"- nav_history contains {len(nav_codes)} unique AMFI scheme codes.")
    print(f"- {len(missing_in_nav)} fund_master codes are missing in nav_history.")

    print("\nRecommended cleaning for next step:")
    print("- Convert date columns to datetime.")
    print("- Convert NAV columns to numeric.")
    print("- Standardize scheme_code columns as string.")
    print("- Handle missing values and duplicate rows.")


if __name__ == "__main__":
    datasets = load_all_csv_files()
    explore_fund_master(datasets)
    validate_amfi_codes(datasets)