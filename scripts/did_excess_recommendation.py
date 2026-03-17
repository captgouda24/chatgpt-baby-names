"""
DiD with "excess recommendation" as treatment.
Treatment = how much MORE ChatGPT recommends a name than its baseline popularity predicts.

Intuition:
- Emma is popular AND ChatGPT recommends it a lot -> expected, not excess
- Juniper is less popular BUT ChatGPT recommends it -> excess recommendation = treatment
"""

import pandas as pd
import numpy as np
from pathlib import Path

data_dir = Path(__file__).parent.parent / "data"

print("="*60)
print("DIFF-IN-DIFF WITH EXCESS RECOMMENDATION")
print("="*60)

# Load data
ssa = pd.read_csv(data_dir / "processed" / "ssa_names_panel.csv")
chatgpt = pd.read_csv(data_dir / "processed" / "chatgpt_names_gpt_3.5_turbo.csv")

print(f"\nSSA names: {ssa['name'].nunique():,}")
print(f"ChatGPT names: {len(chatgpt)}")

# Step 1: Calculate pre-ChatGPT popularity for each name
print("\n1. Calculating pre-ChatGPT baseline popularity...")

pre_pop = ssa[ssa['year'] <= 2022].groupby('name')['count'].mean().reset_index()
pre_pop.columns = ['name', 'pre_mean_count']
pre_pop['pre_mean_log'] = np.log(pre_pop['pre_mean_count'] + 1)

# Merge ChatGPT frequency
chatgpt['name_lower'] = chatgpt['name'].str.lower()
pre_pop['name_lower'] = pre_pop['name'].str.lower()

merged = pre_pop.merge(
    chatgpt[['name_lower', 'frequency']].rename(columns={'frequency': 'chatgpt_freq'}),
    on='name_lower',
    how='left'
)
merged['chatgpt_freq'] = merged['chatgpt_freq'].fillna(0)

print(f"   Names with ChatGPT recs: {(merged['chatgpt_freq'] > 0).sum()}")

# Step 2: Regress chatgpt_freq on baseline popularity
print("\n2. Regressing ChatGPT frequency on baseline popularity...")

# Only among names ChatGPT recommends
recommended = merged[merged['chatgpt_freq'] > 0].copy()

X = np.column_stack([np.ones(len(recommended)), recommended['pre_mean_log'].values])
y = np.log1p(recommended['chatgpt_freq'].values)  # log(1 + freq)

beta = np.linalg.lstsq(X, y, rcond=None)[0]
print(f"   Intercept: {beta[0]:.3f}")
print(f"   Slope on log(pre-popularity): {beta[1]:.3f}")

# Predicted and residual
recommended['predicted_log_freq'] = beta[0] + beta[1] * recommended['pre_mean_log']
recommended['excess_rec'] = np.log1p(recommended['chatgpt_freq']) - recommended['predicted_log_freq']

print(f"\n   Excess recommendation stats:")
print(f"   Mean: {recommended['excess_rec'].mean():.3f}")
print(f"   Std:  {recommended['excess_rec'].std():.3f}")
print(f"   Min:  {recommended['excess_rec'].min():.3f}")
print(f"   Max:  {recommended['excess_rec'].max():.3f}")

# Top excess recommendations (ChatGPT loves these MORE than popularity predicts)
print("\n   Top 15 EXCESS recommendations (ChatGPT favors disproportionately):")
top_excess = recommended.nlargest(15, 'excess_rec')[['name', 'pre_mean_count', 'chatgpt_freq', 'excess_rec']]
for _, row in top_excess.iterrows():
    print(f"   {row['name']:<15} pre_pop={row['pre_mean_count']:>8.0f}  chatgpt_freq={row['chatgpt_freq']:>3.0f}  excess={row['excess_rec']:>+.2f}")

# Bottom excess (ChatGPT recommends LESS than popularity predicts)
print("\n   Bottom 15 (ChatGPT under-recommends relative to popularity):")
bottom_excess = recommended.nsmallest(15, 'excess_rec')[['name', 'pre_mean_count', 'chatgpt_freq', 'excess_rec']]
for _, row in bottom_excess.iterrows():
    print(f"   {row['name']:<15} pre_pop={row['pre_mean_count']:>8.0f}  chatgpt_freq={row['chatgpt_freq']:>3.0f}  excess={row['excess_rec']:>+.2f}")

# Step 3: Merge excess_rec back to panel
print("\n3. Creating analysis dataset...")

excess_map = recommended.set_index('name_lower')['excess_rec'].to_dict()
ssa['name_lower'] = ssa['name'].str.lower()
ssa['excess_rec'] = ssa['name_lower'].map(excess_map).fillna(0)

# Standardize
ssa['excess_rec_std'] = ssa['excess_rec'] / ssa[ssa['excess_rec'] != 0]['excess_rec'].std()

ssa['post'] = (ssa['year'] >= 2023).astype(int)
ssa['excess_x_post'] = ssa['excess_rec_std'] * ssa['post']
ssa['log_count'] = np.log(ssa['count'].replace(0, 1))

