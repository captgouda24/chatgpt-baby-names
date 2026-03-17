"""
Quick diff-in-diff analysis to check for any signal.
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Load data
data_dir = Path(__file__).parent.parent / "data"
df = pd.read_csv(data_dir / "analysis_ready.csv")

print("="*60)
print("QUICK DIFF-IN-DIFF ANALYSIS")
print("="*60)

# Basic stats
print(f"\nData: {len(df):,} observations")
print(f"Names: {df['name'].nunique():,} unique")
print(f"Treated names: {df[df['treated']==1]['name'].nunique()}")
print(f"Years: {df['year'].min()}-{df['year'].max()}")

# Simple 2x2 DiD table
print("\n" + "-"*60)
print("MEAN LOG(COUNT) BY GROUP")
print("-"*60)

did_table = df.groupby(['treated', 'post'])['log_count'].mean().unstack()
did_table.columns = ['Pre (2015-22)', 'Post (2023-24)']
did_table.index = ['Control', 'Treated']
did_table['Diff'] = did_table['Post (2023-24)'] - did_table['Pre (2015-22)']
print(did_table.round(4))

# DiD estimate
control_diff = did_table.loc['Control', 'Diff']
treated_diff = did_table.loc['Treated', 'Diff']
did_estimate = treated_diff - control_diff
print(f"\nDiD Estimate: {did_estimate:.4f}")
print(f"  (Treated change: {treated_diff:.4f}, Control change: {control_diff:.4f})")

# Convert to percent change
pct_effect = (np.exp(did_estimate) - 1) * 100
print(f"  Implied % effect: {pct_effect:.2f}%")

# Simple OLS regression
print("\n" + "-"*60)
print("OLS REGRESSION (no fixed effects)")
print("-"*60)

from scipy import stats

# Create design matrix
X = df[['treated', 'post', 'treated_x_post']].values
X = np.column_stack([np.ones(len(X)), X])  # add constant
y = df['log_count'].values

# OLS
beta = np.linalg.lstsq(X, y, rcond=None)[0]
y_hat = X @ beta
resid = y - y_hat
n, k = X.shape
se = np.sqrt(np.sum(resid**2) / (n - k) * np.diag(np.linalg.inv(X.T @ X)))
t_stats = beta / se

print(f"{'Variable':<20} {'Coef':>10} {'SE':>10} {'t-stat':>10}")
print("-"*50)
for i, name in enumerate(['Constant', 'Treated', 'Post', 'Treated x Post']):
    print(f"{name:<20} {beta[i]:>10.4f} {se[i]:>10.4f} {t_stats[i]:>10.2f}")

print(f"\nR-squared: {1 - np.sum(resid**2) / np.sum((y - y.mean())**2):.4f}")

# Fixed effects regression (within estimator)
print("\n" + "-"*60)
print("FIXED EFFECTS REGRESSION (name + year FE)")
print("-"*60)

# Demean by name and year
df['log_count_dm'] = df.groupby('name')['log_count'].transform(lambda x: x - x.mean())
df['log_count_dm'] = df.groupby('year')['log_count_dm'].transform(lambda x: x - x.mean())
df['treated_x_post_dm'] = df.groupby('name')['treated_x_post'].transform(lambda x: x - x.mean())
df['treated_x_post_dm'] = df.groupby('year')['treated_x_post_dm'].transform(lambda x: x - x.mean())

# Simple FE regression on demeaned data
x_fe = df['treated_x_post_dm'].values
y_fe = df['log_count_dm'].values
mask = ~(np.isnan(x_fe) | np.isnan(y_fe))
x_fe, y_fe = x_fe[mask], y_fe[mask]

beta_fe = np.sum(x_fe * y_fe) / np.sum(x_fe**2)
resid_fe = y_fe - beta_fe * x_fe
n_fe = len(y_fe)
n_names = df['name'].nunique()
n_years = df['year'].nunique()
dof = n_fe - n_names - n_years - 1

# Clustered SE (by name) - simplified
df_temp = df[mask].copy() if mask.sum() < len(df) else df.copy()
df_temp['resid'] = y_fe - beta_fe * df['treated_x_post_dm'].values[mask] if mask.sum() < len(df) else y_fe - beta_fe * x_fe

# Simple robust SE
se_fe = np.sqrt(np.sum(resid_fe**2) / dof / np.sum(x_fe**2))
t_fe = beta_fe / se_fe

print(f"Treated x Post coefficient: {beta_fe:.4f}")
print(f"Standard error: {se_fe:.4f}")
print(f"t-statistic: {t_fe:.2f}")
print(f"Implied % effect: {(np.exp(beta_fe) - 1) * 100:.2f}%")

# Event study - year-by-year effects for treated
print("\n" + "-"*60)
print("EVENT STUDY: Treated vs Control by Year")
print("-"*60)

yearly = df.groupby(['year', 'treated'])['log_count'].mean().unstack()
yearly.columns = ['Control', 'Treated']
yearly['Gap'] = yearly['Treated'] - yearly['Control']
yearly['Gap_normalized'] = yearly['Gap'] - yearly.loc[2022, 'Gap']  # normalize to 2022

print(yearly[['Control', 'Treated', 'Gap', 'Gap_normalized']].round(4))

print("\n" + "-"*60)
print("INTERPRETATION")
print("-"*60)
print(f"""
The DiD estimate of {did_estimate:.4f} in log points implies that ChatGPT-recommended
names {'increased' if did_estimate > 0 else 'decreased'} by {abs(pct_effect):.1f}% relative to non-recommended names
after ChatGPT launched.

Key caveats with this quick analysis:
1. Only {df[df['treated']==1]['name'].nunique()} treated names from 120 queries (need more queries)
2. No clustered standard errors (SEs likely too small)
3. Possible pre-trends - check event study above
4. Selection: ChatGPT recommends already-popular names
""")
