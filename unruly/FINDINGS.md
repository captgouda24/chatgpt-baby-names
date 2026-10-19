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

## What kind of stories made up the coverage spike? (broad headline filter)

The question: was the 2021–22 coverage spike mostly statistics and policy stories, plus minor incidents that once went unreported? Or did coverage of violent incidents rise too?

> **Supersedes an earlier version of this section.** That version matched only headlines containing "unruly/disruptive passenger" or "air rage". Incident stories often don't use those words ("Passenger punches flight attendant"), especially before 2021, so it missed most pre-COVID incident coverage. For example, it found 2 incident stories in Feb 2020, while the broad filter finds 15 distinct incidents (including ones where Haiku could not tell whether the flight was US). It also had a per-passenger normalization bug: the 6-month baseline was divided by total passengers in the period, not monthly passengers. That understated per-passenger rises by about 2×. Both scripts are fixed. The narrow-filter outputs (`gkg_*`) are kept for reference.

### Data and method

1. **Headlines.** `gkg_titles.py --broad` reads the :00 GDELT GKG file of every hour from Oct 2019 to Sep 2026. Page titles only exist in GKG from Oct 2019. That is 84 months and about 85M articles with a title. It keeps any headline with a misconduct word plus an aviation, passenger or crew word, about 22,500 a month (`raw/gkg_titles_broad/`).
2. **Filter.** `prep_broad_batches.py` keeps a headline that either:
   - matches the old phrase filter, or
   - has a misconduct word plus a crew word, or a passenger or person word together with a flight, plane or airline word.

   It drops ground transport, keeps US outlets (by domain), and collapses copies of the same headline within a month. That leaves 9,331 stories (22,544 headlines).
3. **Labels** (Claude Haiku, one calendar month per batch, rubric `raw/haiku_labels/rubric_v2.md`):
   - story type: statistics/policy, violent incident, non-violent incident, other
   - mask flag
   - US flight flag
   - **event code**, so that rewrites of the same incident count once
4. **Two second passes:**
   - Policy stories are split into misconduct coverage vs mask/vaccine/alcohol-service announcements (`rubric_v2_policy_split.md`). Health-rule announcements, mostly 2020–22, are excluded from the misconduct counts.
   - Every headline labeled violent or policy is re-checked with one narrow yes/no question (`rubric_v2_violent_verify.md`). 631 of 2,570 "violent" headlines were downgraded, and 63 policy headlines turned out to be specific violent incidents. An event counts as violent only if a confirmed headline belongs to it.
5. **Hand checks**, on 60 random first-pass labels:
   - Overall agreement was 77%: non-violent 19/20, violent 13/20, policy 6/10, other 8/10.
   - "Violent" was over-applied: "disruptive passenger met by police", "verbal assault", a door failing mid-air.
   - The verification pass agreed with my judgment on 29 of the 30 violence calls in that sample.
6. **Measures.**
   - Distinct US incidents (events) per 1M GKG articles with a title. Misconduct statistics/policy stories are counted per 1M as well.
   - Intervals are 95% month-block bootstraps of each period's ratio to Oct 2019–Mar 2020. Poisson intervals are in `broad_ratios.csv` and are similar.
   - Drift check: the filter also catches off-topic headlines (crashes, strikes, airline business). Their rate per 1M is a placebo for changes in GDELT's source panel. "Drift-adjusted" divides by that ratio.

Outputs: `broad_stories_labeled.csv`, `broad_quarterly.csv`, `broad_annual.csv`, `broad_ratios.csv`, `broad_types.png`.

### Results

US incidents (events) and misconduct statistics/policy stories, per 1M monitored articles:

| Period | Stats/policy stories | Non-violent incidents | Violent incidents | Violent vs base (95% CI) | Violent, drift-adjusted | FAA reports per 10M pax |
|---|---|---|---|---|---|---|
| Oct 2019–Mar 2020 (base) | 0.13 | 4.0 | 2.2 (17 events) | 1 | 1 | 16.1 |
| Apr–Dec 2020 | 5.5 (+7.8 mask-rule) | 4.9 | 1.7 | 0.8 (0.3–1.5) | 1.2 | 35.1 |
| 2021 | **21.8** | 7.2 | 7.3 | **3.3 (2.1–5.4)** | 4.1 | **89.7** |
| 2022 | 8.5 | 7.6 | 7.0 | 3.2 (1.9–5.3) | 3.2 | 28.8 |
| 2023 | 3.7 | 6.0 | 5.6 | 2.5 (1.6–4.0) | 2.3 | 22.1 |
| 2024 | 1.5 | 5.2 | 5.1 | 2.3 (1.6–3.6) | 1.4 | 21.4 |
| 2025 | 0.2 | 4.4 | 7.9 | 3.6 (2.3–5.6) | 3.0 | 16.7 |
| 2026 (Jan–Sep) | 1.9 | 4.4 | 5.8 | 2.6 (1.8–4.2) | 1.6 | 17.8 (Jan–Jun) |

Same calendar window each year (Oct–Mar), which removes seasonality and the partial-year problem:

