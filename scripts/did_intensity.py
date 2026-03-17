"""
Diff-in-diff with continuous treatment intensity.
Treatment = how often ChatGPT recommends the name (chatgpt_freq)
"""

import pandas as pd
import numpy as np
from pathlib import Path

data_dir = Path(__file__).parent.parent / "data"
df = pd.read_csv(data_dir / "analysis_ready.csv")

print("="*60)
print("DIFF-IN-DIFF WITH CONTINUOUS TREATMENT INTENSITY")
print("="*60)

# Look at the distribution of chatgpt_freq
print("\n1. Treatment intensity distribution (among treated):")
treated_df = df[df['treated'] == 1].drop_duplicates('name')
print(f"   Min frequency: {treated_df['chatgpt_freq'].min()}")
print(f"   Max frequency: {treated_df['chatgpt_freq'].max()}")
print(f"   Mean frequency: {treated_df['chatgpt_freq'].mean():.1f}")
print(f"   Median frequency: {treated_df['chatgpt_freq'].median()}")

print("\n   Frequency distribution:")
freq_dist = treated_df['chatgpt_freq'].value_counts().sort_index()
for freq, count in freq_dist.head(15).items():
    print(f"   Freq {freq:2d}: {count:3d} names {'*' * min(count, 50)}")
if len(freq_dist) > 15:
    print(f"   ... and {len(freq_dist) - 15} more frequency levels")

# Create intensity variable (standardized)
df['intensity'] = df['chatgpt_freq'] / df['chatgpt_freq'].max()  # 0 to 1 scale
df['intensity_x_post'] = df['intensity'] * df['post']

# Also create log intensity for robustness
df['log_intensity'] = np.log1p(df['chatgpt_freq'])
df['log_intensity_x_post'] = df['log_intensity'] * df['post']

print("\n" + "="*60)
print("2. CONTINUOUS DiD: intensity x post")
print("="*60)

# OLS with intensity
from numpy.linalg import lstsq

# Model: log_count = a + b*intensity + c*post + d*intensity_x_post
X = np.column_stack([
    np.ones(len(df)),
    df['intensity'].values,
    df['post'].values,
    df['intensity_x_post'].values,
])
y = df['log_count'].values

beta, residuals, rank, s = lstsq(X, y, rcond=None)
y_hat = X @ beta
resid = y - y_hat
n, k = X.shape
mse = np.sum(resid**2) / (n - k)
var_beta = mse * np.linalg.inv(X.T @ X)
se = np.sqrt(np.diag(var_beta))

print("\nOLS (no fixed effects):")
print(f"{'Variable':<25} {'Coef':>10} {'SE':>10} {'t':>8}")
print("-"*55)
for i, name in enumerate(['Constant', 'Intensity', 'Post', 'Intensity x Post']):
    print(f"{name:<25} {beta[i]:>10.4f} {se[i]:>10.4f} {beta[i]/se[i]:>8.2f}")

print(f"\nIntensity x Post = {beta[3]:.4f}")
print(f"Interpretation: A name recommended at max frequency (intensity=1)")
print(f"  grows {(np.exp(beta[3])-1)*100:.1f}% more than unrecommended names post-ChatGPT")

# Fixed effects version
print("\n" + "-"*60)
print("Fixed Effects (name + year FE):")
print("-"*60)

# Demean by name and year
for var in ['log_count', 'intensity_x_post']:
    df[f'{var}_dm'] = df.groupby('name')[var].transform(lambda x: x - x.mean())
    df[f'{var}_dm'] = df.groupby('year')[f'{var}_dm'].transform(lambda x: x - x.mean())

x = df['intensity_x_post_dm'].values
y = df['log_count_dm'].values

beta_fe = np.sum(x * y) / np.sum(x**2)
resid_fe = y - beta_fe * x

