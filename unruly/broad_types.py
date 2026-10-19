"""Coverage by story type and distinct incident events, broad-filter GKG sample (Oct 2019-Sep 2026).

Usage: python broad_types.py LABELDIR [SPLITDIR [VERIFYDIR]]
LABELDIR/YYYYMM.tsv hold id<TAB>kind<TAB>mask<TAB>us<TAB>event (rubric raw/haiku_labels/rubric_v2.md).
SPLITDIR/*.tsv hold id<TAB>group for the aggregate_or_policy stories (rubric_v2_policy_split.md);
health-rule announcements are then reported as health_rule, outside the misconduct counts.
VERIFYDIR/*.tsv hold id<TAB>yes|no from rubric_v2_violent_verify.md (see below).
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
# second pass (rubric_v2_policy_split.md): general stories that only announce health rules
# (mask/vaccine/alcohol-service changes with no misconduct angle) are counted separately
if len(sys.argv) > 2:
    sp = []
    for f in glob.glob(os.path.join(sys.argv[2], "*.tsv")):
        for line in open(f, encoding="utf8"):
            p = line.rstrip("\n").split("\t")
            if len(p) >= 2 and p[0].startswith("b"):
                sp.append(dict(id=p[0], group=p[1].strip()))
    sp = pd.DataFrame(sp).drop_duplicates("id").set_index("id").group
    agg = s.kind == "aggregate_or_policy"
    grp = s.loc[agg, "id"].map(sp)
    print("policy stories without a split label:", int(grp.isna().sum()))
    s.loc[agg & (s.id.map(sp) == "health_rule"), "kind"] = "health_rule"
    s.loc[agg & (s.id.map(sp) == "other"), "kind"] = "other"
# third pass (rubric_v2_violent_verify.md): every incident_violent and aggregate_or_policy
# headline re-checked with one narrow yes/no question. Unconfirmed "violent" headlines become
# non-violent incidents; policy headlines confirmed as a specific violent incident become one.
if len(sys.argv) > 3:
    vv = {}
    for f in glob.glob(os.path.join(sys.argv[3], "*.tsv")):
        for line in open(f, encoding="utf8"):
            p = line.rstrip("\n").split("\t")
            if len(p) >= 2 and p[0].startswith("b"):
                vv[p[0]] = p[1].strip().lower()
    ver = s.id.map(vv)
    need = s.kind.isin(["incident_violent", "aggregate_or_policy"])
    print("headlines needing verification without an answer:", int((need & ver.isna()).sum()))
    down = (s.kind == "incident_violent") & (ver == "no")
    up = (s.kind == "aggregate_or_policy") & (ver == "yes")
    print(f"violent -> non-violent: {int(down.sum())} of {int((s.kind == 'incident_violent').sum())};"
          f" policy -> violent: {int(up.sum())}")
    s.loc[down, "kind"] = "incident_nonviolent"
    s.loc[up, "kind"] = "incident_violent"
    s.loc[up, "event"] = "X" + s.loc[up, "id"]
    s.loc[up & ~s.us.isin(["0", "1"]), "us"] = "?"
bad = ~s.kind.isin(KINDS + ["other", "health_rule"])
print("stories:", len(s), " unlabeled or invalid kind:", int(bad.sum()))
s.to_csv(os.path.join(HERE, "broad_stories_labeled.csv"), index=False)

s["q"] = pd.to_datetime(s.month.astype(str), format="%Y%m").dt.to_period("Q")
s["mask"] = pd.to_numeric(s["mask"], errors="coerce")
inc = s.kind.isin(["incident_violent", "incident_nonviolent"])
# an event with any violent headline counts as violent
s["ev"] = s.month.astype(str) + "_" + s.event.astype(str)
ev_kind = s[inc].groupby("ev").kind.agg(lambda k: "incident_violent" if (k == "incident_violent").any() else "incident_nonviolent")
s.loc[inc, "kind_ev"] = s.loc[inc, "ev"].map(ev_kind)
# Haiku marks "?" when a headline doesn't name the airline; resolve at event level:
# any headline saying US -> US, else any saying foreign -> foreign, else unsure
ev_us = s[inc].groupby("ev").us.agg(lambda u: "1" if (u == "1").any() else ("0" if (u == "0").any() else "?"))
s.loc[inc, "us"] = s.loc[inc, "ev"].map(ev_us)


def counts(sub):
    out = pd.DataFrame(index=sorted(s.q.unique()))
    out["aggregate_or_policy"] = sub[sub.kind == "aggregate_or_policy"].groupby("q").size()
    out["health_rule"] = sub[sub.kind == "health_rule"].groupby("q").size()
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
cols = ["den", "health_rule"] + KINDS + [f"{k}_incl_unsure" for k in KINDS] + [f"stories_{k}" for k in KINDS[1:]] + [f"copies_{k}" for k in KINDS[1:]]
a = g.groupby("per")[cols].sum()
g["pax_months"] = g.pax.notna() * 3
full = g.dropna(subset=["pax"]).groupby("per")[["den", "reports", "pax", "pax_months"] + KINDS].sum()
full["pax_per_month"] = full.pax / full.pax_months  # periods differ in length; use average monthly passengers
for k in KINDS:
    a[f"{k}_per_M"] = a[k] / a.den * 1e6
    a[f"{k}_incl_unsure_per_M"] = a[f"{k}_incl_unsure"] / a.den * 1e6
    a[f"{k}_per_M_per_100M_pax"] = (full[k] / full.den * 1e6) / full.pax_per_month * 1e8
for k in KINDS[1:]:
    a[f"stories_per_event_{k}"] = a[f"stories_{k}"] / a[k]
    a[f"copies_per_event_{k}"] = a[f"copies_{k}"] / a[k]
a["health_rule_per_M"] = a.health_rule / a.den * 1e6
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

# uncertainty: ratio of each period's rate (per 1M articles) to the Oct 2019-Mar 2020 base.
# Poisson: log-scale interval from the two counts. Bootstrap: resample whole months within
# each period (captures clustering of coverage around viral events), 4000 draws.
import numpy as np
mo = s.copy()
mo["m"] = mo.month.astype(str)
mon = pd.DataFrame(index=sorted(den.month.astype(str)))
mon["den"] = den.set_index(den.month.astype(str)).gkg_titled_articles
u = mo[mo.us == "1"]
mon["aggregate_or_policy"] = u[u.kind == "aggregate_or_policy"].groupby("m").size()
for k in ["incident_nonviolent", "incident_violent"]:
    mon[k] = u[u.kind_ev == k].groupby("m").ev.nunique()
mon = mon.fillna(0)
mon["per"] = ["base" if m < "202004" else m[:4] for m in mon.index]
rng = np.random.default_rng(0)
rows = []
for k in KINDS:
    b = mon[mon.per == "base"]
    for per in [p for p in a.index if p != "base"]:
        x = mon[mon.per == per]
        if x.empty:
            continue
        rb, rx = b[k].sum() / b.den.sum(), x[k].sum() / x.den.sum()
        rr = rx / rb if rb else float("nan")
        se = np.sqrt(1 / max(x[k].sum(), 0.5) + 1 / max(b[k].sum(), 0.5))
        bs = []
        for _ in range(4000):
            bb = b.iloc[rng.integers(0, len(b), len(b))]
            xx = x.iloc[rng.integers(0, len(x), len(x))]
            r0 = bb[k].sum() / bb.den.sum()
            bs.append((xx[k].sum() / xx.den.sum()) / r0 if r0 else np.nan)
        bs = np.array(bs)
        rows.append(dict(kind=k, period=per, count=int(x[k].sum()), base_count=int(b[k].sum()), ratio=rr,
                         poisson_lo=rr * np.exp(-1.96 * se), poisson_hi=rr * np.exp(1.96 * se),
                         boot_lo=np.nanpercentile(bs, 2.5), boot_hi=np.nanpercentile(bs, 97.5),
                         boot_undefined_share=np.isnan(bs).mean()))
ci = pd.DataFrame(rows)
ci.round(3).to_csv(os.path.join(HERE, "broad_ratios.csv"), index=False)
print(ci.round(2).to_string(index=False))
