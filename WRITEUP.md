# Did ChatGPT Affect Baby Naming? A Diff-in-Diff Analysis

## Research Question

Did ChatGPT influence baby naming trends after its November 2022 launch? We test whether names that ChatGPT recommends grew disproportionately in 2024 compared to names it does not recommend, after controlling for pre-existing trends.

## Data

### ChatGPT Name Recommendations

We queried OpenAI language models via the OpenRouter API to collect baby name recommendations. We used three models:

| Model | Queries | Unique Names | Total Mentions |
|-------|---------|--------------|----------------|
| GPT-3.5-turbo | 1,440 | 604 | 15,767 |
| GPT-4 | 190 | 1,119 | 5,820 |
| GPT-4-turbo | 420 | 1,093 | 10,451 |
| **Combined** | **2,050** | **1,874** | **32,038** |

Each query used one of 24 prompts designed to mimic how users ask for baby name suggestions (e.g., "Suggest 10 baby names for a boy", "What are some unique baby names?", "What baby names are trending?"). We ran each prompt multiple times with temperature=0.8 to capture variation in recommendations.

### Model Agreement

The three models show moderate overlap in which names they recommend:

| Comparison | Shared Names | Jaccard Similarity |
|------------|--------------|-------------------|
| GPT-3.5 vs GPT-4 | 408 | 31% |
| GPT-3.5 vs GPT-4-turbo | 342 | 25% |
| GPT-4 vs GPT-4-turbo | 490 | 29% |

However, among names recommended by multiple models, the frequency correlation is high (r = 0.82-0.84), suggesting models agree on *how often* to recommend shared names even if they differ on which names to include.

298 names appear in all three models; 1,874 unique names appear in at least one.

### SSA Baby Name Data

We obtained baby name counts from the Social Security Administration:
- **National data**: 322,468 name-year observations covering 52,958 unique names from 2015-2024

Names with fewer than 5 occurrences per year are excluded by SSA for privacy.

## Empirical Strategy

### The Identification Problem

A naive comparison of ChatGPT-recommended names vs. non-recommended names is confounded by selection: ChatGPT tends to recommend names that are already popular or trending. If recommended names grew faster in 2024, this could reflect either:

1. **Causal effect**: ChatGPT influenced parents' naming decisions
2. **Selection**: ChatGPT recommends names that were already on upward trajectories

### Excess Recommendation

To address selection on *levels*, we construct an "excess recommendation" measure. Among names that ChatGPT recommends, we regress log(recommendation frequency) on log(pre-period popularity):

```
log(chatgpt_freq) = 0.055 + 0.320 × log(pre_popularity)
```

The residual from this regression captures names that ChatGPT recommends *more than expected* given their baseline popularity. A name with high excess recommendation is one that ChatGPT favors disproportionately—the "ChatGPT discovery" effect.

### Controlling for Pre-Trends

To address selection on *trends*, we compute each name's linear growth rate over 2015-2022 (pre-ChatGPT) and include it as a control. This asks: among names with similar pre-existing trajectories, did the ones ChatGPT favors grow faster in 2024?

Importantly, excess recommendation is nearly uncorrelated with pre-trend (r = 0.025), suggesting these capture different dimensions of selection.

### Specification

Our main specification:

```
log(count_it) = α_i + γ_t + β₁(ExcessRec_i × Post_t) + β₂(PreTrend_i × Post_t) + ε_it
```

Where:
- `α_i` = name fixed effects
- `γ_t` = year fixed effects
- `ExcessRec_i` = standardized excess recommendation (0 for non-recommended names)
- `PreTrend_i` = standardized pre-period growth rate (2015-2022)
- `Post_t` = indicator for 2024
- `β₁` = **coefficient of interest**

Standard errors are clustered by name.

## Results

### Pre-Trend Analysis

We first examine whether ChatGPT-recommended names (binary) were on differential trends before ChatGPT existed:

