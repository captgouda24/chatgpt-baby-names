"""
Diff-in-diff analysis using only GPT-3.5-turbo recommendations.
This is the free/default model most users would have encountered.
"""

import json
import numpy as np
import pandas as pd
from collections import Counter
from scipy import stats
from pathlib import Path

data_dir = Path(__file__).parent.parent / "data"

# Load only GPT-3.5-turbo responses
gpt35 = Counter()
with open(data_dir / "raw" / "chatgpt_responses_gpt_3.5_turbo.jsonl") as f:
    for line in f:
        rec = json.loads(line)
        for name in rec['extracted_names']:
            gpt35[name] += 1

print("=" * 60)
print("GPT-3.5-TURBO ONLY ANALYSIS")
print("(Free default model Nov 2022 - May 2024)")
print("=" * 60)

print(f"\nGPT-3.5-turbo: {len(gpt35)} unique names, {sum(gpt35.values())} mentions")

# Load SSA data
ssa = pd.read_csv(data_dir / "processed" / "ssa_names_panel.csv")
print(f"SSA data: {len(ssa)} rows, {ssa['name'].nunique()} unique names")

# Create recommendation df
rec_df = pd.DataFrame([
    {'name': name, 'freq': count}
    for name, count in gpt35.items()
])

# Merge with SSA to get pre-period popularity
pre = ssa[ssa['year'] <= 2022].groupby('name')['count'].mean().reset_index()
pre.columns = ['name', 'pre_popularity']

rec_df = rec_df.merge(pre, on='name', how='inner')
print(f"Names in both GPT-3.5 recs and SSA: {len(rec_df)}")

# Compute excess recommendation (residual from popularity regression)
rec_df['pre_level'] = np.log1p(rec_df['pre_popularity'])
X = np.column_stack([np.ones(len(rec_df)), rec_df['pre_level'].values])
y = np.log1p(rec_df['freq'].values)
beta = np.linalg.lstsq(X, y, rcond=None)[0]
rec_df['excess'] = y - (beta[0] + beta[1] * rec_df['pre_level'])

print(f"\nExcess recommendation regression:")
print(f"  log(freq) = {beta[0]:.3f} + {beta[1]:.3f} * log(pre_popularity)")

# Merge excess into SSA
ssa = ssa.merge(rec_df[['name', 'excess']], on='name', how='left')
ssa['excess'] = ssa['excess'].fillna(0)

# Compute pre-trend (2015-2022 linear growth) - vectorized for speed
pre_years = ssa[ssa['year'] <= 2022].copy()
pre_years['log_count'] = np.log1p(pre_years['count'])
pre_years['year_centered'] = pre_years['year'] - 2018.5

# Vectorized slope calculation using covariance formula
grp = pre_years.groupby('name')
mean_x = grp['year_centered'].transform('mean')
mean_y = grp['log_count'].transform('mean')
pre_years['xy_dev'] = (pre_years['year_centered'] - mean_x) * (pre_years['log_count'] - mean_y)
pre_years['x2_dev'] = (pre_years['year_centered'] - mean_x) ** 2

cov_xy = grp['xy_dev'].sum()
var_x = grp['x2_dev'].sum()
slopes = (cov_xy / var_x).reset_index()
slopes.columns = ['name', 'pre_trend']

# Filter names with < 3 observations
counts = grp.size()
valid_names = counts[counts >= 3].index
slopes.loc[~slopes['name'].isin(valid_names), 'pre_trend'] = np.nan

ssa = ssa.merge(slopes, on='name', how='left')

# Standardize
ssa['excess_z'] = ssa['excess'] / ssa['excess'].std()
ssa['pre_trend_z'] = (ssa['pre_trend'] - ssa['pre_trend'].mean()) / ssa['pre_trend'].std()

# Create interactions
ssa['post'] = (ssa['year'] == 2024).astype(int)
ssa['excess_z_x_post'] = ssa['excess_z'] * ssa['post']
ssa['pre_trend_z_x_post'] = ssa['pre_trend_z'] * ssa['post']
ssa['log_count'] = np.log1p(ssa['count'])

