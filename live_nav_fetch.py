from pathlib import Path
import requests
import pandas as pd


RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)


SCHEMES = {
    "hdfc_top_100_direct": 125497,
    "sbi_bluechip": 119551,
    "icici_bluechip": 120503,
    "nippon_large_cap": 118632,
    "axis_bluechip": 119092,
    "kotak_bluechip": 120841,
}


def fetch_nav_data(scheme_name, scheme_code):
    url = f"https://api.mfapi.in/mf/{scheme_code}"

    print("=" * 100)
    print(f"Fetching NAV data for {scheme_name}")
    print(f"Scheme Code: {scheme_code}")

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        json_data = response.json()

        meta = json_data.get("meta", {})
        nav_data = json_data.get("data", [])

        if not nav_data:
            print(f"No NAV data found for {scheme_name}")
            return None

        df = pd.DataFrame(nav_data)

        df["scheme_code"] = meta.get("scheme_code", scheme_code)
        df["scheme_name"] = meta.get("scheme_name", scheme_name)
        df["fund_house"] = meta.get("fund_house")
        df["scheme_type"] = meta.get("scheme_type")
        df["scheme_category"] = meta.get("scheme_category")

        output_file = RAW_DIR / f"{scheme_name}_live_nav.csv"
        df.to_csv(output_file, index=False)

        print(f"Saved: {output_file}")
        print("Shape:", df.shape)
        print(df.head())

        return df

    except requests.exceptions.RequestException as e:
        print(f"Request error for {scheme_name}: {e}")
    except ValueError as e:
        print(f"JSON parsing error for {scheme_name}: {e}")
    except Exception as e:
        print(f"Unexpected error for {scheme_name}: {e}")

    return None


def main():
    all_dataframes = []

    for scheme_name, scheme_code in SCHEMES.items():
        df = fetch_nav_data(scheme_name, scheme_code)

        if df is not None:
            all_dataframes.append(df)

    if all_dataframes:
        combined_df = pd.concat(all_dataframes, ignore_index=True)
        combined_output = RAW_DIR / "all_fetched_live_nav.csv"
        combined_df.to_csv(combined_output, index=False)

        print("=" * 100)
        print(f"Combined NAV file saved: {combined_output}")
        print("Combined Shape:", combined_df.shape)


if __name__ == "__main__":
    main()