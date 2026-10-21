"""Federal criminal cases for interfering with flight crews, by fiscal year, against FAA reports.

Usage: python federal_cases.py
Reads raw/severe/ussc_2A5_2.csv (US Sentencing Commission: offenders sentenced with guideline
§2A5.2 applied) and raw/severe/trac_lead_charge_snapshots.csv (TRAC: prosecutions with lead charge
49 U.S.C. § 46504 interference with flight crew, and § 46506 assault on an aircraft, read from
Wayback snapshots; years with no snapshot are missing). Passengers per federal fiscal year (Oct-Sep)
come from raw/bts_mts.json. Writes federal_cases.csv and federal_cases.png.
"""
import json, os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, "raw")

u = pd.read_csv(os.path.join(R, "severe", "ussc_2A5_2.csv")).set_index("fiscal_year").offender_based_any_applied_2A5_2
t = pd.read_csv(os.path.join(R, "severe", "trac_lead_charge_snapshots.csv"))
t["partial"] = t.note.fillna("").str.contains("PARTIAL")
p46504 = t[t.statute == 46504].set_index("fy_label")
p46506 = t[t.statute == 46506].set_index("fy_label")

m = pd.DataFrame(json.load(open(os.path.join(R, "bts_mts.json"))))
m["date"] = pd.to_datetime(m.date)
m = m.drop_duplicates("date")  # the BTS file lists Apr 2023 twice
m["pax"] = pd.to_numeric(m.u_s_airline_traffic_total_non_seasonally_adjusted, errors="coerce")
m["fy"] = m.date.dt.year + (m.date.dt.month >= 10)
fy = m.groupby("fy").agg(pax=("pax", "sum"), months=("pax", "count"))
fy = fy[fy.months == 12].pax
f = pd.read_csv(os.path.join(R, "faa_monthly.csv"), parse_dates=["month"])
f["fy"] = f.month.dt.year + (f.month.dt.month >= 10)
faa = f.groupby("fy").agg(reports=("reports", "sum"), months=("reports", "count"))
faa = faa[faa.months == 12].reports

years = range(2011, 2026)
d = pd.DataFrame(index=years)
d.index.name = "fiscal_year"
d["ussc_2A5_2_sentenced"] = u
d["trac_46504_prosecutions"] = p46504.prosecutions_fy
d["trac_46504_partial"] = p46504.partial
d["trac_46506_prosecutions"] = p46506.prosecutions_fy
d["pax_M"] = fy / 1e6
d["faa_reports"] = faa
for c in ["ussc_2A5_2_sentenced", "trac_46504_prosecutions", "faa_reports"]:
    d[c + "_per_100M_pax"] = d[c] / d.pax_M * 100
d.round(3).to_csv(os.path.join(HERE, "federal_cases.csv"))
print(d.round(2).to_string())

fig, ax = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
ax[0].plot(d.index, d.ussc_2A5_2_sentenced, "o-", color="#c2453d", label="Sentenced under USSG §2A5.2 (interference with flight crew)")
ok = d[d.trac_46504_prosecutions.notna() & (d.trac_46504_partial != True)]
ax[0].plot(ok.index, ok.trac_46504_prosecutions, "s--", color="#4c78a8", label="Prosecuted, lead charge 49 USC §46504 (TRAC; gaps = no snapshot)")
bad = d[d.trac_46504_partial == True]
ax[0].plot(bad.index, bad.trac_46504_prosecutions, "s", mfc="white", color="#4c78a8", label="§46504 FY2025: partial/anomalous TRAC figure")
ax[0].plot(d.index, d.trac_46506_prosecutions, "^:", color="#f2a541", label="Prosecuted, lead charge 49 USC §46506 (assault on aircraft)")
ax[0].axvline(2021.4, color="0.75", lw=1)
ax[0].text(2021.5, 52, "FAA zero tolerance\n(Jan 2021); FBI\nreferral program\n(late 2021)", fontsize=8, color="0.4", va="top")
ax[0].set_ylim(0, 55)
ax[0].set_ylabel("Federal cases per fiscal year")
ax[0].set_title("Federal criminal cases for interfering with flight crews", loc="left")
ax[0].legend(frameon=False, fontsize=8, loc="upper left")

# one axis: each series per passenger, relative to its FY2018-19 average
base = lambda c: d.loc[[2018, 2019], c].mean()
ix = pd.DataFrame({k: d[k] / base(k) for k in ["ussc_2A5_2_sentenced_per_100M_pax", "trac_46504_prosecutions_per_100M_pax", "faa_reports_per_100M_pax"]})
ix.loc[d.trac_46504_partial == True, "trac_46504_prosecutions_per_100M_pax"] = float("nan")
ix.round(3).add_suffix("_index_FY18_19").to_csv(os.path.join(HERE, "federal_cases_index.csv"))
ax[1].plot(ix.index, ix.ussc_2A5_2_sentenced_per_100M_pax, "o-", color="#c2453d", label="§2A5.2 sentenced per passenger")
k = ix.trac_46504_prosecutions_per_100M_pax.dropna()
ax[1].plot(k.index, k, "s--", color="#4c78a8", label="§46504 prosecutions per passenger")
ax[1].plot(ix.index, ix.faa_reports_per_100M_pax, "d-", color="0.35", label="FAA unruly reports per passenger")
for x_, y_ in ix.faa_reports_per_100M_pax.dropna().items():
    if y_ > 3:
        ax[1].annotate(f"{y_:.1f}×", (x_, y_), textcoords="offset points", xytext=(8, -4), fontsize=8, color="0.35")
ax[1].axhline(1, color="0.8", lw=0.8)
ax[1].set_ylim(0, None)
ax[1].set_ylabel("Per passenger, relative to\nFY2018–19 average")
ax[1].legend(frameon=False, fontsize=8, loc="upper left")
ax[1].set_xticks(list(years)[::2])
ax[1].set_xlabel("Federal fiscal year (Oct–Sep)")
ax[0].spines[["top", "right"]].set_visible(False)
ax[1].spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(os.path.join(HERE, "federal_cases.png"), dpi=130)
