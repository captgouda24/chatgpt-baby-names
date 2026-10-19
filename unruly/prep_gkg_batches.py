"""Dedupe GKG headline matches, keep US outlets, and batch them for LLM labeling.

Usage: python prep_gkg_batches.py OUTDIR
Reads raw/gkg_titles/YYYYMM.tsv (from gkg_titles.py). GKG has no source country,
so US outlets are approximated by domain: .com/.org/.net/.us/.edu/.gov/.tv/.fm,
minus a list of known foreign outlets on those TLDs. Writes gkg_headlines_unique.csv,
gkg_monthly_counts.csv (all US matches incl. syndicated copies, plus the denominator)
and OUTDIR/batch_NNN.tsv for headlines not yet labeled in OUTDIR/labels/.
"""
import glob, html, os, re, sys
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
US_TLD = re.compile(r"\.(com|org|net|us|edu|gov|tv|fm)$")
FOREIGN = re.compile(r"india|hindu|hindustan|business-standard|timesnow|prokerala|ndtv|deccan|tribune\.com\.pk|dawn\.com|"
                     r"gulf|khaleej|arab|thenational|aljazeera|asia|scmp|straitstimes|japantimes|korea|xinhua|cgtn|"
                     r"globaltimes|sputnik|^rt\.com|theguardian|bbc|independent\.ie|irishtimes|sundayworld|rte\.|"
                     r"thejournal|vocm|cbc\.ca|ctvnews|globalnews|travelmole|traveldailymedia|breakingtravelnews|"
                     r"eturbonews|simpleflying|aerotime|euronews|france24|dw\.com|thelocal|news24|"
                     r"pulse\.ng|nation\.africa|nzherald|stuff\.co|9news|smh\.com|news\.com", re.I)
AIR = re.compile(r"flight|plane|airline|airport|passenger|aircraft|jet|cabin|faa|attendant|pilot|air rage", re.I)


def norm(t):
    return re.sub(r"[^a-z0-9 ]", "", t.lower()).strip()[:90]


def story(t):
    # same story across outlets: drop " | Station name" / " - Outlet" suffixes and HTML entities
    t = re.sub(r"&#?\w+;.*$", "", html.unescape(t)) if "&#" in t else html.unescape(t)
    t = re.split(r"\s+\|\s+|\s+[-\u2013\u2014]\s+(?=[A-Z0-9][^-\u2013\u2014]{0,40}$)", t)[0]
    return re.sub(r"[^a-z0-9 ]", "", t.lower()).split()[:12]


rows, den = [], []
for f in sorted(glob.glob(os.path.join(HERE, "raw", "gkg_titles", "*.tsv"))):
    tag = os.path.basename(f)[:6]
    files, arts, _ = open(f[:-4] + ".n").read().split()
    den.append(dict(month=tag, gkg_files=int(files), gkg_titled_articles=int(arts)))
    for line in open(f, encoding="utf8"):
        p = line.rstrip("\n").split("\t")
        if len(p) == 4:
            rows.append(dict(month=tag, date=p[0][:8], domain=p[1], url=p[2], title=p[3]))

d = pd.DataFrame(rows)
d["us"] = d.domain.str.contains(US_TLD) & ~d.domain.str.contains(FOREIGN)
cnt = pd.DataFrame(den).merge(d.groupby("month").agg(matches_all=("us", "size"), matches_us=("us", "sum")).reset_index(),
                              on="month", how="left").fillna(0)
cnt.to_csv(os.path.join(HERE, "gkg_monthly_counts.csv"), index=False)

d = d[d.us & d.title.str.contains(AIR)].copy()
d["quarter"] = pd.to_datetime(d.month, format="%Y%m").dt.to_period("Q").dt.start_time.dt.strftime("%Y%m%d")
d["key"] = d.title.map(norm)
d["n_copies"] = d.groupby(["quarter", "key"]).title.transform("size")
d = d.sort_values(["quarter", "date"]).drop_duplicates(["quarter", "key"]).copy()
d["id"] = "g" + d.quarter + "_" + d.groupby("quarter").cumcount().astype(str)
d["story"] = d.title.map(lambda t: " ".join(story(t)))
d.to_csv(os.path.join(HERE, "gkg_headlines_unique.csv"), index=False)

out = sys.argv[1]
os.makedirs(os.path.join(out, "labels"), exist_ok=True)
done = set()
for f in glob.glob(os.path.join(out, "labels", "*.tsv")):
    done |= {l.split("\t")[0] for l in open(f, encoding="utf8") if l.strip()}
todo = d[~d.id.isin(done)]
start = len(glob.glob(os.path.join(out, "batch_*.tsv")))
for i in range(0, len(todo), 150):
    with open(os.path.join(out, f"batch_{start + i // 150:03d}.tsv"), "w", encoding="utf8") as fh:
        for r in todo.iloc[i:i + 150].itertuples():
            fh.write(f"{r.id}\t{r.title.replace(chr(9), ' ')}\n")
print(len(rows), "matches;", int(cnt.matches_us.sum()), "US;", len(d), "unique US aviation;",
      (len(todo) + 149) // 150, "new batches from", start)
print(d.groupby("quarter").size().to_string())