# Step 4: DiD with excess recommendation
print("\n" + "="*60)
print("4. DIFF-IN-DIFF WITH EXCESS RECOMMENDATION")
print("="*60)

# Binned analysis
ssa['excess_bin'] = pd.cut(
    ssa['excess_rec'],
    bins=[-np.inf, 0, 0.5, 1.0, np.inf],
    labels=['None/Under', 'Low Excess', 'Med Excess', 'High Excess']
)

print("\nNames per excess bin:")
for bin_name in ['None/Under', 'Low Excess', 'Med Excess', 'High Excess']:
    n = ssa[ssa['excess_bin']==bin_name]['name'].nunique()
    print(f"  {bin_name}: {n:,} names")

print("\nDiD by excess recommendation bin:")
print(f"{'Bin':<15} {'Pre':>10} {'Post':>10} {'Diff':>10} {'DiD vs None':>12}")
print("-"*60)

baseline_pre = ssa[(ssa['excess_bin']=='None/Under') & (ssa['post']==0)]['log_count'].mean()
baseline_post = ssa[(ssa['excess_bin']=='None/Under') & (ssa['post']==1)]['log_count'].mean()
baseline_diff = baseline_post - baseline_pre
print(f"{'None/Under':<15} {baseline_pre:>10.3f} {baseline_post:>10.3f} {baseline_diff:>10.3f} {'-':>12}")

for bin_name in ['Low Excess', 'Med Excess', 'High Excess']:
    pre = ssa[(ssa['excess_bin']==bin_name) & (ssa['post']==0)]['log_count'].mean()
    post = ssa[(ssa['excess_bin']==bin_name) & (ssa['post']==1)]['log_count'].mean()
    diff = post - pre
    did = diff - baseline_diff
    pct = (np.exp(did) - 1) * 100
    print(f"{bin_name:<15} {pre:>10.3f} {post:>10.3f} {diff:>10.3f} {did:>8.3f} ({pct:>+5.1f}%)")

# Event study
print("\n" + "-"*60)
print("EVENT STUDY BY EXCESS BIN (normalized to 2022)")
print("-"*60)

print(f"{'Year':<6} {'None/Under':>12} {'Low Excess':>12} {'Med Excess':>12} {'High Excess':>12}")
print("-"*55)

baseline_by_year = ssa[ssa['excess_bin']=='None/Under'].groupby('year')['log_count'].mean()

for year in range(2015, 2025):
    row = f"{year:<6}"
    for bin_name in ['None/Under', 'Low Excess', 'Med Excess', 'High Excess']:
        bin_mean = ssa[(ssa['excess_bin']==bin_name) & (ssa['year']==year)]['log_count'].mean()
        if pd.isna(bin_mean):
            row += f"{'N/A':>12}"
            continue
        gap = bin_mean - baseline_by_year[year]
        gap_2022 = ssa[(ssa['excess_bin']==bin_name) & (ssa['year']==2022)]['log_count'].mean() - baseline_by_year[2022]
        gap_norm = gap - gap_2022 if not pd.isna(gap_2022) else np.nan
        row += f"{gap_norm:>12.3f}" if not pd.isna(gap_norm) else f"{'N/A':>12}"
    print(row)

# Continuous regression
print("\n" + "-"*60)
print("FIXED EFFECTS REGRESSION (continuous excess)")
print("-"*60)

# Demean
for var in ['log_count', 'excess_x_post']:
    ssa[f'{var}_dm'] = ssa.groupby('name')[var].transform(lambda x: x - x.mean())
    ssa[f'{var}_dm'] = ssa.groupby('year')[f'{var}_dm'].transform(lambda x: x - x.mean())

x = ssa['excess_x_post_dm'].values
y = ssa['log_count_dm'].values

beta_fe = np.sum(x * y) / np.sum(x**2)
resid = y - beta_fe * x

# Clustered SE
ssa['resid'] = resid
cluster_scores = ssa.groupby('name').apply(
    lambda g: (g['excess_x_post_dm'] * g['resid']).sum(),
    include_groups=False
)
n_clusters = len(cluster_scores)
meat = np.sum(cluster_scores**2)
bread = np.sum(x**2)
se_clustered = np.sqrt((n_clusters / (n_clusters - 1)) * meat / bread**2)

print(f"Excess_rec x Post: {beta_fe:.4f}")
print(f"Clustered SE:      {se_clustered:.4f}")
print(f"t-statistic:       {beta_fe/se_clustered:.2f}")

print("\n" + "="*60)
print("INTERPRETATION")
print("="*60)
print("""
Excess recommendation = ChatGPT rec frequency BEYOND what baseline popularity predicts

- Positive excess: ChatGPT "discovers" or favors this name disproportionately
- Negative/zero excess: ChatGPT just recommends popular names as expected

If ChatGPT causally affects naming, effect should be concentrated in
HIGH EXCESS names - the ones ChatGPT surfaces beyond their baseline popularity.
""")
