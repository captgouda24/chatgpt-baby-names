"""Crimes recorded by Chicago police on aircraft at O'Hare and Midway, per passenger.

Usage: python chicago_aircraft.py
Reads raw/chicago/cpd_aircraft_crimes_2010_2026.csv (Chicago Data Portal, Crimes - 2001 to Present,
location_description = AIRCRAFT; the older catch-all AIRPORT/AIRCRAFT code, mostly narcotics
and airport-wide crime and retired after 2023, is excluded) and raw/chicago/bts_t100_ord_mdw_departing_pax.csv
(BTS T-100 segment summary, passengers departing ORD + MDW, Jan 2014 on). Writes chicago_aircraft_annual.csv
and chicago_aircraft.png.

A police crime code is a standard that FAA enforcement policy does not change, unlike FAA
unruly-passenger reports.
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
VIOLENT = ["BATTERY", "ASSAULT", "SEX OFFENSE", "CRIM SEXUAL ASSAULT", "CRIMINAL SEXUAL ASSAULT", "HOMICIDE", "ROBBERY"]

c = pd.read_csv(os.path.join(HERE, "raw", "chicago", "cpd_aircraft_crimes_2010_2026.csv"), parse_dates=["date"])
c = c[c.location_description == "AIRCRAFT"].copy()
c["violent"] = c.primary_type.isin(VIOLENT)
c["month"] = c.date.dt.to_period("M")
p = pd.read_csv(os.path.join(HERE, "raw", "chicago", "bts_t100_ord_mdw_departing_pax.csv"), parse_dates=["reporting_month"])
pax = p.groupby(p.reporting_month.dt.to_period("M")).total_passengers.sum()
last_crime = c.date.max()

yrs = range(2010, last_crime.year + 1)
rows = []
for y in yrs:
    cy = c[c.date.dt.year == y]
    pm = pax[pax.index.year == y]
    # rate only over months that have passenger data
    cm = cy[cy.month.isin(pm.index)]
    rows.append(dict(year=y, violent=int(cy.violent.sum()), other=int((~cy.violent).sum()),
                     pax_months=len(pm), pax_departing_M=pm.sum() / 1e6,
                     violent_in_pax_months=int(cm.violent.sum())))
a = pd.DataFrame(rows).set_index("year")
a["violent_per_10M_pax"] = a.violent_in_pax_months / (a.pax_departing_M / 10)
lo, hi = [], []
for k, n in zip(a.violent_in_pax_months, a.pax_departing_M / 10):
    if n == 0:
        lo.append(np.nan); hi.append(np.nan); continue
    # exact Poisson interval via chi-square quantiles (Garwood)
    from scipy.stats import chi2
    lo.append(chi2.ppf(0.025, 2 * k) / 2 / n if k > 0 else 0.0)
    hi.append(chi2.ppf(0.975, 2 * k + 2) / 2 / n)
a["rate_lo"], a["rate_hi"] = lo, hi

f = pd.read_csv(os.path.join(HERE, "analysis_monthly.csv"), parse_dates=["month"])
f = f.groupby(f.month.dt.year).agg(reports=("reports", "sum"), pax=("pax", "sum"))
a["faa_reports_per_10M_pax_us"] = f.reports / f.pax * 1e7
a.round(3).to_csv(os.path.join(HERE, "chicago_aircraft_annual.csv"))
print(a.round(2).to_string())

base = a.loc[2015:2019]
b_rate = base.violent_in_pax_months.sum() / (base.pax_departing_M.sum() / 10)
b_faa = (f.loc[2015:2019].reports.sum() if 2015 in f.index else np.nan)
print("2015-19 violent per 10M departing pax:", round(b_rate, 2))

fig, ax = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
part = last_crime.year
ax[0].bar(a.index, a.other, color="#9ecae9", label="Other crimes on aircraft (mostly theft, disorderly conduct)")
ax[0].bar(a.index, a.violent, bottom=a.other, color="#c2453d", label="Violent: battery, assault, sexual offenses")
ax[0].text(part, (a.loc[part, "violent"] + a.loc[part, "other"]) + 3, f"to {last_crime:%b %d}", ha="center", fontsize=8, color="0.4")
ax[0].set_ylabel("Crimes recorded on aircraft")
ax[0].set_title("Chicago police: crimes on aircraft at O'Hare and Midway (location code AIRCRAFT)", loc="left")
ax[0].legend(frameon=False, fontsize=8, loc="upper right")
ax[0].set_ylim(0, (a.violent + a.other).max() * 1.25)

r = a[a.pax_months > 0]
ax[1].errorbar(r.index, r.violent_per_10M_pax, yerr=[r.violent_per_10M_pax - r.rate_lo, r.rate_hi - r.violent_per_10M_pax],
               fmt="o-", color="#c2453d", capsize=3, label="Violent crimes on aircraft per 10M departing ORD+MDW passengers (95% CI)")
ax[1].axhline(b_rate, color="#c2453d", lw=0.8, ls=":")
ax[1].text(2014.1, b_rate + 0.2, "2015–19 average", fontsize=8, color="#c2453d")
ax2 = ax[1].twinx()
ax2.plot(r.index, r.faa_reports_per_10M_pax_us, "s--", color="0.35", label="FAA unruly reports per 10M US passengers (right axis)")
ax2.set_ylim(0, None)
ax2.set_ylabel("FAA reports per 10M US passengers", color="0.35")
ax[1].set_ylim(0, None)
ax[1].set_ylabel("Violent crimes on aircraft\nper 10M departing passengers")
if r.pax_months.iloc[-1] < 12:
    ax[1].text(r.index[-1], r.rate_hi.iloc[-1], f"Jan–{pd.Timestamp(year=2000, month=int(r.pax_months.iloc[-1]), day=1):%b}", ha="center", va="bottom", fontsize=8, color="0.4")
h1, l1 = ax[1].get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax[1].legend(h1 + h2, l1 + l2, frameon=False, fontsize=8, loc="upper left")
ax[1].set_xticks(list(yrs)[::2])
for a_ in [ax[0], ax[1]]:
    a_.spines[["top"]].set_visible(False)
ax[0].spines[["right"]].set_visible(False)
fig.tight_layout()
fig.savefig(os.path.join(HERE, "chicago_aircraft.png"), dpi=130)
