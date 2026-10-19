"""NASA ASRS passenger-misconduct reports: how violent were the incidents crews reported?

Usage: python asrs_analysis.py
Reads raw/asrs/ASRS_DBOnline_passenger_misconduct_2015_2026.csv (ASRS Database Online export:
Anomaly = Flight Deck / Cabin / Aircraft Event: Passenger Misconduct, Jan 2015-Jun 2026) and
raw/asrs/labels/*.tsv (Haiku codes per report, rubric raw/asrs/rubric_asrs.md). Writes
asrs_coded.csv, asrs_by_period.csv and asrs.png.

ASRS is voluntary and its volume moved with reporting channels (a 2020-21 flood of mask
reports, fewer misconduct reports after FAA zero tolerance), so counts are not a trend measure;
the share of reports that describe violence is.
"""
import glob, os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
FLAGS = ["violent", "restrained", "threat", "crew_assaulted", "mask", "alcohol", "diverted", "police"]

d = pd.read_csv(os.path.join(HERE, "raw", "asrs", "ASRS_DBOnline_passenger_misconduct_2015_2026.csv"), header=1, dtype=str)
d = d[d.ACN.fillna("").str.match(r"^\d+$")]
lab = []
for f in glob.glob(os.path.join(HERE, "raw", "asrs", "labels", "*.tsv")):
    for line in open(f, encoding="utf8"):
        p = [x.strip() for x in line.rstrip("\n").split("\t")]
        if len(p) >= 10 and p[0].isdigit():
            lab.append(dict(zip(["ACN"] + FLAGS + ["us"], p[:10])))
lab = pd.DataFrame(lab).drop_duplicates("ACN")
for c in FLAGS:
    lab[c] = pd.to_numeric(lab[c], errors="coerce")
d = d[["ACN", "Date", "Function", "Synopsis"]].merge(lab, on="ACN", how="left")
print("reports:", len(d), " uncoded:", int(d.violent.isna().sum()))
d["year"] = d.Date.str[:4].astype(int)
d.to_csv(os.path.join(HERE, "asrs_coded.csv"), index=False)


def wilson(k, n, z=1.96):
    if n == 0:
        return np.nan, np.nan
    if k == 0:
        return 0.0, 1 - (0.025) ** (1 / n)  # exact upper bound when nothing is observed
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return c - h, c + h


def period(y):
    return "2015-19" if y <= 2019 else ("2020" if y == 2020 else ("2021" if y == 2021 else ("2022-23" if y <= 2023 else "2024-26")))


rows = []
for scope, sub in [("all reports", d), ("excluding mask reports", d[d["mask"] != 1])]:
    for key, g in list(sub.groupby("year")) + list(sub.groupby(sub.year.map(period))):
        g = g.dropna(subset=["violent"])
        n, k = len(g), int(g.violent.sum())
        lo, hi = wilson(k, n)
        r = dict(scope=scope, period=str(key), reports=n, violent=k, violent_share=k / n if n else np.nan, lo=lo, hi=hi)
        for c in ["restrained", "threat", "crew_assaulted", "alcohol", "mask", "diverted", "police"]:
            r[f"{c}_share"] = g[c].mean()
        rows.append(r)
t = pd.DataFrame(rows)
t.round(3).to_csv(os.path.join(HERE, "asrs_by_period.csv"), index=False)
pd.set_option("display.width", 220)
print(t.round(2).to_string(index=False))

fig, ax = plt.subplots(2, 1, figsize=(10, 7.5), sharex=True)
yrs = list(range(2015, 2027))
cnt = d.groupby(["year", d["mask"] == 1]).size().unstack(fill_value=0).reindex(yrs, fill_value=0)
ax[0].bar(yrs, cnt.get(False, 0), color="#4c78a8", label="Not mask-related")
ax[0].bar(yrs, cnt.get(True, 0), bottom=cnt.get(False, 0), color="#9ecae9", label="Mask-related")
ax[0].set_ylabel("ASRS passenger-misconduct reports")
ax[0].set_title("NASA ASRS crew reports coded 'Passenger Misconduct' (2026 = Jan–Jun)", loc="left")
ax[0].legend(frameon=False)
for scope, col, off in [("all reports", "#c2453d", -0.12), ("excluding mask reports", "0.3", 0.12)]:
    s = t[(t.scope == scope) & t.period.str.fullmatch(r"\d{4}")].copy()
    s["y"] = s.period.astype(int)
    ax[1].errorbar(s.y + off, s.violent_share * 100, yerr=[(s.violent_share - s.lo).clip(lower=0) * 100, (s.hi - s.violent_share).clip(lower=0) * 100],
                   fmt="o", color=col, capsize=3, label=f"Violent share, {scope} (95% CI)")
ax[1].set_ylabel("% of reports describing violence")
ax[1].set_ylim(0, 100)
ax[1].axvspan(2021.5, 2026.5, color="0.93", zorder=0)
ax[1].text(2021.7, 92, "after 2021 ASRS 'passenger misconduct' reports are mostly\nbatteries, dangerous goods and cabin heat, not behaviour", fontsize=8, color="0.35", va="top")
ax[1].legend(frameon=False, fontsize=8, loc="upper left")
for a_ in ax:
    a_.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(os.path.join(HERE, "asrs.png"), dpi=130)
