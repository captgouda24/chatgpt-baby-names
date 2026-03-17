"""
Merge ChatGPT name recommendations with SSA data to create analysis-ready dataset.
"""

import numpy as np
import pandas as pd
from pathlib import Path

def load_chatgpt_names(filepath: Path = None) -> pd.DataFrame:
    """Load ChatGPT name recommendations."""
    if filepath is None:
        # Prefer the model-specific file if it exists
        data_dir = Path(__file__).parent.parent / "data" / "processed"
        if (data_dir / "chatgpt_names_gpt_3.5_turbo.csv").exists():
            filepath = data_dir / "chatgpt_names_gpt_3.5_turbo.csv"
        else:
            filepath = data_dir / "chatgpt_names.csv"

    df = pd.read_csv(filepath)
    print(f"Loaded {len(df)} ChatGPT-recommended names from {filepath.name}")
    return df

def load_ssa_panel(filepath: Path = None) -> pd.DataFrame:
    """Load SSA panel data."""
    if filepath is None:
        filepath = Path(__file__).parent.parent / "data" / "processed" / "ssa_names_panel.csv"

    df = pd.read_csv(filepath)
    print(f"Loaded {len(df):,} SSA records ({df['name'].nunique():,} unique names)")
    return df

def create_treatment_indicator(ssa_df: pd.DataFrame, chatgpt_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create the treatment indicator:
    - treated = 1 if name appears in ChatGPT recommendations
    - chatgpt_freq = how many times ChatGPT recommended this name
    """
    # Normalize names for matching (lowercase)
    chatgpt_names = set(chatgpt_df["name"].str.lower())

    # Create treatment indicator
    ssa_df = ssa_df.copy()
    ssa_df["name_lower"] = ssa_df["name"].str.lower()
    ssa_df["treated"] = ssa_df["name_lower"].isin(chatgpt_names).astype(int)

    # Merge frequency
    chatgpt_df = chatgpt_df.copy()
    chatgpt_df["name_lower"] = chatgpt_df["name"].str.lower()
    freq_map = chatgpt_df.set_index("name_lower")["frequency"].to_dict()
    ssa_df["chatgpt_freq"] = ssa_df["name_lower"].map(freq_map).fillna(0).astype(int)

    # Create post-treatment indicator (ChatGPT launched Nov 2022)
    ssa_df["post"] = (ssa_df["year"] >= 2023).astype(int)

    # DiD interaction term
    ssa_df["treated_x_post"] = ssa_df["treated"] * ssa_df["post"]

    # Clean up
    ssa_df = ssa_df.drop(columns=["name_lower"])

    return ssa_df

def create_analysis_dataset(ssa_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create the final analysis dataset with useful derived variables.
    """
    df = ssa_df.copy()

    # Log count (for regression)
    df["log_count"] = np.log(df["count"].replace(0, 1))

    # Name fixed effects (numeric ID for each name)
    df["name_id"] = df.groupby("name").ngroup()

    # Year fixed effects
    df["year_fe"] = df["year"]

    # Summary stats
    print("\n" + "=" * 50)
    print("ANALYSIS DATASET SUMMARY")
    print("=" * 50)
    print(f"Total observations: {len(df):,}")
    print(f"Unique names: {df['name'].nunique():,}")
    print(f"Years: {df['year'].min()}-{df['year'].max()}")
    print(f"\nTreatment breakdown:")
    print(f"  Treated names: {df[df['treated']==1]['name'].nunique():,}")
    print(f"  Control names: {df[df['treated']==0]['name'].nunique():,}")
    print(f"\nPre/Post breakdown:")
    print(f"  Pre-treatment (2015-2022): {len(df[df['post']==0]):,} obs")
    print(f"  Post-treatment (2023+): {len(df[df['post']==1]):,} obs")

    # Mean outcomes by group
    print("\nMean count by treatment/period:")
    summary = df.groupby(["treated", "post"])["count"].mean().unstack()
    summary.columns = ["Pre (2015-2022)", "Post (2023+)"]
    summary.index = ["Control", "Treated"]
    print(summary.round(1))

    return df

def save_analysis_data(df: pd.DataFrame, output_dir: Path = None):
    """Save the analysis-ready dataset."""
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "data"

    # Full dataset
    output_file = output_dir / "analysis_ready.csv"
    df.to_csv(output_file, index=False)
    print(f"\nSaved analysis dataset to: {output_file}")

    # Also save a Stata-friendly version
    try:
        stata_file = output_dir / "analysis_ready.dta"
        df.to_stata(stata_file, write_index=False)
        print(f"Saved Stata dataset to: {stata_file}")
    except Exception as e:
        print(f"Note: Could not save Stata file ({e})")

    return output_file

def main():
    # Load data
    chatgpt_df = load_chatgpt_names()
    ssa_df = load_ssa_panel()

    # Create treatment indicator
    df = create_treatment_indicator(ssa_df, chatgpt_df)

    # Create analysis dataset
    df = create_analysis_dataset(df)

    # Save
    save_analysis_data(df)

    # Print regression specification hint
    print("\n" + "=" * 50)
    print("SUGGESTED DIFF-IN-DIFF SPECIFICATION")
    print("=" * 50)
    print("""
Stata:
  reghdfe log_count treated_x_post, absorb(name_id year_fe) cluster(name_id)

R:
  library(fixest)
  feols(log(count) ~ treated_x_post | name + year, data = df, cluster = "name")

Python (linearmodels):
  from linearmodels.panel import PanelOLS
  mod = PanelOLS.from_formula('log_count ~ treated_x_post + EntityEffects + TimeEffects', data=df.set_index(['name_id', 'year']))

Key variables:
  - count: Number of babies with this name
  - treated: 1 if ChatGPT recommends this name
  - post: 1 if year >= 2023
  - treated_x_post: DiD coefficient (THE EFFECT OF INTEREST)
  - chatgpt_freq: How often ChatGPT recommends (for intensity analysis)
""")

if __name__ == "__main__":
    main()
