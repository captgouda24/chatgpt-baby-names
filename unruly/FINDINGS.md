# Why did unruly-passenger incidents rise?

Data:
- FAA monthly unruly-passenger reports, Jan 2017–Sep 2026. Extracted from the FAA Tableau dashboard (faa.gov/unruly) into `raw/faa_monthly.csv`.
- BTS Monthly Transportation Statistics passengers on U.S. airlines, total (`raw/bts_mts.json`). This series runs through Jun 2026.
- FAA investigations initiated, 1995–2021 (`raw/dw_investigations.csv`).

Outputs: `analysis_monthly.csv`, `composition_bound.csv`, `unruly_rate.png`.

## Reports per 10M passengers

| Year | Reports | Passengers (M) | Per 10M passengers |
|---|---|---|---|
| 2017 | 544 | 849 | 6.4 |
| 2018 | 889 | 889 | 10.0 |
| 2019 | 1,161 | 927 | 12.5 |
| Jan–Feb 2020 | 246 | 139 | 17.7 |
| 2020 | 1,009 | 372 | 27.1 |
| 2021 | 5,973 | 666 | 89.7 |
| 2022 | 2,455 | 853 | 28.8 |
| 2023 | 2,076 | 942 | 22.0 |
| 2024 | 2,102 | 983 | 21.4 |
| 2025 | 1,623 | 972 | 16.7 |
| 2026 H1 | 843 | 475 | 17.7 |

## Findings

1. **The series was already rising steeply before COVID.** Reports per passenger nearly tripled from 2017 to early 2020, from 6.4 to 17.7 per 10M. FAA investigations stayed flat over the same years (91, 159, 146). Reports rising while investigations stayed flat points to more incidents being reported, not more serious misconduct. Using the longer investigations series, 2019 was also unusually low per passenger compared with 1995–2004, when there were 200–310 investigations a year on fewer passengers.

2. **The 2021 spike is a policy event, and the timing shows it.** In January 2021 the rate was 60 per 10M. In February it was 214. That month the FAA's zero-tolerance order took effect (Jan 13) and the federal mask mandate began (Feb 1), which made refusing a mask a federal violation. FAA reported that about 72% of 2021 reports were mask-related. The mix of passengers barely changed between January and February 2021, so a jump of this size can't be a composition effect. When the mandate was vacated on Apr 18, 2022, the rate fell from 34 (April) to 20 (May) to 17 (June).

3. **After the mandate, the rate went back to its pre-pandemic level.** From mid-2022 through 2024 the rate was 17–22. In 2025–26 it was about 17. That's roughly the Jan–Feb 2020 level of 17.7 and the same months of 2019 (14.4). Calling this "1.7× 2019" mostly measures the reporting run-up during 2017–2019.

4. **The one span the business-travel story could explain is H2 2020.** From Jul–Dec 2020 the rate was 30–41 per 10M, about twice early 2020. There was no federal mandate yet, but airlines had their own mask rules from May 2020. Business travel was at its lowest.

## How big can the business-travel composition effect be?

Take the most generous case for the hypothesis: business travelers cause zero incidents. Then the rate can rise at most by the factor (1−b₁)/(1−b₀), where b₀ and b₁ are the business share of passengers before and after (see `composition_bound.csv`).

| Pre-COVID business share b₀ | 2021 trough (business at 30% of 2019, leisure at 80%) | 2023+ (business 80%, leisure 105%) |
|---|---|---|
| 12% | ×1.08 | ×1.03 |
| 30% | ×1.23 | ×1.08 |
| 40% | ×1.33 | ×1.11 |

The observed changes are ×5.5 in 2021 and ×1.2 in 2023–24, both relative to early 2020. Composition can explain at most a few percent of the 2021 spike. For H2 2020 it could account for perhaps a quarter of the doubling. After 2022 there is very little left over to explain.

The real composition question is within leisure travel: less frequent flyers, more growth at ultra-low-cost carriers, and more families and groups. Testing that would need incidents broken out by carrier or route, which FAA does not publish.

## Caveats
- Reporting depends on the crew: FAA itself says reporting is "at the discretion of the crewmember." After 2021, airlines and unions actively pushed crews to report, so even a flat rate may hide a fall in actual behavior.
- IATA's global series is no cleaner. Its rate went from 1 per 1,424 flights (2016) to 1 per 1,053 (2017), 1 per 835 (2021), 1 per 568 (2022) and 1 per 307 (2024), while the number of reporting operators grew to more than 140 when IATA moved to IDX. Its 2023–24 figures disagree across IATA's own documents. It also keeps rising after 2022 while the FAA series falls, which points to changes in its reporting panel.
- The April 2020 point (23 reports on 3M passengers) is noise from a tiny denominator.
- A more independent check would be NASA ASRS crew reports coded "passenger misconduct". Reporting incentives there didn't change with FAA enforcement policy. Not pulled yet.

## News coverage (GDELT, US sources)

