"""Filter the broad GKG headline superset and batch it, one calendar month per batch, for Haiku labeling.

Usage: python prep_broad_batches.py SRCDIR OUTDIR
SRCDIR holds YYYYMM.tsv/.n from `gkg_titles.py ... --broad`. A headline is kept if it
matches the narrow phrase filter (unruly/disruptive passenger, air rage) OR the
broad filter: a misconduct word plus a crew word, or a passenger/person word together
with a flight/plane/airline word, and no ground-transport word. US outlets are
approximated by domain as in prep_gkg_batches.py. Copies of one story (same headline
minus outlet suffix) are collapsed within a month.

Writes broad_stories.csv (one row per month x story) and broad_monthly_counts.csv
(denominator), and OUTDIR/YYYYMM.tsv (id<TAB>title) for months without labels in
OUTDIR/labels/YYYYMM.tsv. Label with raw/haiku_labels/rubric_v2.md.
"""
import glob, html, os, re, sys
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
NARROW = re.compile(r"unruly passenger|unruly (airline|plane|flight|air) ?(passenger|traveler|flyer)|"
                    r"disruptive passenger|air rage", re.I)
BAD = re.compile(r"punch|\bhit(s|ting)?\b|slap|assault|attack|\bbit(e|es|ing)?\b|kick|chok|strangl|headbutt|stab|fight|brawl|scuffle|"
                 r"altercation|melee|duct[- ]?tap|zip[- ]?tie|restrain|subdu|tackl|grop|sexual|lewd|masturbat|indecent|urinat|\bspit|"
                 r"\bspat\b|threat|bomb|hijack|storm|breach|\bdoor|emergency exit|drunk|intoxicat|\bbooze|alcohol|disrupt|unruly|\brage|"
                 r"meltdown|tirade|\brant|yell|scream|\bslur|racist|abus|harass|\bmasks?\b|maskless|refus|kicked off|booted|removed|"
                 r"escorted|arrest|charged|pleads?|sentenc|indict|\bjail|prison|\bfined?\b|\bfbi\b|divert|emergency landing|"
                 r"turn(s|ed)? (back|around)|banned|no-fly|smok|vap(e|ing)|naked|nude|feces|police|\bcops?\b|misconduct|violent|"
                 r"outburst|rowdy|belligerent|combative|tantrum|disturbance|incident", re.I)
PAX = re.compile(r"\b(passengers?|fliers?|flyers?|travell?ers?)\b", re.I)
CREW = re.compile(r"\b(flight attendants?|stewardess(es)?|cabin crew|crew members?|flight crew|"
                  r"airline (crew|staff|employees?|workers?|agents?))\b", re.I)
CABIN = re.compile(r"\b(flights?|planes?|airplanes?|airliners?|jetliners?|jet|aboard|on ?board|in-?flight|mid-?air|cockpit|airlines?|faa|"
                   r"delta|united|american airlines|southwest|spirit|frontier|jetblue|alaska airlines|allegiant|hawaiian|sun country)\b", re.I)
PERSON = re.compile(r"\b(man|woman|men|women|teens?|teenager|boy|girl|mom|dad|mother|father|couple|person|suspect|someone|"
                    r"influencer|rapper|actor|actress|singer|ceo|lawmaker|congressman|senator|player|officer|soldier|marine|"
                    r"grandma|student|family)\b", re.I)
GROUND = re.compile(r"\b(uber|lyft|taxi|cab driver|bus|buses|train|subway|metro|transit|cruise|ferry|car crash|driver|vehicle|"
                    r"rail|amtrak|boat|ship)\b", re.I)
US_TLD = re.compile(r"\.(?:com|org|net|us|edu|gov|tv|fm)$")
FOREIGN = re.compile(r"india|hindu|hindustan|business-standard|timesnow|prokerala|ndtv|deccan|tribune\.com\.pk|dawn\.com|"
                     r"gulf|khaleej|arab|thenational|aljazeera|asia|scmp|straitstimes|japantimes|korea|xinhua|cgtn|"
                     r"globaltimes|sputnik|^rt\.com|theguardian|bbc|independent\.ie|irishtimes|sundayworld|rte\.|"
                     r"thejournal|vocm|cbc\.ca|ctvnews|globalnews|travelmole|traveldailymedia|breakingtravelnews|"
                     r"eturbonews|simpleflying|aerotime|euronews|france24|dw\.com|thelocal|news24|"
                     r"pulse\.ng|nation\.africa|nzherald|stuff\.co|9news|smh\.com|news\.com|winnipegfreepress|"
                     r"torontosun|nationalpost|thestar\.com|lfpress|ottawacitizen|montrealgazette|vancouversun", re.I)


def story(t):
    # same story across outlets: drop " | Station name" / " - Outlet" suffixes and HTML entities
    t = re.sub(r"&#?\w+;.*$", "", html.unescape(t)) if "&#" in t else html.unescape(t)
    t = re.split(r"\s+\|\s+|\s+[-–—]\s+(?=[A-Z0-9][^-–—]{0,40}$)", t)[0]
    return " ".join(re.sub(r"[^a-z0-9 ]", "", t.lower()).split()[:12])


src, out = sys.argv[1], sys.argv[2]
rows, den = [], []
for f in sorted(glob.glob(os.path.join(src, "*.tsv"))):
    tag = os.path.basename(f)[:6]
    if not os.path.exists(f[:-4] + ".n"):  # month still being pulled
        continue
    files, arts, _ = open(f[:-4] + ".n").read().split()
    den.append(dict(month=tag, gkg_files=int(files), gkg_titled_articles=int(arts)))
    for line in open(f, encoding="utf8"):
        p = line.rstrip("\n").split("\t")
        if len(p) == 4:
            rows.append(dict(month=tag, date=p[0][:8], domain=p[1], url=p[2], title=p[3]))
pd.DataFrame(den).to_csv(os.path.join(HERE, "broad_monthly_counts.csv"), index=False)

d = pd.DataFrame(rows)
d = d[d.domain.str.contains(US_TLD) & ~d.domain.str.contains(FOREIGN)]
t = d.title
d["narrow"] = t.str.contains(NARROW)
d["broad"] = (t.str.contains(BAD) & (t.str.contains(CREW) | ((t.str.contains(PAX) | t.str.contains(PERSON)) & t.str.contains(CABIN)))
              & ~t.str.contains(GROUND))
d = d[d.narrow | d.broad].copy()
d["story"] = d.title.map(story)
s = (d.sort_values("date").groupby(["month", "story"], sort=False)
     .agg(date=("date", "first"), title=("title", "first"), domain=("domain", "first"),
          url=("url", "first"), narrow=("narrow", "max"), copies=("url", "size")).reset_index())
s = s.sort_values(["month", "date"]).reset_index(drop=True)
s["id"] = "b" + s.month.astype(str) + "_" + s.groupby("month").cumcount().astype(str)
s.to_csv(os.path.join(HERE, "broad_stories.csv"), index=False)

os.makedirs(os.path.join(out, "labels"), exist_ok=True)
new = 0
for m, g in s.groupby("month"):
    if os.path.exists(os.path.join(out, "labels", f"{m}.tsv")):
        continue
    with open(os.path.join(out, f"{m}.tsv"), "w", encoding="utf8") as fh:
        for r in g.itertuples():
            fh.write(f"{r.id}\t{html.unescape(r.title).replace(chr(9), ' ')}\n")
    new += 1
print(len(d), "headlines kept;", len(s), "stories;", new, "month batches written")
print(s.groupby("month").size().describe().round(0).to_string())
