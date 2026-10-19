"""Classify GDELT 'unruly passenger' headlines into story types.

Usage: python classify_headlines.py
Reads raw/headlines/*.json (GDELT artlist, <=250 articles per quarter),
dedupes syndicated copies by normalized title, writes headlines_classified.csv
and prints shares by quarter.
"""
import glob, json, os, re
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))

AIR = re.compile(r"flight|plane|airline|airport|passenger|aircraft|jet|cabin|faa|attendant|pilot|air rage|"
                 r"delta|united|american|southwest|spirit|frontier|jetblue|alaska|allegiant|ryanair|easyjet", re.I)
VIOLENT = re.compile(r"punch|\bhit(s|ting)?\b|slap|assault|attack|\bbit(e|es|ing)?\b|kick|chok|strangl|headbutt|"
                     r"stab|duct[- ]?tape|\btaped\b|restrain|zip[- ]?tie|tied (up|down|to)|subdued|tackl|"
                     r"broke .*(nose|teeth)|bloodied|injur|grope|sexual|cockpit|(emergency |cabin )?door|"
                     r"emergency exit|threat(en|s)? to kill|bomb|choke|elbow|shov|spit|spat|fight|brawl|violent", re.I)
AGG = re.compile(r"\bfaa\b.*(fine|penalt|record|refer|zero[- ]tolerance|report|incident|investigat|crack)|"
                 r"\bfines?\b.*\bpassengers\b|record|surge|soar|spike|skyrocket|on the rise|\brise[sn]?\b|rising|"
                 r"increase|so far this year|number of|data|statistic|survey|zero[- ]tolerance|crackdown|"
                 r"no[- ]fly list|\blaw\b|\bbill\b|congress|senat|lawmaker|\bunion\b|campaign|alcohol sales|"
                 r"what (to|can|should)|how to|why |epidemic|trend|wave of|problem|crisis|across the|airlines (ask|urge|call)|"
                 r"\bfbi\b.*(refer|cases)|justice department|\bdoj\b|garland|prosecut", re.I)
SPECIFIC = re.compile(r"\b(man|woman|teen|mom|dad|mother|father|couple|boy|girl|he|she|his|her|suspect|"
                      r"arrested|charged|pleads?|sentenced|indicted|accused|video shows|caught on (video|camera)|"
                      r"diverted|forced to land|kicked off|booted|removed from|escorted|duct)\b", re.I)
MASK = re.compile(r"mask|face cover", re.I)


def norm(t):
    return re.sub(r"[^a-z0-9 ]", "", t.lower()).strip()[:90]


def classify(t):
    violent = bool(VIOLENT.search(t))
    agg = bool(AGG.search(t))
    spec = bool(SPECIFIC.search(t))
    if agg and not spec:
        kind = "aggregate_or_policy"
    elif violent:
        kind = "incident_violent"
    elif spec:
        kind = "incident_nonviolent"
    elif agg:
        kind = "aggregate_or_policy"
    else:
        kind = "other"
    return kind


rows = []
for f in sorted(glob.glob(os.path.join(HERE, "raw", "headlines", "*.json"))):
    txt = open(f, encoding="utf8").read().strip()
    arts = json.loads(txt).get("articles", []) if txt else []
    q = os.path.basename(f)[:8]
    for a in arts:
        rows.append(dict(quarter=q, title=a["title"], domain=a["domain"], date=a["seendate"][:8], url=a["url"]))

d = pd.DataFrame(rows)
d["key"] = d.title.map(norm)
d["n_copies"] = d.groupby(["quarter", "key"]).title.transform("size")
d = d.drop_duplicates(["quarter", "key"]).copy()
d = d[d.title.str.contains(AIR)]  # drop bus/transit/rideshare stories
d["kind"] = d.title.map(classify)
d["mask"] = d.title.str.contains(MASK)
d.to_csv(os.path.join(HERE, "headlines_classified.csv"), index=False)

s = pd.crosstab(d.quarter, d.kind, normalize="index").round(2)
s["n_unique"] = d.groupby("quarter").size()
s["mask_share"] = d.groupby("quarter")["mask"].mean().round(2)
print(s.to_string())
