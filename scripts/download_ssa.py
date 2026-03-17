"""
Download and process SSA baby name data.
Source: https://www.ssa.gov/oact/babynames/
"""

import io
import zipfile
import requests
import pandas as pd
from pathlib import Path

SSA_URL = "https://www.ssa.gov/oact/babynames/names.zip"

def download_ssa_data(output_dir: Path = None) -> Path:
    """Download the SSA national baby names zip file."""
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "data" / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)

    zip_path = output_dir / "names.zip"

    print(f"Downloading SSA data from {SSA_URL}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    response = requests.get(SSA_URL, headers=headers)
    response.raise_for_status()

    with open(zip_path, "wb") as f:
        f.write(response.content)

    print(f"Saved to {zip_path}")
    return zip_path

def process_ssa_data(zip_path: Path = None, years: tuple = (2015, 2024)) -> pd.DataFrame:
    """
    Extract and process SSA data into a panel dataset.
    Each row: (name, sex, year, count)
    """
    if zip_path is None:
        zip_path = Path(__file__).parent.parent / "data" / "raw" / "names.zip"

    print(f"Processing SSA data for years {years[0]}-{years[1]}...")

    all_data = []

    with zipfile.ZipFile(zip_path, "r") as zf:
        for year in range(years[0], years[1] + 1):
            filename = f"yob{year}.txt"

            try:
                with zf.open(filename) as f:
                    content = f.read().decode("utf-8")

                for line in content.strip().split("\n"):
                    parts = line.strip().split(",")
                    if len(parts) == 3:
                        name, sex, count = parts
                        all_data.append({
                            "name": name,
                            "sex": sex,
                            "year": year,
                            "count": int(count),
                        })

                print(f"  Processed {filename}")

            except KeyError:
                print(f"  WARNING: {filename} not found in archive (year {year} may not be available yet)")

    df = pd.DataFrame(all_data)

    # Calculate rank within each year and sex
    df["rank"] = df.groupby(["year", "sex"])["count"].rank(ascending=False, method="min")

    # Calculate year-over-year growth
    df = df.sort_values(["name", "sex", "year"])
    df["prev_count"] = df.groupby(["name", "sex"])["count"].shift(1)
    df["yoy_growth"] = (df["count"] - df["prev_count"]) / df["prev_count"]

    print(f"\nTotal records: {len(df):,}")
    print(f"Unique names: {df['name'].nunique():,}")
    print(f"Years: {df['year'].min()}-{df['year'].max()}")

    return df

def save_processed_data(df: pd.DataFrame, output_dir: Path = None):
    """Save the processed data."""
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Full panel
    panel_file = output_dir / "ssa_names_panel.csv"
    df.to_csv(panel_file, index=False)
    print(f"Saved panel data to: {panel_file}")

    # Summary by name (for merging with ChatGPT data)
    summary = df.groupby(["name", "sex"]).agg({
        "count": ["sum", "mean"],
        "rank": "min",
        "year": ["min", "max"],
    }).reset_index()
    summary.columns = ["name", "sex", "total_count", "mean_annual_count", "best_rank", "first_year", "last_year"]

    summary_file = output_dir / "ssa_names_summary.csv"
    summary.to_csv(summary_file, index=False)
    print(f"Saved summary data to: {summary_file}")

    return panel_file, summary_file

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-year", type=int, default=2015)
    parser.add_argument("--end-year", type=int, default=2024)
    parser.add_argument("--skip-download", action="store_true",
                        help="Skip download if names.zip already exists")
    args = parser.parse_args()

    data_dir = Path(__file__).parent.parent / "data"
    zip_path = data_dir / "raw" / "names.zip"

    # Download
    if not args.skip_download or not zip_path.exists():
        download_ssa_data()
    else:
        print(f"Using existing {zip_path}")

    # Process
    df = process_ssa_data(zip_path, years=(args.start_year, args.end_year))

    # Save
    save_processed_data(df)

    # Quick stats
    print("\n" + "=" * 50)
    print("Top 10 names by total count (2015-2024):")
    top = df.groupby("name")["count"].sum().nlargest(10)
    for name, count in top.items():
        print(f"  {name}: {count:,}")

if __name__ == "__main__":
    main()
