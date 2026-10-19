"""Coverage by story type and distinct incident events, broad-filter GKG sample (Oct 2019-Sep 2026).

Usage: python broad_types.py LABELDIR
LABELDIR/YYYYMM.tsv hold id<TAB>kind<TAB>mask<TAB>us<TAB>event (rubric raw/haiku_labels/rubric_v2.md).
Counts US items (us == 1; us == "?" kept as a sensitivity check):
  aggregate_or_policy: distinct stories
  incident_violent / incident_nonviolent: distinct events (Haiku's event codes, within a month)
per 1M GKG articles with a page title, and again per 100M BTS passengers.
Writes broad_stories_labeled.csv, broad_quarterly.csv, broad_annual.csv, broad_types.png.
"""
import glob, os, sys
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
KINDS = ["aggregate_or_policy", "incident_nonviolent", "incident_violent"]
NAMES = {"aggregate_or_policy": "Statistics / policy stories", "incident_nonviolent": "Non-violent incidents",
         "incident_violent": "Violent incidents"}
COLS = {"aggregate_or_policy": "#4c78a8", "incident_nonviolent": "#f2a541", "incident_violent": "#c2453d"}

lab = []
for f in sorted(glob.glob(os.path.join(sys.argv[1], "*.tsv"))):
    for line in open(f, encoding="utf8"):
        p = line.rstrip("\n").split("\t")
        if len(p) >= 5 and p[0].startswith("b"):
            lab.append(dict(id=p[0], kind=p[1].strip(), mask=p[2].strip(), us=p[3].strip(), event=p[4].strip()))
lab = pd.DataFrame(lab).drop_duplicates("id")
s = pd.read_csv(os.path.join(HERE, "broad_stories.csv")).merge(lab, on="id", how="left")
bad = ~s.kind.isin(KINDS + ["other"])
print("stories:", len(s), " unlabeled or invalid kind:", int(bad.sum()))
s.to_csv(os.path.join(HERE, "broad_stories_labeled.csv"), index=False)

s["q"] = pd.to_datetime(s.month.astype(str), format="%Y%m").dt.to_period("Q")
s["mask"] = pd.to_numeric(s["mask"], errors="coerce")
inc = s.kind.isin(["incident_violent", "incident_nonviolent"])
# an event with any violent headline counts as violent
s["ev"] = s.month.astype(str) + "_" + s.event.astype(str)
ev_kind = s[inc].groupby("ev").kind.agg(lambda k: "incident_violent" if (k == "incident_violent").any() else "incident_nonviolent")
s.loc[inc, "kind_ev"] = s.loc[inc, "ev"].map(ev_kind)


def counts(sub):
    out = pd.DataFrame(index=sorted(s.q.unique()))
    out["aggregate_or_policy"] = sub[sub.kind == "aggregate_or_policy"].groupby("q").size()
    for k in ["incident_nonviolent", "incident_violent"]:
        e = sub[sub.kind_ev == k]
        out[k] = e.groupby("q").ev.nunique()
        out[f"stories_{k}"] = e.groupby("q").size()
        out[f"copies_{k}"] = e.groupby("q").copies.sum()
    return out.fillna(0)


us = counts(s[s.us == "1"])
us_wide = counts(s[s.us.isin(["1", "?"])]).add_suffix("_incl_unsure")
den = pd.read_csv(os.path.join(HERE, "broad_monthly_counts.csv"))
den["q"] = pd.to_datetime(den.month.astype(str), format="%Y%m").dt.to_period("Q")
p = pd.read_csv(os.path.join(HERE, "analysis_monthly.csv"), parse_dates=["month"])
p["q"] = p.month.dt.to_period("Q")
pq = p.groupby("q").agg(reports=("reports", "sum"), pax=("pax", "sum"), pm=("pax", "count"))
pq.loc[pq.pm < 3, "pax"] = float("nan")
g = den.groupby("q").gkg_titled_articles.sum().to_frame("den").join(us).join(us_wide).join(pq[["reports", "pax"]])
g["mask_share_incident_stories"] = s[inc & (s.us == "1")].groupby("q")["mask"].mean()
for k in KINDS:
    g[f"{k}_per_M"] = g[k] / g.den * 1e6
