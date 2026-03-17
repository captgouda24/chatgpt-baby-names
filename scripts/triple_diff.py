"""
Triple difference analysis:
(ChatGPT recommended vs not) x (Post-2022 vs Pre) x (Tech states vs Non-tech)

If ChatGPT causally affects naming, effect should be strongest in tech states
where adoption was highest/earliest.
"""

import pandas as pd
import numpy as np
from pathlib import Path

data_dir = Path(__file__).parent.parent / "data"

print("="*60)
print("TRIPLE DIFFERENCE ANALYSIS")
print("="*60)

# Load state panel
print("\n1. Loading data...")
state_df = pd.read_csv(data_dir / "processed" / "ssa_names_state_panel.csv")
print(f"   State panel: {len(state_df):,} records")

# Load ChatGPT names (use whichever file exists)
chatgpt_file = data_dir / "processed" / "chatgpt_names.csv"
if not chatgpt_file.exists():
    chatgpt_file = data_dir / "processed" / "chatgpt_names_gpt_3.5_turbo.csv"

chatgpt_df = pd.read_csv(chatgpt_file)
print(f"   ChatGPT names: {len(chatgpt_df)} names")

# Merge
print("\n2. Creating treatment indicators...")
chatgpt_names = set(chatgpt_df['name'].str.lower())
state_df['name_lower'] = state_df['name'].str.lower()
state_df['treated'] = state_df['name_lower'].isin(chatgpt_names).astype(int)

# Add frequency
freq_map = chatgpt_df.set_index(chatgpt_df['name'].str.lower())['frequency'].to_dict()
state_df['chatgpt_freq'] = state_df['name_lower'].map(freq_map).fillna(0).astype(int)

# Post indicator
state_df['post'] = (state_df['year'] >= 2023).astype(int)

# Log count
state_df['log_count'] = np.log(state_df['count'].replace(0, 1))

# Interactions
state_df['treated_x_post'] = state_df['treated'] * state_df['post']
state_df['treated_x_tech'] = state_df['treated'] * state_df['tech_state']
state_df['post_x_tech'] = state_df['post'] * state_df['tech_state']
state_df['triple'] = state_df['treated'] * state_df['post'] * state_df['tech_state']

print(f"   Treated names: {state_df[state_df['treated']==1]['name'].nunique()}")
print(f"   Tech states: {state_df[state_df['tech_state']==1]['state'].nunique()}")

# 2x2x2 Table
print("\n" + "="*60)
print("3. TRIPLE DIFF TABLE: Mean log(count)")
print("="*60)

table = state_df.groupby(['treated', 'post', 'tech_state'])['log_count'].mean().unstack([1, 2])
table.columns = ['Pre/Non-Tech', 'Pre/Tech', 'Post/Non-Tech', 'Post/Tech']
table.index = ['Control', 'Treated']
print("\n", table.round(3))

# Calculate DiD within each state type
print("\n" + "-"*60)
print("DiD by state type:")
print("-"*60)

# Non-tech states DiD
nontech_did = (
    (table.loc['Treated', 'Post/Non-Tech'] - table.loc['Treated', 'Pre/Non-Tech']) -
    (table.loc['Control', 'Post/Non-Tech'] - table.loc['Control', 'Pre/Non-Tech'])
)
print(f"Non-Tech states DiD: {nontech_did:.4f} ({(np.exp(nontech_did)-1)*100:.2f}%)")

# Tech states DiD
tech_did = (
    (table.loc['Treated', 'Post/Tech'] - table.loc['Treated', 'Pre/Tech']) -
    (table.loc['Control', 'Post/Tech'] - table.loc['Control', 'Pre/Tech'])
)
print(f"Tech states DiD:     {tech_did:.4f} ({(np.exp(tech_did)-1)*100:.2f}%)")

# Triple diff
triple_diff = tech_did - nontech_did
print(f"\nTriple Diff (Tech - Non-Tech): {triple_diff:.4f} ({(np.exp(triple_diff)-1)*100:.2f}%)")

# Regression
print("\n" + "="*60)
print("4. TRIPLE DIFF REGRESSION")
print("="*60)

# OLS with all interactions
X_vars = ['treated', 'post', 'tech_state', 'treated_x_post', 'treated_x_tech', 'post_x_tech', 'triple']
X = np.column_stack([np.ones(len(state_df))] + [state_df[v].values for v in X_vars])
y = state_df['log_count'].values

beta = np.linalg.lstsq(X, y, rcond=None)[0]
y_hat = X @ beta
resid = y - y_hat
n, k = X.shape
mse = np.sum(resid**2) / (n - k)
se = np.sqrt(mse * np.diag(np.linalg.inv(X.T @ X)))

print(f"\n{'Variable':<20} {'Coef':>10} {'SE':>10} {'t':>8}")
print("-"*50)
for i, name in enumerate(['Constant'] + X_vars):
    print(f"{name:<20} {beta[i]:>10.4f} {se[i]:>10.4f} {beta[i]/se[i]:>8.2f}")

print(f"\nKey coefficient: 'triple' = {beta[-1]:.4f}")
print(f"Interpretation: ChatGPT effect is {(np.exp(beta[-1])-1)*100:.1f}% LARGER in tech states")

# Event study by state type
print("\n" + "="*60)
print("5. EVENT STUDY BY STATE TYPE")
print("="*60)

print("\nGap (Treated - Control), normalized to 2022:")
print(f"{'Year':<6} {'Non-Tech':>12} {'Tech':>12} {'Difference':>12}")
print("-"*45)

for year in range(2015, 2025):
    gaps = {}
    for tech in [0, 1]:
        treated_mean = state_df[(state_df['treated']==1) & (state_df['year']==year) & (state_df['tech_state']==tech)]['log_count'].mean()
        control_mean = state_df[(state_df['treated']==0) & (state_df['year']==year) & (state_df['tech_state']==tech)]['log_count'].mean()
        gaps[tech] = treated_mean - control_mean

    # Normalize to 2022
    if year == 2022:
        baseline = gaps.copy()
        gaps_norm = {0: 0, 1: 0}
    else:
        gaps_norm = {k: gaps[k] - baseline[k] for k in gaps}

    diff = gaps_norm[1] - gaps_norm[0]
    print(f"{year:<6} {gaps_norm[0]:>12.3f} {gaps_norm[1]:>12.3f} {diff:>12.3f}")

print("\n" + "="*60)
print("INTERPRETATION")
print("="*60)
print(f"""
If the triple diff coefficient is positive and significant:
- ChatGPT effect is LARGER in tech states (where adoption was higher)
- Supports causal interpretation: more ChatGPT usage -> more effect

Triple diff estimate: {beta[-1]:.4f} ({(np.exp(beta[-1])-1)*100:.1f}% larger effect in tech states)

Look for:
1. Tech states showing bigger post-2022 divergence than non-tech
2. Effect concentrated in 2024 (gestation lag from ChatGPT use)
""")
