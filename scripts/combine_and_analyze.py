"""
Combine GPT-3.5 and GPT-4 data using multiple weighting schemes,
then run DiD analysis on each.
"""

import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path
from collections import Counter
import json

data_dir = Path(__file__).parent.parent / "data"

print("="*60)
print("COMBINING MODELS & RUNNING ANALYSIS")
print("="*60)

# Load raw responses
def load_responses(filepath):
    names = Counter()
    with open(filepath) as f:
        for line in f:
            rec = json.loads(line)
            for name in rec['extracted_names']:
                names[name] += 1
    return names

gpt35_file = data_dir / "raw" / "chatgpt_responses_gpt_3.5_turbo.jsonl"
gpt4_file = data_dir / "raw" / "chatgpt_responses_gpt_4.jsonl"

gpt35_names = load_responses(gpt35_file)
gpt4_names = load_responses(gpt4_file) if gpt4_file.exists() else Counter()

print(f"\nGPT-3.5-turbo: {len(gpt35_names)} unique names, {sum(gpt35_names.values())} mentions")
print(f"GPT-4:         {len(gpt4_names)} unique names, {sum(gpt4_names.values())} mentions")

# Create different weighting schemes
print("\n" + "-"*60)
print("Creating combined datasets...")
print("-"*60)

all_names = set(gpt35_names.keys()) | set(gpt4_names.keys())
print(f"Total unique names across models: {len(all_names)}")

combined = pd.DataFrame({'name': list(all_names)})
combined['name_lower'] = combined['name'].str.lower()

# Method 1: Simple pool (raw counts added)
combined['freq_pool'] = combined['name'].map(lambda n: gpt35_names.get(n, 0) + gpt4_names.get(n, 0))

# Method 2: Equal model weight (normalize within model, then average)
gpt35_total = sum(gpt35_names.values())
gpt4_total = sum(gpt4_names.values()) if gpt4_names else 1
combined['freq_gpt35_norm'] = combined['name'].map(lambda n: gpt35_names.get(n, 0) / gpt35_total)
combined['freq_gpt4_norm'] = combined['name'].map(lambda n: gpt4_names.get(n, 0) / gpt4_total)
combined['freq_equal_weight'] = (combined['freq_gpt35_norm'] + combined['freq_gpt4_norm']) / 2

# Method 3: Union (binary)
combined['treated_union'] = ((combined['name'].map(lambda n: gpt35_names.get(n, 0)) > 0) |
                              (combined['name'].map(lambda n: gpt4_names.get(n, 0)) > 0)).astype(int)

# Method 4: GPT-3.5 only
combined['freq_gpt35_only'] = combined['name'].map(lambda n: gpt35_names.get(n, 0))

print(f"  Pool: {(combined['freq_pool'] > 0).sum()} names")
print(f"  Equal weight: {(combined['freq_equal_weight'] > 0).sum()} names")
print(f"  Union: {combined['treated_union'].sum()} names")
print(f"  GPT-3.5 only: {(combined['freq_gpt35_only'] > 0).sum()} names")

# Save combined
combined.to_csv(data_dir / "processed" / "chatgpt_names_combined.csv", index=False)

# Load SSA data
ssa = pd.read_csv(data_dir / "processed" / "ssa_names_panel.csv")
ssa['name_lower'] = ssa['name'].str.lower()
ssa['log_count'] = np.log(ssa['count'].replace(0, 1))
ssa['post_2024'] = (ssa['year'] == 2024).astype(int)

# Pre-period popularity for excess calculation
pre_pop = ssa[ssa['year'] <= 2022].groupby('name_lower')['count'].mean().reset_index()
pre_pop.columns = ['name_lower', 'pre_mean_count']
pre_pop['pre_mean_log'] = np.log(pre_pop['pre_mean_count'] + 1)