| Year | Coefficient | t-stat | |
|------|-------------|--------|---|
| 2015 | -14.4% | -7.41 | *** |
| 2016 | -11.1% | -5.86 | *** |
| 2017 | -7.3% | -4.28 | *** |
| 2018 | +0.6% | 0.38 | |
| 2019 | +2.3% | 1.44 | |
| 2020 | +1.4% | 0.82 | |
| 2021 | +6.9% | 4.60 | *** |
| 2022 | (ref) | — | |
| 2023 | +5.6% | 3.20 | *** |
| 2024 | +9.1% | 5.54 | *** |

ChatGPT-recommended names were on a clear upward trajectory *before* ChatGPT launched, rising from -14% (2015) to +7% (2021) relative to 2022. This invalidates naive binary DiD estimates.

### Main Results

| Specification | Coefficient | SE | t-stat | p-value |
|---------------|-------------|------|--------|---------|
| Excess recommendation (no controls) | +2.54% | 0.017 | 1.53 | 0.126 |
| Excess recommendation (controlling for pre-trend) | +2.25% | 0.017 | 1.36 | 0.175 |
| Pre-trend | +16.32% | 0.004 | 43.01 | <0.001 |

Interpretation:
- **Pre-trend** is massively predictive of 2024 outcomes. Names that were growing before ChatGPT continued growing after.
- **Excess recommendation** shows a positive but statistically insignificant effect. A 1 SD increase in excess ChatGPT recommendation is associated with ~2.3% higher baby counts in 2024, but we cannot distinguish this from noise (p = 0.175).

### Binary Treatment (For Comparison)

| Specification | Coefficient | SE | t-stat | p-value |
|---------------|-------------|------|--------|---------|
| Binary (recommended by any model) | +9.1% | 0.016 | 5.54 | <0.001 |

The binary effect is highly significant but confounded by pre-trends. ChatGPT-recommended names grew 9% more in 2024, but they were already growing faster before ChatGPT existed.

## Interpretation

We find **no statistically significant evidence** that ChatGPT influenced baby naming after accounting for pre-existing trends.

The point estimate is positive (+2.3% per SD of excess recommendation) and economically meaningful, but the standard error is too large to reject the null hypothesis of no effect. This could reflect:

1. **True null**: ChatGPT did not meaningfully influence baby naming
2. **Underpowered**: The effect exists but is too small to detect with our sample
3. **Measurement error**: Our proxy for "ChatGPT recommendation" is noisy

The highly significant binary result (+9.1%) is misleading—it reflects ChatGPT's tendency to recommend already-trending names rather than a causal effect on naming.

## Limitations

1. **Selection on unobservables**: We control for linear pre-trends, but names may differ on higher-order dynamics (acceleration, seasonality) that correlate with both ChatGPT recommendation and future growth.

2. **Measurement of treatment**: We observe what ChatGPT recommends *today*, not what it recommended in 2023 when parents were choosing names. Model behavior may have drifted.

3. **Mechanism**: Even if we found an effect, we could not distinguish direct influence (parents asking ChatGPT) from indirect influence (ChatGPT reflecting cultural trends that independently affect naming).

4. **External validity**: We query ChatGPT in English with US-centric prompts. Effects may differ for non-English names or other countries.

## Conclusion

Despite ChatGPT's widespread adoption, we find no statistically significant evidence that it influenced baby naming trends in 2024. ChatGPT-recommended names did grow faster than non-recommended names, but this appears to reflect selection—ChatGPT recommends names that were already on upward trajectories—rather than a causal effect of the technology.

The null result is informative: it suggests that either (1) few parents actually use ChatGPT for baby naming, (2) ChatGPT's recommendations are too generic to shift aggregate trends, or (3) parents who consult ChatGPT would have chosen similar names anyway.

## Data and Code

**ChatGPT queries**: Collected via OpenRouter API (openrouter.ai)
- `scripts/query_openrouter.py` - Query script

**SSA data**: https://www.ssa.gov/oact/babynames/names.zip
- `scripts/download_ssa.py` - Processing script

**Analysis**:
- `scripts/combine_and_analyze.py` - Main analysis
- `data/processed/` - Cleaned datasets
