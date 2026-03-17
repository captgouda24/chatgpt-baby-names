"""
Diff-in-diff with matching on pre-trends.
Match treated names to control names with similar pre-ChatGPT trajectories.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy.spatial.distance import cdist

# Load data
data_dir = Path(__file__).parent.parent / "data"
df = pd.read_csv(data_dir / "analysis_ready.csv")

print("="*60)
print("DIFF-IN-DIFF WITH PRE-TREND MATCHING")
print("="*60)

# Step 1: Calculate pre-treatment characteristics for each name
print("\n1. Calculating pre-treatment characteristics...")

pre = df[df['post'] == 0].copy()  # 2015-2022

# For each name, calculate:
# - Mean log count (level)
# - Trend (slope of log count over time)
# - Volatility (std dev of log count)

def calc_trend(group):
    if len(group) < 3:
        return np.nan
    x = group['year'].values - group['year'].mean()
    y = group['log_count'].values
    slope = np.sum(x * (y - y.mean())) / np.sum(x**2) if np.sum(x**2) > 0 else 0
    return slope

pre_chars = pre.groupby('name').agg({
    'log_count': ['mean', 'std'],
    'count': 'mean',
    'treated': 'first',
    'chatgpt_freq': 'first',
}).reset_index()
pre_chars.columns = ['name', 'pre_mean_log', 'pre_std_log', 'pre_mean_count', 'treated', 'chatgpt_freq']

# Calculate trend
trends = pre.groupby('name').apply(calc_trend, include_groups=False).reset_index()
trends.columns = ['name', 'pre_trend']
pre_chars = pre_chars.merge(trends, on='name')

# Fill NaN std with 0
pre_chars['pre_std_log'] = pre_chars['pre_std_log'].fillna(0)
pre_chars['pre_trend'] = pre_chars['pre_trend'].fillna(0)

print(f"   Names with pre-period data: {len(pre_chars):,}")
print(f"   Treated: {pre_chars['treated'].sum()}")
print(f"   Control: {(~pre_chars['treated'].astype(bool)).sum()}")

# Step 2: Match treated to controls
print("\n2. Matching treated to controls on pre-trends...")

treated_chars = pre_chars[pre_chars['treated'] == 1].copy()
control_chars = pre_chars[pre_chars['treated'] == 0].copy()

# Standardize matching variables
match_vars = ['pre_mean_log', 'pre_trend', 'pre_std_log']
for var in match_vars:
    mean_val = pre_chars[var].mean()
    std_val = pre_chars[var].std()
    treated_chars[f'{var}_z'] = (treated_chars[var] - mean_val) / std_val
    control_chars[f'{var}_z'] = (control_chars[var] - mean_val) / std_val

# Calculate distance matrix
treated_X = treated_chars[[f'{v}_z' for v in match_vars]].values
control_X = control_chars[[f'{v}_z' for v in match_vars]].values

# Handle any NaN
treated_X = np.nan_to_num(treated_X, 0)
control_X = np.nan_to_num(control_X, 0)

distances = cdist(treated_X, control_X, metric='euclidean')

# For each treated, find k nearest controls (with replacement)
k = 5  # 5 nearest neighbors
matches = []
for i, treated_name in enumerate(treated_chars['name'].values):
    nearest_idx = np.argsort(distances[i])[:k]
    for j in nearest_idx:
        matches.append({
            'treated_name': treated_name,
            'control_name': control_chars.iloc[j]['name'],
            'distance': distances[i, j],
        })

matches_df = pd.DataFrame(matches)
matched_controls = matches_df['control_name'].unique()
print(f"   Matched {len(treated_chars)} treated to {len(matched_controls)} unique controls")
print(f"   Average match distance: {matches_df['distance'].mean():.3f}")

# Step 3: Create matched sample
print("\n3. Creating matched sample...")

matched_names = set(treated_chars['name'].tolist() + list(matched_controls))
df_matched = df[df['name'].isin(matched_names)].copy()

print(f"   Matched sample: {len(df_matched):,} observations")
print(f"   Names: {df_matched['name'].nunique()}")

# Step 4: Run DiD on matched sample
print("\n" + "="*60)
print("RESULTS: MATCHED SAMPLE")
print("="*60)

# 2x2 table
print("\nMean log(count) by group:")
did_table = df_matched.groupby(['treated', 'post'])['log_count'].mean().unstack()
did_table.columns = ['Pre (2015-22)', 'Post (2023-24)']
did_table.index = ['Control', 'Treated']
did_table['Diff'] = did_table['Post (2023-24)'] - did_table['Pre (2015-22)']
print(did_table.round(4))

control_diff = did_table.loc['Control', 'Diff']
treated_diff = did_table.loc['Treated', 'Diff']
did_estimate = treated_diff - control_diff
print(f"\nDiD Estimate: {did_estimate:.4f}")
print(f"Implied % effect: {(np.exp(did_estimate) - 1) * 100:.2f}%")

# Event study on matched sample
print("\n" + "-"*60)
print("EVENT STUDY (Matched Sample)")
print("-"*60)

yearly = df_matched.groupby(['year', 'treated'])['log_count'].mean().unstack()
yearly.columns = ['Control', 'Treated']
yearly['Gap'] = yearly['Treated'] - yearly['Control']
yearly['Gap_norm'] = yearly['Gap'] - yearly.loc[2022, 'Gap']
print(yearly[['Control', 'Treated', 'Gap', 'Gap_norm']].round(4))

# Fixed effects regression
print("\n" + "-"*60)
print("FIXED EFFECTS REGRESSION (Matched Sample)")
print("-"*60)

# Demean
df_matched['log_count_dm'] = df_matched.groupby('name')['log_count'].transform(lambda x: x - x.mean())
df_matched['log_count_dm'] = df_matched.groupby('year')['log_count_dm'].transform(lambda x: x - x.mean())
df_matched['txp_dm'] = df_matched.groupby('name')['treated_x_post'].transform(lambda x: x - x.mean())
df_matched['txp_dm'] = df_matched.groupby('year')['txp_dm'].transform(lambda x: x - x.mean())

x = df_matched['txp_dm'].values
y = df_matched['log_count_dm'].values
beta = np.sum(x * y) / np.sum(x**2)

# Clustered SE by name
df_matched['resid'] = y - beta * x
cluster_var = df_matched.groupby('name').apply(
    lambda g: (g['txp_dm'] * g['resid']).sum()**2,
    include_groups=False
)
n_clusters = len(cluster_var)
meat = cluster_var.sum()
bread = np.sum(x**2)**2
se_clustered = np.sqrt(n_clusters / (n_clusters - 1) * meat / bread)

print(f"Treated x Post: {beta:.4f}")
print(f"Clustered SE:   {se_clustered:.4f}")
print(f"t-statistic:    {beta/se_clustered:.2f}")
print(f"Implied effect: {(np.exp(beta) - 1) * 100:.2f}%")

# Step 5: Compare pre-trends
print("\n" + "-"*60)
print("PRE-TREND BALANCE CHECK")
print("-"*60)

# Check if matching improved balance
balance = pd.DataFrame({
    'Treated': treated_chars[match_vars].mean(),
    'All Control': control_chars[match_vars].mean(),
    'Matched Control': pre_chars[pre_chars['name'].isin(matched_controls)][match_vars].mean(),
})
balance['Std Diff (All)'] = (balance['Treated'] - balance['All Control']) / pre_chars[match_vars].std()
balance['Std Diff (Matched)'] = (balance['Treated'] - balance['Matched Control']) / pre_chars[match_vars].std()
print(balance.round(3))

print("\n" + "="*60)
print("COMPARISON: FULL VS MATCHED SAMPLE")
print("="*60)

# Full sample DiD
did_full = df.groupby(['treated', 'post'])['log_count'].mean().unstack()
full_did = (did_full.loc[1, 1] - did_full.loc[1, 0]) - (did_full.loc[0, 1] - did_full.loc[0, 0])

print(f"\nFull sample DiD:    {full_did:.4f} ({(np.exp(full_did)-1)*100:.1f}%)")
print(f"Matched sample DiD: {did_estimate:.4f} ({(np.exp(did_estimate)-1)*100:.1f}%)")
print(f"\nDifference: {did_estimate - full_did:.4f}")

if abs(did_estimate) < abs(full_did):
    print("\n→ Effect SMALLER after matching (some of original effect was pre-trend differences)")
else:
    print("\n→ Effect LARGER/SIMILAR after matching (robust to pre-trend controls)")
