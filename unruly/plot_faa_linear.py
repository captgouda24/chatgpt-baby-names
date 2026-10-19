"""FAA unruly-passenger reports on a linear scale: raw monthly counts and per 10M passengers.

Usage: python plot_faa_linear.py   (reads analysis_monthly.csv, writes faa_reports_linear.png)
"""
import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
d = pd.read_csv(os.path.join(HERE, "analysis_monthly.csv"), parse_dates=["month"])
f = pd.read_csv(os.path.join(HERE, "raw", "faa_monthly.csv"), parse_dates=["month"])  # runs past the BTS passenger data

fig, ax = plt.subplots(2, 1, figsize=(11, 7.5), sharex=True)
ax[0].plot(f.month, f.reports, color="#2a5d8a", lw=2)
ax[0].set_ylabel("Reports per month")
ax[0].set_title("FAA unruly-passenger reports (linear scale)", loc="left")
ax[1].plot(d.month, d.rate, color="#2a5d8a", lw=2)
ax[1].set_ylabel("Reports per 10M passengers")
jf20 = d[(d.month >= "2020-01-01") & (d.month < "2020-03-01")]
lvl = jf20.reports.sum() / jf20.pax.sum() * 1e7
ax[1].axhline(lvl, color="0.5", ls=":", lw=1)
ax[1].text(pd.Timestamp("2017-02-01"), lvl + 4, f"Jan–Feb 2020 level ({lvl:.0f})", color="0.4", fontsize=9)
events = [("2020-05-01", "airline mask\npolicies"), ("2021-01-13", "FAA zero tolerance;\nFeb 1 federal mask mandate"),
          ("2022-04-18", "mandate\nvacated")]
for a in ax:
    a.spines[["top", "right"]].set_visible(False)
    a.set_ylim(bottom=0)
    for t, _ in events:
        a.axvline(pd.Timestamp(t), color="#c2453d", lw=0.8, alpha=0.6)
top = ax[0].get_ylim()[1]
for (t, lab), y, ha in zip(events, (0.97, 0.97, 0.55), ("right", "left", "left")):
    dx = pd.Timedelta(days=-12 if ha == "right" else 12)
    a, yy = ax[0], top * y
    if lab.startswith("FAA"):  # the top panel's peak sits right of this line
        a, yy, dx = ax[1], ax[1].get_ylim()[1] * 0.9, pd.Timedelta(days=110)
    a.text(pd.Timestamp(t) + dx, yy, lab, color="#c2453d", fontsize=8.5, va="top", ha=ha)
ax[1].annotate("Apr 2020: 23 reports on 3M passengers", xy=(pd.Timestamp("2020-04-01"), d.set_index("month").rate["2020-04-01"]),
               xytext=(pd.Timestamp("2017-06-01"), 150), fontsize=8, color="0.4", arrowprops=dict(arrowstyle="-", color="0.6"))
fig.tight_layout()
fig.savefig(os.path.join(HERE, "faa_reports_linear.png"), dpi=130)
