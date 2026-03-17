import pandas as pd
import numpy as np
from scipy import stats

ssa = pd.read_csv('data/processed/ssa_names_panel.csv')
chatgpt = pd.read_csv('data/processed/chatgpt_names_gpt_3.5_turbo.csv')

pre_pop = ssa[ssa['year'] <= 2022].groupby('name')['count'].mean().reset_index()
pre_pop.columns = ['name', 'pre_mean_count']
pre_pop['pre_mean_log'] = np.log(pre_pop['pre_mean_count'] + 1)

chatgpt['name_lower'] = chatgpt['name'].str.lower()
pre_pop['name_lower'] = pre_pop['name'].str.lower()
merged = pre_pop.merge(chatgpt[['name_lower', 'frequency']].rename(columns={'frequency': 'chatgpt_freq'}), on='name_lower', how='left')
merged['chatgpt_freq'] = merged['chatgpt_freq'].fillna(0)

rec = merged[merged['chatgpt_freq'] > 0].copy()
X = np.column_stack([np.ones(len(rec)), rec['pre_mean_log'].values])
y = np.log1p(rec['chatgpt_freq'].values)
beta = np.linalg.lstsq(X, y, rcond=None)[0]
rec['excess'] = y - (beta[0] + beta[1] * rec['pre_mean_log'])

excess_map = rec.set_index('name_lower')['excess'].to_dict()
ssa['name_lower'] = ssa['name'].str.lower()
ssa['excess'] = ssa['name_lower'].map(excess_map).fillna(0)
ssa['post'] = (ssa['year'] >= 2023).astype(int)
ssa['excess_x_post'] = ssa['excess'] * ssa['post']
ssa['log_count'] = np.log(ssa['count'].replace(0, 1))

print("="*50)
print("EXCESS RECOMMENDATION x POST")
print("="*50)

# FE
for v in ['log_count', 'excess_x_post']:
    ssa[v+'_dm'] = ssa.groupby('name')[v].transform(lambda x: x - x.mean())
    ssa[v+'_dm'] = ssa.groupby('year')[v+'_dm'].transform(lambda x: x - x.mean())

x = ssa['excess_x_post_dm'].values
y = ssa['log_count_dm'].values
b_fe = np.sum(x*y) / np.sum(x**2)

ssa['resid'] = y - b_fe * x
scores = ssa.groupby('name').apply(lambda g: (g['excess_x_post_dm'] * g['resid']).sum(), include_groups=False)
n_c = len(scores)
se_cl = np.sqrt((n_c/(n_c-1)) * np.sum(scores**2) / np.sum(x**2)**2)
t_stat = b_fe / se_cl
p_val = 2 * (1 - stats.t.cdf(abs(t_stat), n_c - 1))

print(f"Coefficient:  {b_fe:.4f}")
print(f"Std Error:    {se_cl:.4f}")
print(f"t-statistic:  {t_stat:.2f}")
print(f"p-value:      {p_val:.3f}")
print()
print(f"Significant at 5%? {'YES' if p_val < 0.05 else 'NO'}")
print(f"Significant at 10%? {'YES' if p_val < 0.10 else 'NO'}")