Data: GDELT DOC 2.0 daily counts of US-source articles matching "unruly passenger(s)", aggregated to months (`raw/gdelt_unruly.csv`). A second query covers "disruptive passenger(s)" or "air rage" (`raw/gdelt_disruptive.csv`). Each month's count is divided by the total number of articles GDELT monitored that month. That total fell about 4× between 2017 and 2026, so raw counts understate how much coverage grew. Outputs are in `news_vs_reports_monthly.csv` and `news_vs_reports.png`.

| Year | FAA reports | Articles | Articles per 1M monitored | Articles per FAA report |
|---|---|---|---|---|
| 2017 | 544 | 2,229 | 9.8 | 4.1 |
| 2018 | 889 | 2,243 | 11.6 | 2.5 |
| 2019 | 1,161 | 2,264 | 13.3 | 2.0 |
| 2020 | 1,009 | 363 | 2.6 | 0.4 |
| 2021 | 5,973 | 10,725 | 89.1 | 1.8 |
| 2022 | 2,455 | 4,614 | 44.8 | 1.9 |
| 2023 | 2,076 | 1,649 | 24.2 | 0.8 |
| 2024 | 2,102 | 961 | 16.1 | 0.5 |
| 2025 | 1,623 | 954 | 17.0 | 0.6 |
| 2026 (Jan–Sep) | 1,310 | 1,325 | 36.0 | 1.0 |

1. **Coverage did rise sharply, about 7× its 2017–19 share in 2021.** That roughly matches the rise in FAA reports. Coverage per report was no higher in 2021–22 than in 2019 (about 1.8 against 2.0). The press did not cover the 2021 surge disproportionately.
2. **Coverage followed reports rather than leading them.** Reports jumped in February 2021, when there were only 40 articles. Sustained heavy coverage began in May 2021, when there were 1,340 articles. That month brought high-profile assaults on crew and FAA's first publicized fines under zero tolerance. The January 2021 news spike (734 articles) was coverage around January 6 and flights to and from DC, not the mask surge. Coverage can't explain the initial jump in reporting. It could have helped keep reporting high afterward, because crews and airlines had public backing to report.
3. **The H2 2020 rise got almost no coverage.** From Jul–Dec 2020 there were about 1 article per 1M monitored, a tenth of the 2017–19 share, even though reports per passenger had doubled.
4. **Coverage per report fell from 2023 on, to 0.5–0.8 against about 2 before COVID.** The story lost novelty, and coverage fell faster than incidents. 2026 shows spiky coverage, with months near 90–100 per 1M, but no matching rise in reports. These look like individual viral incidents. I haven't checked which events they were.

Caveats: GDELT's source panel changes over time, which the per-1M normalization only partly corrects. Matching on a phrase misses stories that don't say "unruly passenger", and before 2021 that term was probably less standard. The "disruptive/air rage" query shows the same 2021–22 bulge (3,060 articles in 2021 against 1,183 in 2019) but no pre-2020 drop-off from the unruly series. That suggests the vocabulary didn't shift much.

## What kind of stories made up the 2021–22 coverage spike?

The question: was the coverage spike mostly statistics and policy stories plus minor incidents that once went unreported, or did coverage of violent incidents rise too?

