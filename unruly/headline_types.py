"""Coverage by story type: Haiku headline labels x GDELT coverage volume.

Usage: python headline_types.py LABELDIR
LABELDIR/*.tsv hold id<TAB>kind<TAB>mask from the Haiku labelers (rubric in
FINDINGS.md). Joins them to headlines_unique.csv, writes headlines_classified.csv,
headline_types_quarterly.csv and headline_types.png.
"""
import glob, os, sys
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
KINDS = ["aggregate_or_policy", "incident_nonviolent", "incident_violent"]

lab = pd.concat([pd.read_csv(f, sep="\t", header=None, names=["id", "kind", "mask"])
                 for f in glob.glob(os.path.join(sys.argv[1], "*.tsv"))]).drop_duplicates("id")
d = pd.read_csv(os.path.join(HERE, "headlines_unique.csv")).merge(lab, on="id", how="inner")
d.drop(columns="key").to_csv(os.path.join(HERE, "headlines_classified.csv"), index=False)

d["q"] = pd.to_datetime(d.quarter.astype(str)).dt.to_period("Q")
rel = d[d.kind != "other"]
sh = pd.crosstab(rel.q, rel.kind, normalize="index").reindex(columns=KINDS, fill_value=0)
sh["n_unique"] = rel.groupby("q").size()
sh["mask_share"] = rel.groupby("q")["mask"].mean()

m = pd.read_csv(os.path.join(HERE, "news_vs_reports_monthly.csv"), parse_dates=["month"])
p = pd.read_csv(os.path.join(HERE, "analysis_monthly.csv"), parse_dates=["month"])[["month", "pax"]]
m = m.merge(p, on="month", how="left")
m["q"] = m.month.dt.to_period("Q")
g = m.groupby("q").agg(cov_per_M=("unruly_per_M_articles", "mean"), reports=("reports", "sum"),
                       pax=("pax", "sum"), pax_months=("pax", "count"))
g.loc[g.pax_months < 3, "pax"] = float("nan")
out = sh.join(g, how="left")
for k in KINDS:
    out[f"vol_{k}"] = out[k] * out.cov_per_M                       # articles per 1M monitored
    out[f"vol_{k}_per_100M_pax"] = out[f"vol_{k}"] / out.pax * 1e8  # same, per passenger flown
out.round(4).to_csv(os.path.join(HERE, "headline_types_quarterly.csv"))

pd.set_option("display.width", 200)
print(out[KINDS + ["n_unique", "mask_share", "cov_per_M"] + [f"vol_{k}" for k in KINDS]].round(2).to_string())

# annual summary
a = out.copy()
a["yr"] = a.index.year
yr = a.groupby("yr")[[f"vol_{k}" for k in KINDS] + ["n_unique"]].mean().round(2)
yr = yr.join(a.groupby("yr")[[f"vol_{k}_per_100M_pax" for k in KINDS]].mean().round(2))
print(yr.to_string())

fig, ax = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
x = out.index.to_timestamp()
cols = {"aggregate_or_policy": "#4c78a8", "incident_nonviolent": "#f2a541", "incident_violent": "#c2453d"}
names = {"aggregate_or_policy": "Statistics / policy", "incident_nonviolent": "Non-violent incident",
         "incident_violent": "Violent incident"}
ax[0].stackplot(x, *[out[f"vol_{k}"].fillna(0) for k in KINDS], colors=[cols[k] for k in KINDS],
                labels=[names[k] for k in KINDS], step="post")
ax[0].set_ylabel("Articles per 1M monitored\n(quarterly mean, by type)")
ax[0].legend(loc="upper left", frameon=False)
ax[0].set_title('US news coverage of "unruly passengers" by story type (GDELT, Haiku-labeled headlines)')
for k in KINDS:
    ax[1].plot(x, out[k] * 100, color=cols[k], label=names[k], drawstyle="steps-post")
ax[1].set_ylabel("Share of unique headlines (%)")
ax[1].set_ylim(0, 100)
for a_ in ax:
    a_.spines[["top", "right"]].set_visible(False)
    a_.axvspan(pd.Timestamp("2021-02-01"), pd.Timestamp("2022-04-18"), color="0.9", zorder=0)
ax[1].text(pd.Timestamp("2021-02-15"), 92, "federal mask mandate", fontsize=8, color="0.4")
fig.tight_layout()
fig.savefig(os.path.join(HERE, "headline_types.png"), dpi=130)