g.round(4).to_csv(os.path.join(HERE, "broad_quarterly.csv"))

g["per"] = [("base" if q < pd.Period("2020Q2") else str(q.year)) for q in g.index]
cols = ["den"] + KINDS + [f"{k}_incl_unsure" for k in KINDS] + [f"stories_{k}" for k in KINDS[1:]] + [f"copies_{k}" for k in KINDS[1:]]
a = g.groupby("per")[cols].sum()
full = g.dropna(subset=["pax"]).groupby("per")[["den", "reports", "pax"] + KINDS].sum()
for k in KINDS:
    a[f"{k}_per_M"] = a[k] / a.den * 1e6
    a[f"{k}_incl_unsure_per_M"] = a[f"{k}_incl_unsure"] / a.den * 1e6
    a[f"{k}_per_M_per_100M_pax"] = (full[k] / full.den * 1e6) / full.pax * 1e8
for k in KINDS[1:]:
    a[f"stories_per_event_{k}"] = a[f"stories_{k}"] / a[k]
    a[f"copies_per_event_{k}"] = a[f"copies_{k}"] / a[k]
a["agg_share_of_items"] = a.aggregate_or_policy / a[KINDS].sum(axis=1)
a["faa_reports_per_10M_pax"] = full.reports / full.pax * 1e7
a = a.reindex(["base"] + [str(y) for y in range(2020, 2027)])
a.round(3).to_csv(os.path.join(HERE, "broad_annual.csv"))
pd.set_option("display.width", 220)
print(a.round(2).T.to_string())

# chart: linear scales
fig, ax = plt.subplots(2, 1, figsize=(10, 8.5))
x = g.index.to_timestamp()
ax[0].stackplot(x, *[g[f"{k}_per_M"] for k in KINDS], colors=[COLS[k] for k in KINDS],
                labels=[NAMES[k] for k in KINDS], step="post")
top = ax[0].get_ylim()[1] * 1.12
ax[0].set_ylim(0, top)
ax[0].axvspan(pd.Timestamp("2021-02-01"), pd.Timestamp("2022-04-18"), color="0.92", zorder=0)
ax[0].text(pd.Timestamp("2021-02-15"), top * 0.97, "federal mask mandate", fontsize=8, color="0.4", va="top")
ax[0].set_ylabel("Per 1M monitored articles\n(stories, or distinct incident events)")
ax[0].set_title("US news coverage of airline passenger misconduct, broad headline filter (GDELT GKG, Haiku-labeled)", loc="left")
ax[0].legend(loc="upper right", frameon=False)

ussc = pd.read_csv(os.path.join(HERE, "raw", "severe", "ussc_2A5_2.csv")).set_index("fiscal_year").offender_based_any_applied_2A5_2
yrs = [str(y) for y in range(2020, 2027)]
xs = list(range(len(yrs) + 1))
lab_x = ["Oct19–\nMar20", "Apr–Dec\n2020"] + yrs[1:-1] + ["2026\nJan–Jun"]
series = {f"{k}_per_M_per_100M_pax": (NAMES[k] + " / passenger", COLS[k]) for k in KINDS[1:]}
series["faa_reports_per_10M_pax"] = ("FAA unruly reports / passenger", "0.2")
for c, (nm, col) in series.items():
    ax[1].plot(xs, (a[c] / a.loc["base", c]).values, marker="o", color=col, label=nm)
fy = [ussc.get(int(y), float("nan")) / ussc.loc[[2019, 2020]].mean() for y in yrs]
ax[1].plot(xs, [1.0] + fy, marker="s", ls="--", color="0.5", label="Federal §2A5.2 sentencings (FY, base FY19–20)")
ax[1].axhline(1, color="0.8", lw=0.8)
ax[1].set_ylim(bottom=0)
ax[1].set_xticks(xs, lab_x)
ax[1].set_ylabel("Index, Oct 2019–Mar 2020 = 1")
ax[1].legend(frameon=False, fontsize=8, loc="upper right")
for a_ in ax:
    a_.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(os.path.join(HERE, "broad_types.png"), dpi=130)
