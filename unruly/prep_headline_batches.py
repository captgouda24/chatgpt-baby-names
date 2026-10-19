"""Dedupe GDELT 'unruly passenger' headlines and split them into batches for LLM labeling.

Usage: python prep_headline_batches.py OUTDIR
Reads raw/headlines/*.json, drops syndicated copies (same normalized title within
a quarter) and non-aviation stories, writes headlines_unique.csv and
OUTDIR/batch_NNN.tsv (id<TAB>title, ~150 rows each) for headlines
not yet labeled in OUTDIR/labels/.
"""
import glob, json, os, re, sys
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
AIR = re.compile(r"flight|plane|airline|airport|passenger|aircraft|jet|cabin|faa|attendant|pilot|air rage|"
                 r"delta|united|american|southwest|spirit|frontier|jetblue|alaska|allegiant|ryanair|easyjet", re.I)
NONAIR = re.compile(r"\bbus\b|transit|subway|\bmetro\b|\btrains?\b|\buber\b|lyft|rideshare|cruise|ferry", re.I)


def norm(t):
    return re.sub(r"[^a-z0-9 ]", "", t.lower()).strip()[:90]


rows = []
for f in sorted(glob.glob(os.path.join(HERE, "raw", "headlines", "*.json"))):
    txt = open(f, encoding="utf8").read().strip()
    arts = json.loads(txt).get("articles", []) if txt else []
    q = os.path.basename(f)[:8]
    for a in arts:
        rows.append(dict(quarter=q, title=a["title"].strip(), domain=a["domain"], date=a["seendate"][:8], url=a["url"]))

d = pd.DataFrame(rows)
d["key"] = d.title.map(norm)
d["n_copies"] = d.groupby(["quarter", "key"]).title.transform("size")
d = d.drop_duplicates(["quarter", "key"]).copy()
d = d[d.title.str.contains(AIR) & ~(d.title.str.contains(NONAIR) & ~d.title.str.contains(r"flight|plane|airline|airport", case=False))]
d["id"] = d.quarter + "_" + d.groupby("quarter").cumcount().astype(str)
d.to_csv(os.path.join(HERE, "headlines_unique.csv"), index=False)

# only batch headlines without a label yet (labels/*.tsv: id<TAB>kind<TAB>mask)
out = sys.argv[1]
os.makedirs(os.path.join(out, "labels"), exist_ok=True)
done = set()
for f in glob.glob(os.path.join(out, "labels", "*.tsv")):
    done |= {l.split("\t")[0] for l in open(f, encoding="utf8") if l.strip()}
todo = d[~d.id.isin(done)]
start = len(glob.glob(os.path.join(out, "batch_*.tsv")))
for i in range(0, len(todo), 150):
    b = todo.iloc[i:i + 150]
    with open(os.path.join(out, f"batch_{start + i // 150:03d}.tsv"), "w", encoding="utf8") as fh:
        for r in b.itertuples():
            fh.write(f"{r.id}\t{r.title.replace(chr(9), ' ')}\n")
print(len(rows), "raw;", len(d), "unique aviation;", len(todo), "unlabeled;", (len(todo) + 149) // 150, "new batches from", start)
print(d.groupby("quarter").size().to_string())