**Data.** GDELT's DOC API rate-limited this work to a standstill: every request got a 429 for more than two hours. So the 2019–2026 series comes from GDELT's raw GKG 2.0 files, which carry a `<PAGE_TITLE>` only from about October 2019. `gkg_titles.py` reads the :00 file of every hour (one in four of GKG's 15-minute files), 84 months, about 80M articles with a title. It keeps headlines containing "unruly passenger(s)", "disruptive passenger" or "air rage". `prep_gkg_batches.py` keeps US outlets, approximated by domain (.com/.org/.net etc., minus a list of known foreign outlets), and aviation headlines. It then collapses copies of the same story; iHeart radio-station sites repost one story 100+ times with a station suffix. That leaves 733 distinct stories. The DOC API sample pulled earlier (2018 to Q3 2020, missing 2018Q3 and 2020Q2) is labeled the same way in `headlines_classified.csv` and serves as the 2018–19 baseline.

**Labels.** Claude Haiku labeled each headline with a fixed rubric:
- statistics/policy: trends, aggregate FAA fines, laws, unions, explainers
- violent incident: physical violence, restraint, door or cockpit attempts, sexual assault, threats to kill
- non-violent incident: mask refusal, verbal, intoxication, diversion or removal without violence
- other

Each headline also got a mask flag. On hand-checks of 50 random headlines, I agreed with 46 of 50 labels (92%) in the API sample and 48 of 50 (96%) in the GKG sample. Most disagreements were diversions labeled violent or other, and empty headlines labeled policy. Outputs are in `gkg_headlines_classified.csv`, `gkg_types_quarterly.csv`, `gkg_types_annual.csv` and `gkg_types.png`.

Rates are distinct US stories per 1M GKG articles. The "per passenger" columns divide that again by BTS passengers, in units per 100M.

| Period | Stats/policy share | Violent share | Stats/policy per 1M | Non-violent per 1M | Violent per 1M | Non-violent per pax | Violent per pax | FAA reports per 10M pax |
|---|---|---|---|---|---|---|---|---|
| Oct 2019–Mar 2020 | 15% | 21% | 0.65 | 2.73 | 0.91 | 0.67 | 0.22 | 16.1 |
| Apr–Dec 2020 | 40% | 30% | 0.43 | 0.32 | 0.32 | 0.17 | 0.17 | 35.1 |
| 2021 | **72%** | 9% | **17.1** | 4.39 | 2.20 | 0.66 | 0.33 | 89.7 |
| 2022 | 55% | 15% | 7.73 | 4.36 | 2.08 | 0.51 | 0.24 | 28.8 |
| 2023 | 54% | 10% | 4.82 | 3.14 | 0.92 | 0.33 | 0.10 | 22.1 |
| 2024 | 33% | 25% | 1.54 | 1.94 | 1.13 | 0.20 | 0.12 | 21.4 |
| 2025 | 19% | 30% | 0.77 | 2.12 | 1.25 | 0.22 | 0.13 | 16.7 |
| 2026 (Jan–Sep; pax Jan–Jun) | 10% | 40% | 0.71 | 3.55 | 2.84 | 0.97 | 0.39 | 17.8 |

For comparison, the DOC API sample for 2018–19 (367 stories) is 21% statistics/policy, 47% non-violent and 32% violent.

1. **The 2021–22 spike was mostly statistics and policy stories.** Statistics/policy stories went from 0.65 to 17 per 1M monitored articles, 26× the pre-COVID level. They made up 72% of distinct 2021 stories, against 15–30% before COVID. Typical headlines: FAA referral counts, fine totals, no-fly-list proposals, union statements, "incidents are soaring".
2. **Incident coverage rose far less than reports did.** Per passenger flown, non-violent incident stories were flat in 2021 (0.66 vs 0.67) and below baseline in 2022–25. Violent incident stories rose about 1.5× in 2021 and 1.1× in 2022, while FAA reports per passenger rose 5.6× and 1.8×. The pre-COVID base has only 7 violent stories, so the 1.5× has wide error bars, roughly ±2× on a Poisson basis. It is still nowhere near 5.6×.
3. **Masks barely appear in headlines.** About 72% of 2021 FAA reports were mask-related, but only 6% of 2021 stories mention masks (4% of non-violent incident stories). The mask-refusal reports that drove the count were mostly never covered as individual stories. They reached the news in aggregate, as statistics.
4. **This matches the severe-end series.** Federal sentencings under USSG §2A5.2 (interference with a flight crew) were 16–27 a year in FY2017–2023 and 28–29 in FY2024–25 (`raw/severe/ussc_2A5_2.csv`). TRAC § 46504 lead-charge prosecutions were 18–28 a year in FY2011–2024. FY2025 shows 48, a real uptick worth watching, but it arrives three years after the spike (`raw/severe/trac_lead_charge_snapshots.csv`). Violent-incident coverage per passenger, sentencings and prosecutions all moved within about 1–1.5× of baseline through 2021–22, while reports moved 5.6×. The evidence points to a surge in reporting and in aggregate attention, not a matching surge in violent misconduct.
5. **2026 looks different, but it is a few stories.** The violent share is 40% and violent stories per passenger are 1.8× baseline, without any rise in FAA reports. Twenty distinct stories, several heavily syndicated (a cockpit-breach diversion, a "threaten to take over the plane" grounding, a duct-tape restraint), drive this. Copy-weighted volume (`vol_*` columns) exaggerates it further because of iHeart reposts. It is consistent with the news-coverage finding above that 2026 coverage spikes are a handful of viral incidents.

Caveats:
- GKG matches on headlines, while the DOC API matched full text. The two samples agree on violent share where they overlap (Oct 2019–Mar 2020: 21% vs 25%), but the headline sample has fewer statistics/policy pieces (15% vs 30%). So the 2018–19 API numbers are a baseline for shares only, not for rates.
- The US filter is by domain and imperfect. A few US-outlet stories are about foreign flights (e.g. IndiGo, Shannon).
- The 1-in-4 file sample and small annual story counts (12–25 violent stories a year) make single-year rates noisy. Read the series for multiples of 3× or more, not 20% moves.
- Haiku labels headlines only. A story whose headline says "diverted" may involve violence described in the body, which biases the violent counts down evenly across years.

Reproduce: `python gkg_titles.py raw/gkg_titles 201910 202609 48`, then `python prep_gkg_batches.py <dir>` (writes batches for Haiku), then `python gkg_headline_types.py raw/haiku_labels/gkg`. For the API sample, run `python headline_types.py raw/haiku_labels/api`. The labeling rubric is in `raw/haiku_labels/rubric.md`.
