"""
Process SSA state-level baby name data.
"""

import zipfile
import pandas as pd
from pathlib import Path

def process_state_data(zip_path: Path = None, years: tuple = (2015, 2024)) -> pd.DataFrame:
    """Process state-level SSA data."""
    if zip_path is None:
        zip_path = Path(__file__).parent.parent / "data" / "raw" / "namesbystate.zip"

    print(f"Processing state-level data from {zip_path}")
    print(f"Years: {years[0]}-{years[1]}")

    all_data = []

    with zipfile.ZipFile(zip_path, "r") as zf:
        # List files in archive
        files = [f for f in zf.namelist() if f.endswith('.TXT')]
        print(f"Found {len(files)} state files")

        for filename in files:
            state = filename.replace('.TXT', '')

            with zf.open(filename) as f:
                content = f.read().decode("utf-8")

            for line in content.strip().split("\n"):
                parts = line.strip().split(",")
                if len(parts) == 5:
                    st, sex, year, name, count = parts
                    year = int(year)
                    if years[0] <= year <= years[1]:
                        all_data.append({
                            "state": st,
                            "sex": sex,
                            "year": year,
                            "name": name,
                            "count": int(count),
                        })

        print(f"  Processed {len(files)} states")

    df = pd.DataFrame(all_data)

    print(f"\nTotal records: {len(df):,}")
    print(f"States: {df['state'].nunique()}")
    print(f"Unique names: {df['name'].nunique():,}")
    print(f"Years: {df['year'].min()}-{df['year'].max()}")

    return df


def add_state_characteristics(df: pd.DataFrame) -> pd.DataFrame:
    """Add state-level characteristics for heterogeneity analysis."""

    # Tech hub states (high ChatGPT adoption expected)
    tech_states = {'CA', 'WA', 'MA', 'NY', 'CO', 'TX', 'OR', 'VA', 'MD', 'IL'}

    # Urban states (proxy for tech adoption)
    high_urban = {'NJ', 'CA', 'MA', 'NY', 'FL', 'IL', 'TX', 'PA', 'HI', 'NV'}

    df['tech_state'] = df['state'].isin(tech_states).astype(int)
    df['urban_state'] = df['state'].isin(high_urban).astype(int)

    return df


def main():
    data_dir = Path(__file__).parent.parent / "data"

    # Process state data
    df = process_state_data()

    # Add characteristics
    df = add_state_characteristics(df)

    # Save
    output_file = data_dir / "processed" / "ssa_names_state_panel.csv"
    df.to_csv(output_file, index=False)
    print(f"\nSaved to: {output_file}")

    # Quick stats by state type
    print("\n" + "="*50)
    print("SUMMARY BY STATE TYPE")
    print("="*50)

    summary = df.groupby(['tech_state', 'year'])['count'].sum().unstack(level=0)
    summary.columns = ['Non-Tech States', 'Tech States']
    print("\nTotal births by year:")
    print(summary.tail(10))

    # Top states
    print("\nTop 10 states by total names (2015-2024):")
    top_states = df.groupby('state')['count'].sum().nlargest(10)
    for state, count in top_states.items():
        tech = "(tech)" if state in {'CA', 'WA', 'MA', 'NY', 'CO', 'TX', 'OR', 'VA', 'MD', 'IL'} else ""
        print(f"  {state}: {count:,} {tech}")


if __name__ == "__main__":
    main()