| Oct–Mar | Violent incidents | per 1M articles | per 100M passengers | Off-topic stories per 1M (drift) | FAA reports per 10M pax |
|---|---|---|---|---|---|
| 2019–20 | 17 | 2.2 | 4.2 | 46 | 16.1 |
| 2020–21 | 20 | 3.7 | 10.8 | 27 | 93.8 |
| 2021–22 | 34 | 6.3 | 9.0 | 39 | 65.5 |
| 2022–23 | 28 | 5.8 | 6.5 | 57 | 20.1 |
| 2023–24 | 39 | 6.0 | 8.4 | 76 | 21.4 |
| 2024–25 | 31 | 5.4 | 6.7 | 60 | 19.0 |
| 2025–26 | 31 | 6.1 | 6.7 | 56 | 17.1 |

1. **The 2021–22 spike was mostly statistics and policy stories.**
   - Misconduct statistics/policy stories went from almost none before COVID to 21.8 per 1M in 2021. They were 60% of all misconduct items that year.
   - Typical headlines: FAA referral and fine totals, "incidents soar", no-fly-list bills, union statements, alcohol-to-go requests.
   - Mask-requirement announcements were another large block in 2020–22 and are counted separately.
   - The statistics/policy share fell back to 2–15% by 2025–26.
2. **Non-violent incident coverage rose modestly and then returned to baseline.**
   - It rose 1.8–1.9× in 2021–22 (CIs 1.3–2.9), while FAA reports rose 5.6× and 1.8×.
   - By 2024–26 it was about 1.1–1.3×, with CIs that include 1.
   - Mask refusals, which were 72% of 2021 FAA reports, mostly never became individual stories.
3. **Violent incident coverage rose about 3× in 2021 and has not come back down.**
   - It was 3.3× in 2021 and 2.3–3.6× in every year since, with every interval above 1.
   - The season-matched windows show the same thing: about 2.5–3× per article and 1.6–2× per passenger, every winter since 2021.
   - Over the same years FAA reports per passenger fell back to 1.0–1.3×.
   - Correcting for source-panel drift shrinks the late years (1.4× in 2024, 1.6× in 2026) but not 2021–23 or 2025.
4. **This is not one viral video being re-run.**
   - Distinct stories per violent incident were 4.9 before COVID and 3.4–5.4 since.
   - Syndicated copies per violent incident fell, from 22 to 9–14.
   - The rise is in the number of distinct violent incidents covered, not in pile-ons around a few videos.
5. **Severe-end comparison.**
   - Federal sentencings under USSG §2A5.2 averaged 21.5 a year in FY2019–20 and 28–29 in FY2024–25, about 1.3× (`raw/severe/ussc_2A5_2.csv`).
   - TRAC § 46504 lead-charge prosecutions were 18–28 a year through FY2024, then 48 in FY2025 (`raw/severe/trac_lead_charge_snapshots.csv`).
   - So the severe end has also drifted up a little since 2021, about 1.3–2×, though less than violent-incident coverage.

**Interpretation.**
- The 2021 surge in reports is mostly policy and recording, as the sections above find. News coverage tracked it mainly through statistics stories, not through more incident stories.
- Violent incidents are different. Their coverage per article has stayed about 2.5–3× its pre-COVID level since 2021, and the federal severe-end series are also somewhat higher in the latest years.
- That is consistent with two explanations, and probably some of both:
  - **More attention:** "air rage" became an established story genre, and filmed incidents are easier to report.
  - **A modest real increase** in the most serious incidents, on the order of the 1.3–2× seen in sentencings and prosecutions.
- FAA's totals can't settle it, because they don't separate violent cases.
- What the data does rule out is a 5× rise in serious misconduct in 2021 like the jump in reports.

Caveats:
- The baseline is short, 6 months with 17 violent incidents, and GKG has no headlines before Oct 2019. Intervals reflect this but are wide.
- Labels come from headlines only; a story whose headline says "diverted" may involve violence.
- Haiku's event codes group rewrites within a month only, so a story spanning two months, or a later sentencing story, counts again.
- The US filter (domain plus Haiku's US-flight flag) is imperfect. Results using "US or unsure" incidents are in `broad_annual.csv` (`*_incl_unsure`) and show the same pattern.
- The drift placebo includes COVID-era airline news (crashes, strikes, quarantines), so it is a rough correction.

Reproduce:
1. `python gkg_titles.py raw/gkg_titles_broad 201910 202609 48 --broad`
2. `python prep_broad_batches.py raw/gkg_titles_broad <dir>` (writes monthly batches for Haiku, rubric v2)
3. The policy-split and violent-verify passes (rubrics in `raw/haiku_labels/`)
4. `python broad_types.py raw/haiku_labels/broad raw/haiku_labels/broad_policy_split raw/haiku_labels/broad_violent_verify`

The narrow-filter version: `python gkg_headline_types.py raw/haiku_labels/gkg`. The 2018–20 DOC-API sample: `python headline_types.py raw/haiku_labels/api`.