# Clustered SE
df['resid'] = resid_fe
cluster_scores = df.groupby('name').apply(
    lambda g: (g['intensity_x_post_dm'] * g['resid']).sum(),
    include_groups=False
)
n_clusters = len(cluster_scores)
meat = np.sum(cluster_scores**2)
bread = np.sum(x**2)
se_clustered = np.sqrt((n_clusters / (n_clusters - 1)) * meat / bread**2)

print(f"Intensity x Post: {beta_fe:.4f}")
print(f"Clustered SE:     {se_clustered:.4f}")
print(f"t-statistic:      {beta_fe/se_clustered:.2f}")
print(f"\nAt max intensity: {(np.exp(beta_fe)-1)*100:.1f}% effect")

# Binned analysis - split into intensity terciles
print("\n" + "="*60)
print("3. BINNED ANALYSIS: Effect by recommendation frequency")
print("="*60)

# Among treated, create bins
treated_names = df[df['treated']==1]['name'].unique()
name_freq = df[df['treated']==1].groupby('name')['chatgpt_freq'].first()

# Create bins
bins = [0, 5, 15, 100]
labels = ['Low (1-5)', 'Med (6-15)', 'High (16+)']
name_bins = pd.cut(name_freq, bins=bins, labels=labels)

# Add bin to df
bin_map = name_bins.to_dict()
df['freq_bin'] = df['name'].map(bin_map).fillna('Control')

print("\nNames per bin:")
for bin_name in ['Control'] + labels:
    n_names = df[df['freq_bin']==bin_name]['name'].nunique()
    print(f"  {bin_name}: {n_names:,} names")

print("\nDiD by intensity bin:")
print(f"{'Bin':<15} {'Pre':>10} {'Post':>10} {'Diff':>10} {'DiD vs Ctrl':>12}")
print("-"*60)

control_pre = df[(df['freq_bin']=='Control') & (df['post']==0)]['log_count'].mean()
control_post = df[(df['freq_bin']=='Control') & (df['post']==1)]['log_count'].mean()
control_diff = control_post - control_pre
print(f"{'Control':<15} {control_pre:>10.3f} {control_post:>10.3f} {control_diff:>10.3f} {'-':>12}")

for bin_name in labels:
    pre = df[(df['freq_bin']==bin_name) & (df['post']==0)]['log_count'].mean()
    post = df[(df['freq_bin']==bin_name) & (df['post']==1)]['log_count'].mean()
    diff = post - pre
    did = diff - control_diff
    pct = (np.exp(did) - 1) * 100
    print(f"{bin_name:<15} {pre:>10.3f} {post:>10.3f} {diff:>10.3f} {did:>8.3f} ({pct:>4.1f}%)")

# Event study by intensity
print("\n" + "="*60)
print("4. EVENT STUDY BY INTENSITY BIN")
print("="*60)

print("\nGap vs Control (normalized to 2022):")
print(f"{'Year':<6}", end="")
for bin_name in labels:
    print(f"{bin_name:>15}", end="")
print()
print("-"*60)

control_by_year = df[df['freq_bin']=='Control'].groupby('year')['log_count'].mean()

for year in range(2015, 2025):
    print(f"{year:<6}", end="")
    for bin_name in labels:
        bin_mean = df[(df['freq_bin']==bin_name) & (df['year']==year)]['log_count'].mean()
        gap = bin_mean - control_by_year[year]
        gap_2022 = df[(df['freq_bin']==bin_name) & (df['year']==2022)]['log_count'].mean() - control_by_year[2022]
        gap_norm = gap - gap_2022
        print(f"{gap_norm:>15.3f}", end="")
    print()

print("\n" + "="*60)
print("INTERPRETATION")
print("="*60)
print("""
If ChatGPT causally affects naming, we expect:
1. Dose-response: Higher intensity -> larger effect
2. Timing: Effect appears post-2022, especially 2024
3. Parallel pre-trends across intensity bins

Look for: Do high-frequency recommendations show bigger 2024 bumps?
""")
