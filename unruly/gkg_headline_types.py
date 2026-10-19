"""Coverage by story type from GKG headlines (Oct 2019-Sep 2026), against reports and severe cases.

Usage: python gkg_headline_types.py LABELDIR
LABELDIR/*.tsv hold id<TAB>kind<TAB>mask from the Haiku labelers. The main measure of
a type is distinct US stories (headline minus outlet suffix) with that label per 1M GKG articles with a page title.
vol_* counts syndicated copies too; it is dominated by iHeart radio-station reposts
(one story can appear on 100+ station sites), so it is reported but not charted. Writes gkg_headlines_classified.csv,
gkg_types_quarterly.csv, gkg_types_annual.csv and gkg_types.png.
"""
import glob, os, sys
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
KINDS = ["aggregate_or_policy", "incident_nonviolent", "incident_violent"]
NAMES = {"aggregate_or_policy": "Statistics / policy", "incident_nonviolent": "Non-violent incident",
         "incident_violent": "Violent incident"}
COLS = {"aggregate_or_policy": "#4c78a8", "incident_nonviolent": "#f2a541", "incident_violent": "#c2453d"}

lab = pd.concat([pd.read_csv(f, sep="\t", header=None, names=["id", "kind", "mask"])
                 for f in glob.glob(os.path.join(sys.argv[1], "*.tsv"))]).drop_duplicates("id")
d = pd.read_csv(os.path.join(HERE, "gkg_headlines_unique.csv")).merge(lab, on="id", how="left")
print("unlabeled:", d.kind.isna().sum())
d.drop(columns="key").to_csv(os.path.join(HERE, "gkg_headlines_classified.csv"), index=False)
d["q"] = pd.to_datetime(d.quarter.astype(str)).dt.to_period("Q")

cnt = pd.read_csv(os.path.join(HERE, "gkg_monthly_counts.csv"))
cnt["q"] = pd.to_datetime(cnt.month.astype(str), format="%Y%m").dt.to_period("Q")
p = pd.read_csv(os.path.join(HERE, "analysis_monthly.csv"), parse_dates=["month"])
p["q"] = p.month.dt.to_period("Q")
pq = p.groupby("q").agg(reports=("reports", "sum"), pax=("pax", "sum"), pm=("pax", "count"))
pq.loc[pq.pm < 3, "pax"] = float("nan")

g = cnt.groupby("q").gkg_titled_articles.sum().to_frame("den")
g = g.join(pd.crosstab(d.q, d.kind, values=d.n_copies, aggfunc="sum").reindex(columns=KINDS).fillna(0))
ds = d.drop_duplicates(["q", "story"])  # one row per story per quarter (station-suffix variants collapsed)
g = g.join(pd.crosstab(ds.q, ds.kind).reindex(columns=KINDS).fillna(0).add_prefix("uniq_"))
g["mask_share"] = ds[ds.kind != "other"].groupby("q")["mask"].mean()
g = g.join(pq[["reports", "pax"]])
for k in KINDS:
    g[f"vol_{k}"] = g[k] / g.den * 1e6
    g[f"uniq_{k}_per_M"] = g[f"uniq_{k}"] / g.den * 1e6
g.round(4).to_csv(os.path.join(HERE, "gkg_types_quarterly.csv"))

# annual (Oct 2019-Mar 2020 = pre-COVID base; 2026 = Jan-Sep; pax-based rates use quarters with full BTS data)
g["per"] = [("base" if q < pd.Period("2020Q2") else str(q.year)) for q in g.index]
a = g.groupby("per")[["den"] + KINDS + [f"uniq_{k}" for k in KINDS]].sum()
g["pax_months"] = g.pax.notna() * 3
full = g.dropna(subset=["pax"]).groupby("per")[["den", "reports", "pax", "pax_months"] + KINDS + [f"uniq_{k}" for k in KINDS]].sum()
full["pax_per_month"] = full.pax / full.pax_months  # periods differ in length; use average monthly passengers
for k in KINDS:
    a[f"vol_{k}"] = a[k] / a.den * 1e6
    a[f"uniq_{k}_per_M"] = a[f"uniq_{k}"] / a.den * 1e6
    a[f"share_{k}"] = a[f"uniq_{k}"] / a[[f"uniq_{j}" for j in KINDS]].sum(axis=1)
    a[f"uniq_{k}_per_M_per_100M_pax"] = (full[f"uniq_{k}"] / full.den * 1e6) / full.pax_per_month * 1e8
a["faa_reports_per_10M_pax"] = full.reports / full.pax * 1e7
a = a.reindex(["base"] + [str(y) for y in range(2020, 2027)])
a.round(3).to_csv(os.path.join(HERE, "gkg_types_annual.csv"))
pd.set_option("display.width", 220)
show = ([f"uniq_{k}" for k in KINDS] + [f"share_{k}" for k in KINDS] + [f"uniq_{k}_per_M" for k in KINDS]
        + [f"uniq_{k}_per_M_per_100M_pax" for k in KINDS] + ["faa_reports_per_10M_pax"] + [f"vol_{k}" for k in KINDS])
print(a[show].round(2).T.to_string())

# chart
fig, ax = plt.subplots(2, 1, figsize=(10, 8))
x = g.index.to_timestamp()
ax[0].stackplot(x, *[g[f"uniq_{k}_per_M"] for k in KINDS], colors=[COLS[k] for k in KINDS],
                labels=[NAMES[k] for k in KINDS], step="post")
ax[0].axvspan(pd.Timestamp("2021-02-01"), pd.Timestamp("2022-04-18"), color="0.92", zorder=0)
top = ax[0].get_ylim()[1] * 1.1
ax[0].set_ylim(0, top)
ax[0].text(pd.Timestamp("2021-02-15"), top * 0.96, "federal mask mandate", fontsize=8, color="0.4", va="top")
ax[0].set_ylabel("Distinct US headlines\nper 1M monitored articles")
ax[0].set_title('Headlines with "unruly/disruptive passenger" or "air rage", by story type (GDELT GKG, Haiku-labeled)')
ax[0].legend(loc="upper right", frameon=False)

ussc = pd.read_csv(os.path.join(HERE, "raw", "severe", "ussc_2A5_2.csv")).set_index("fiscal_year").offender_based_any_applied_2A5_2
yrs = [str(y) for y in range(2020, 2027)]
xs = range(len(yrs) + 1)
lab_x = ["Oct19–\nMar20", "Apr–Dec\n2020"] + yrs[1:-1] + ["2026\nJan–Jun"]
series = {f"uniq_{k}_per_M_per_100M_pax": (NAMES[k] + " headlines / passenger", COLS[k]) for k in KINDS}
series["faa_reports_per_10M_pax"] = ("FAA unruly reports / passenger", "0.2")
for c, (nm, col) in series.items():
    v = a[c] / a.loc["base", c]
    ax[1].plot(xs, v.values, marker="o", color=col, label=nm)
us = [ussc.get(int(y), float("nan")) / ussc.loc[[2019, 2020]].mean() for y in yrs]
ax[1].plot(xs, [1.0] + us, marker="s", ls="--", color="0.5", label="Federal §2A5.2 sentencings (FY, base FY19–20)")
ax[1].axhline(1, color="0.8", lw=0.8)
ax[1].set_yscale("log")
ax[1].set_xticks(list(xs), lab_x)
ax[1].set_ylabel("Index, Oct 2019–Mar 2020 = 1 (log)")
ax[1].legend(frameon=False, fontsize=8, loc="upper right")
for a_ in ax:
    a_.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(os.path.join(HERE, "gkg_types.png"), dpi=130)
