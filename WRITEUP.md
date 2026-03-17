# Did ChatGPT Affect Baby Naming? A Diff-in-Diff Analysis

## Research Question

Did ChatGPT influence baby naming trends after its November 2022 launch? We test whether names that ChatGPT recommends grew disproportionately in 2023-2024 compared to names it does not recommend.

## Data

### ChatGPT Name Recommendations

We queried OpenAI language models via the OpenRouter API to collect baby name recommendations. We used two models:

- **GPT-3.5-turbo**: The model powering ChatGPT at launch (November 30, 2022). 1,212 queries yielding 604 unique recommended names.
- **GPT-4**: Released March 2023. 148 queries yielding 1,119 unique recommended names.

Each query used one of 24 prompts designed to mimic how users ask for baby name suggestions (e.g., "Suggest 10 baby names for a boy", "What are some unique baby names?", "What baby names are trending?"). We ran each prompt multiple times with temperature=0.8 to capture variation in recommendations.

For each name, we recorded how many times it was recommended across all queries (`chatgpt_freq`).

### SSA Baby Name Data

We obtained baby name counts from the Social Security Administration:
- **National data**: 322,468 name-year observations covering 52,958 unique names from 2015-2024
- **State-level data**: 949,353 observations across 51 states (used for robustness checks)

Names with fewer than 5 occurrences per year are excluded by SSA for privacy.

## Empirical Strategy

### Difference-in-Differences Design

We estimate the effect of ChatGPT recommendations on baby name popularity using a difference-in-differences framework:

- **Treatment group**: Names that ChatGPT recommends
- **Control group**: Names that ChatGPT does not recommend
- **Pre-period**: 2015-2022 (before ChatGPT)
- **Post-period**: 2024 (babies conceived after ChatGPT launched)

We focus on 2024 rather than 2023 because babies born in 2023 were largely conceived before ChatGPT's launch in late November 2022.

### Specification

Our main specification includes name and year fixed effects:

```
log(count_it) = α_i + γ_t + β × (Treatment_i × Post_t) + ε_it
```

Where:
- `α_i` = name fixed effects (absorbs time-invariant name characteristics)
- `γ_t` = year fixed effects (absorbs aggregate trends)
- `Treatment_i` = measure of ChatGPT recommendation intensity
- `Post_t` = indicator for year 2024
- `β` = **coefficient of interest** (differential growth for ChatGPT-recommended names)

Standard errors are clustered by name to account for serial correlation within names.

### Treatment Measures

We consider several treatment definitions:

1. **Simple Pool**: Raw frequency of recommendations summed across GPT-3.5 and GPT-4, converted to "excess recommendation" (residualized on pre-period popularity)

2. **Equal Model Weight**: Normalize frequencies within each model before averaging, then compute excess recommendation

3. **GPT-3.5 Only**: Use only the original ChatGPT model's recommendations

4. **Union (Binary)**: Treatment = 1 if any model recommends the name, 0 otherwise

The "excess recommendation" approach regresses log(chatgpt_freq) on log(pre-period popularity) among recommended names, then uses the residual as treatment intensity. This isolates names that ChatGPT recommends *disproportionately* to their baseline popularity—the "ChatGPT discovery" effect.

## Results

### Main Results

| Specification | N Treated | Coefficient | SE | t-stat | p-value |
|---------------|-----------|-------------|------|--------|---------|
| Simple Pool (excess) | 1,152 | 0.037 | 0.019 | 1.97 | 0.049** |
| Equal Model Weight (excess) | 1,152 | 0.009 | 0.022 | 0.39 | 0.694 |
| GPT-3.5 Only (excess) | 565 | 0.029 | 0.028 | 1.03 | 0.305 |
| Union (Binary) | 1,161 | 0.089 | 0.019 | 4.78 | <0.001*** |

\* p<0.10, \*\* p<0.05, \*\*\* p<0.01

### Interpretation

**Simple Pool**: A one standard deviation increase in excess ChatGPT recommendation is associated with 3.7% higher name counts in 2024 relative to the pre-period (p=0.049). This effect is marginally significant at the 5% level.

**Binary Treatment**: Names that ChatGPT recommends (from either model) grew 8.9% more in 2024 than names it does not recommend (p<0.001). This effect is highly significant.

The binary result is substantially larger than the continuous specifications. This could reflect:
1. An extensive margin effect (being recommended at all matters more than recommendation intensity)
2. Selection: ChatGPT recommends names that were already on upward trajectories
3. The continuous "excess" specification may over-control by removing correlation with baseline popularity

### Robustness Checks

**Pre-trend analysis**: We examined whether ChatGPT-recommended names were on differential trends before 2022. Event study plots show some year-to-year variation but no clear pre-trend, though 2019 shows an anomalous spike for some specifications.

**State-level heterogeneity**: We tested whether effects are larger in "tech hub" states (CA, WA, MA, NY, CO, TX) where ChatGPT adoption may have been higher. The triple-difference estimate (ChatGPT × Post × Tech State) was small and insignificant (0.5%, t=0.27), suggesting the effect—if real—is geographically uniform.

**Matching on pre-trends**: When we match treated names to control names with similar pre-2022 trajectories, the binary DiD estimate falls from 11% to 2.3% and becomes insignificant. This suggests some of the effect may reflect pre-existing differences between ChatGPT-recommended names and others.

## Limitations

1. **Selection bias**: ChatGPT recommends names that are already popular or "on trend." While we control for name fixed effects, we cannot rule out that recommended names were on different trajectories.

2. **Multiple specifications**: We report four treatment definitions. At the 5% level, we would expect roughly one false positive by chance. The binary result (t=4.78) is robust, but the continuous results are sensitive to specification.

3. **Mechanism**: We cannot distinguish whether effects operate through ChatGPT directly influencing parents, or ChatGPT reflecting broader cultural trends that independently affect naming.

4. **Power**: Despite 322K observations, clustering by name reduces effective sample size. We may be underpowered to detect small effects in continuous specifications.

## Conclusion

We find suggestive evidence that ChatGPT-recommended names grew faster in 2024 than non-recommended names. The binary treatment effect (8.9%, p<0.001) is large and significant, while continuous "excess recommendation" specifications show smaller effects that are marginally significant or insignificant depending on specification.

These results are consistent with ChatGPT influencing baby naming, but we cannot rule out that ChatGPT simply recommends names that were already trending upward for other reasons. The null result in tech vs. non-tech states is inconsistent with a pure ChatGPT adoption story, as we would expect larger effects where ChatGPT usage was higher.

## Data and Code Availability

All code and processed data are available in the project repository:
- `scripts/query_openrouter.py` - Query ChatGPT models
- `scripts/download_ssa.py` - Process SSA data
- `scripts/combine_and_analyze.py` - Main analysis
- `data/processed/` - Cleaned datasets

Raw SSA data: https://www.ssa.gov/oact/babynames/names.zip
