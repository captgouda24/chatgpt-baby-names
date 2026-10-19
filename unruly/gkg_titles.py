"""Pull unruly-passenger headlines from GDELT GKG 2.0 raw files (fallback for the rate-limited DOC API).

Usage: python gkg_titles.py OUTDIR START_YYYYMM END_YYYYMM [THREADS]
Reads the :00 file of every hour (a 1-in-4 sample of GKG's 15-minute files), keeps
articles whose page title matches TITLE, and writes per month:
  OUTDIR/YYYYMM.tsv   file_ts, domain, url, title for matches
  OUTDIR/YYYYMM.n     files read, articles with a page title (denominator), failed files
GKG carries <PAGE_TITLE> only from about October 2019, so start there.
Months already written are skipped.
"""
import concurrent.futures as cf, io, os, re, sys, urllib.request, zipfile
from datetime import datetime, timedelta

TITLE = re.compile(r"unruly passenger|unruly (airline|plane|flight|air) ?(passenger|traveler|flyer)|"
                   r"disruptive passenger|air rage", re.I)
PT = re.compile(r"<PAGE_TITLE>(.*?)</PAGE_TITLE>")


def fetch(ts):
    u = f"https://data.gdeltproject.org/gdeltv2/{ts}.gkg.csv.zip"
    for _ in range(3):
        try:
            b = urllib.request.urlopen(u, timeout=120).read()
            break
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return ts, 0, []
        except Exception:
            pass
    else:
        return ts, None, []
    z = zipfile.ZipFile(io.BytesIO(b))
    n, hits = 0, []
    for line in z.read(z.namelist()[0]).decode("utf8", "ignore").split("\n"):
        f = line.split("\t")
        if len(f) < 27:
            continue
        m = PT.search(f[26])
        if not m:  # PAGE_TITLE only exists from about Oct 2019
            continue
        n += 1
        if TITLE.search(m.group(1)):
            hits.append((ts, f[3], f[4], " ".join(m.group(1).split())))
    return ts, n, hits


out, start, end = sys.argv[1], sys.argv[2], sys.argv[3]
threads = int(sys.argv[4]) if len(sys.argv) > 4 else 16
os.makedirs(out, exist_ok=True)
m = datetime.strptime(start, "%Y%m")
while m.strftime("%Y%m") <= end:
    nxt = (m + timedelta(days=32)).replace(day=1)
    tag = m.strftime("%Y%m")
    if not os.path.exists(os.path.join(out, tag + ".n")):
        hours, t = [], m
        while t < nxt:
            hours.append(t.strftime("%Y%m%d%H%M%S"))
            t += timedelta(hours=1)
        files = arts = failed = 0
        rows = []
        with cf.ThreadPoolExecutor(threads) as ex:
            for ts, n, hits in ex.map(fetch, hours):
                if n is None:
                    failed += 1
                elif n:
                    files += 1
                    arts += n
                    rows += hits
        with open(os.path.join(out, tag + ".tsv"), "w", encoding="utf8") as fh:
            for r in sorted(rows):
                fh.write("\t".join(r) + "\n")
        with open(os.path.join(out, tag + ".n"), "w") as fh:
            fh.write(f"{files}\t{arts}\t{failed}\n")
        print(tag, files, arts, failed, len(rows), flush=True)
    m = nxt