# Double-demean for name and year FE
for v in ['log_count', 'excess_z_x_post', 'pre_trend_z_x_post']:
    ssa[v+'_dm'] = ssa.groupby('name')[v].transform(lambda x: x - x.mean())
    ssa[v+'_dm'] = ssa.groupby('year')[v+'_dm'].transform(lambda x: x - x.mean())

# Regression with pre-trend control
valid = ssa.dropna(subset=['log_count_dm', 'excess_z_x_post_dm', 'pre_trend_z_x_post_dm'])
X_reg = np.column_stack([valid['excess_z_x_post_dm'], valid['pre_trend_z_x_post_dm']])
y_reg = valid['log_count_dm'].values

beta_reg = np.linalg.lstsq(X_reg, y_reg, rcond=None)[0]
resid = y_reg - X_reg @ beta_reg

# Cluster by name
clusters = valid['name'].values
unique_clusters = np.unique(clusters)
meat = np.zeros((2, 2))
for c in unique_clusters:
    mask = clusters == c
    score = X_reg[mask].T @ resid[mask].reshape(-1, 1)
    meat += score @ score.T

bread = np.linalg.inv(X_reg.T @ X_reg)
V_cluster = bread @ meat @ bread * (len(unique_clusters) / (len(unique_clusters) - 1))
se = np.sqrt(np.diag(V_cluster))

t_stat_excess = beta_reg[0] / se[0]
t_stat_trend = beta_reg[1] / se[1]
p_excess = 2 * (1 - stats.t.cdf(abs(t_stat_excess), len(unique_clusters) - 2))
p_trend = 2 * (1 - stats.t.cdf(abs(t_stat_trend), len(unique_clusters) - 2))

print("\n" + "=" * 60)
print("DIFF-IN-DIFF RESULTS (GPT-3.5-turbo only)")
print("=" * 60)

print("\nWith pre-trend control:")
print(f"  Excess Rec × Post:  {beta_reg[0]*100:+.2f}%  (SE={se[0]:.4f}, t={t_stat_excess:.2f}, p={p_excess:.3f})")
print(f"  Pre-Trend × Post:   {beta_reg[1]*100:+.2f}%  (SE={se[1]:.4f}, t={t_stat_trend:.2f}, p={p_trend:.3f})")

# Also without pre-trend control
X_no_trend = valid['excess_z_x_post_dm'].values.reshape(-1, 1)
beta_no = np.linalg.lstsq(X_no_trend, y_reg, rcond=None)[0]
resid_no = y_reg - X_no_trend @ beta_no

meat_no = np.zeros((1, 1))
for c in unique_clusters:
    mask = clusters == c
    score = X_no_trend[mask].T @ resid_no[mask].reshape(-1, 1)
    meat_no += score @ score.T

bread_no = np.linalg.inv(X_no_trend.T @ X_no_trend)
V_no = bread_no @ meat_no @ bread_no * (len(unique_clusters) / (len(unique_clusters) - 1))
se_no = np.sqrt(V_no[0, 0])

t_no = beta_no[0] / se_no
p_no = 2 * (1 - stats.t.cdf(abs(t_no), len(unique_clusters) - 2))

print("\nWithout pre-trend control:")
print(f"  Excess Rec × Post:  {beta_no[0]*100:+.2f}%  (SE={se_no:.4f}, t={t_no:.2f}, p={p_no:.3f})")

print("\n" + "-" * 60)
print("COMPARISON TO COMBINED (ALL 3 MODELS) ANALYSIS:")
print("-" * 60)
print("Combined (GPT-3.5 + GPT-4 + GPT-4-turbo):")
print("  Excess Rec × Post:  +2.25%  (t=1.36, p=0.175)")
print(f"\nGPT-3.5-turbo only:")
print(f"  Excess Rec × Post:  {beta_reg[0]*100:+.2f}%  (t={t_stat_excess:.2f}, p={p_excess:.3f})")
