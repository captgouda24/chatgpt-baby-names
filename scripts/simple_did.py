import pandas as pd
import numpy as np

# Load data
gpt = pd.read_csv('C:/Users/Owner/chatgpt_names_study/data/processed/chatgpt_names_gpt_3.5_turbo.csv')
ssa = pd.read_csv('C:/Users/Owner/chatgpt_names_study/data/processed/ssa_names_panel.csv')
print(f"GPT-3.5: {len(gpt)} names")
print(f"SSA: {ssa['name'].nunique()} names")

# Pre-period popularity
pre_pop = ssa[ssa['year'] <= 2022].groupby('name')['count'].mean()

# Merge and compute excess recommendation
gpt = gpt[['name', 'frequency']].copy()
gpt = gpt.merge(pre_pop.reset_index(), on='name', how='inner')
gpt.columns = ['name', 'freq', 'pre_pop']
print(f"Matched: {len(gpt)} names")

X = np.column_stack([np.ones(len(gpt)), np.log1p(gpt['pre_pop'])])
y = np.log1p(gpt['freq'])
b = np.linalg.lstsq(X, y, rcond=None)[0]
gpt['excess'] = y - X @ b

# Pre-trends - simple loop (few seconds for 50k names)
print("Computing pre-trends...")
pre = ssa[ssa['year'] <= 2022].copy()
pre['lc'] = np.log1p(pre['count'])
trends = {}
for name, g in pre.groupby('name'):
    if len(g) >= 3:
        x = g['year'].values - 2018.5
        y = g['lc'].values
        trends[name] = np.polyfit(x, y, 1)[0]
trends = pd.DataFrame(list(trends.items()), columns=['name', 'pre_trend'])
print(f"Computed trends for {len(trends)} names")

# Merge all
ssa = ssa.merge(gpt[['name', 'excess']], on='name', how='left').fillna({'excess': 0})
ssa = ssa.merge(trends, on='name', how='left')

# Standardize and create interactions
ssa['ez'] = ssa['excess'] / ssa['excess'].std()
ssa['tz'] = (ssa['pre_trend'] - ssa['pre_trend'].mean()) / ssa['pre_trend'].std()
ssa['post'] = (ssa['year'] == 2024).astype(int)
ssa['ez_post'] = ssa['ez'] * ssa['post']
ssa['tz_post'] = ssa['tz'] * ssa['post']
ssa['lc'] = np.log1p(ssa['count'])

# Double demean for FE
for v in ['lc', 'ez_post', 'tz_post']:
    ssa[v] = ssa.groupby('name')[v].transform(lambda x: x - x.mean())
    ssa[v] = ssa.groupby('year')[v].transform(lambda x: x - x.mean())

# Regress
d = ssa.dropna()
X2 = d[['ez_post', 'tz_post']].values
y2 = d['lc'].values
b2 = np.linalg.lstsq(X2, y2, rcond=None)[0]

# Clustered SEs
resid = y2 - X2 @ b2
clusters = d['name'].values
uc = np.unique(clusters)
meat = np.zeros((2, 2))
for c in uc:
    m = clusters == c
    s = X2[m].T @ resid[m].reshape(-1, 1)
    meat += s @ s.T
bread = np.linalg.inv(X2.T @ X2)
V = bread @ meat @ bread * len(uc) / (len(uc) - 1)
se = np.sqrt(np.diag(V))

print("\n" + "="*50)
print("RESULTS: GPT-3.5-turbo only (free default model)")
print("="*50)
print(f"Excess Rec x Post: {b2[0]*100:+.2f}%  (t={b2[0]/se[0]:.2f})")
print(f"Pre-Trend x Post:  {b2[1]*100:+.2f}%  (t={b2[1]/se[1]:.2f})")
print("\nComparison - Combined (all 3 models): +2.25% (t=1.36)")