def run_did_analysis(ssa_df, combined_df, freq_col, method_name):
    """Run DiD with excess recommendation for a given frequency column."""

    # Merge frequency
    df = ssa_df.copy()
    freq_map = combined_df.set_index('name_lower')[freq_col].to_dict()
    df['chatgpt_freq'] = df['name_lower'].map(freq_map).fillna(0)

    # Compute excess recommendation (only among recommended names)
    rec_names = combined_df[combined_df[freq_col] > 0][['name_lower', freq_col]].copy()
    rec_names = rec_names.merge(pre_pop, on='name_lower', how='left')
    rec_names = rec_names.dropna()

    if len(rec_names) < 10:
        return None

    # Regress log freq on log pre-popularity
    X = np.column_stack([np.ones(len(rec_names)), rec_names['pre_mean_log'].values])
    y = np.log1p(rec_names[freq_col].values)
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    rec_names['excess'] = y - (beta[0] + beta[1] * rec_names['pre_mean_log'])
    excess_std = rec_names['excess'].std()

    # Map excess back
    excess_map = rec_names.set_index('name_lower')['excess'].to_dict()
    df['excess'] = df['name_lower'].map(excess_map).fillna(0)
    df['excess_z'] = df['excess'] / excess_std if excess_std > 0 else 0
    df['excess_z_x_post'] = df['excess_z'] * df['post_2024']

    # FE regression
    for v in ['log_count', 'excess_z_x_post']:
        df[v+'_dm'] = df.groupby('name')[v].transform(lambda x: x - x.mean())
        df[v+'_dm'] = df.groupby('year')[v+'_dm'].transform(lambda x: x - x.mean())

    x = df['excess_z_x_post_dm'].values
    y = df['log_count_dm'].values

    if np.sum(x**2) == 0:
        return None

    b_fe = np.sum(x*y) / np.sum(x**2)

    df['resid'] = y - b_fe * x
    scores = df.groupby('name').apply(lambda g: (g['excess_z_x_post_dm'] * g['resid']).sum(), include_groups=False)
    n_c = len(scores)
    se_cl = np.sqrt((n_c/(n_c-1)) * np.sum(scores**2) / np.sum(x**2)**2)
    t_stat = b_fe / se_cl if se_cl > 0 else 0
    p_val = 2 * (1 - stats.t.cdf(abs(t_stat), n_c - 1))

    return {
        'method': method_name,
        'n_treated_names': (df.groupby('name')['excess'].first() != 0).sum(),
        'coef': b_fe,
        'se': se_cl,
        't_stat': t_stat,
        'p_value': p_val
    }

# Run all methods
print("\n" + "="*60)
print("DIFF-IN-DIFF RESULTS (2024 vs 2015-2022)")
print("="*60)

methods = [
    ('freq_pool', '1. Simple Pool'),
    ('freq_equal_weight', '2. Equal Model Weight'),
    ('freq_gpt35_only', '3. GPT-3.5 Only'),
]

results = []
for freq_col, method_name in methods:
    res = run_did_analysis(ssa, combined, freq_col, method_name)
    if res:
        results.append(res)

# Also run binary union
ssa_union = ssa.copy()
union_map = combined.set_index('name_lower')['treated_union'].to_dict()
ssa_union['treated'] = ssa_union['name_lower'].map(union_map).fillna(0)
ssa_union['treated_x_post'] = ssa_union['treated'] * ssa_union['post_2024']

for v in ['log_count', 'treated_x_post']:
    ssa_union[v+'_dm'] = ssa_union.groupby('name')[v].transform(lambda x: x - x.mean())
    ssa_union[v+'_dm'] = ssa_union.groupby('year')[v+'_dm'].transform(lambda x: x - x.mean())

x = ssa_union['treated_x_post_dm'].values
y = ssa_union['log_count_dm'].values
b_fe = np.sum(x*y) / np.sum(x**2)
ssa_union['resid'] = y - b_fe * x
scores = ssa_union.groupby('name').apply(lambda g: (g['treated_x_post_dm'] * g['resid']).sum(), include_groups=False)
n_c = len(scores)
se_cl = np.sqrt((n_c/(n_c-1)) * np.sum(scores**2) / np.sum(x**2)**2)
t_stat = b_fe / se_cl
p_val = 2 * (1 - stats.t.cdf(abs(t_stat), n_c - 1))

results.append({
    'method': '4. Union (Binary)',
    'n_treated_names': int(ssa_union.groupby('name')['treated'].first().sum()),
    'coef': b_fe,
    'se': se_cl,
    't_stat': t_stat,
    'p_value': p_val
})

# Print results
print(f"\n{'Method':<25} {'N Treated':>10} {'Coef':>10} {'SE':>10} {'t':>8} {'p':>8}")
print("-"*75)
for r in results:
    sig = '*' if r['p_value'] < 0.10 else ''
    sig = '**' if r['p_value'] < 0.05 else sig
    sig = '***' if r['p_value'] < 0.01 else sig
    print(f"{r['method']:<25} {r['n_treated_names']:>10} {r['coef']:>10.4f} {r['se']:>10.4f} {r['t_stat']:>8.2f} {r['p_value']:>7.3f} {sig}")

print("\n* p<0.10, ** p<0.05, *** p<0.01")
print("\nNote: Methods 1-3 use continuous 'excess recommendation' (standardized).")
print("      Method 4 uses binary treatment (any recommendation).")
