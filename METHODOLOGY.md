# ChatGPT Baby Names Study - Methodology

## Research Question
Did ChatGPT influence baby naming trends after its November 2022 launch?

## Data Sources

### 1. ChatGPT Name Recommendations
- **Source**: OpenRouter API (provides access to historical OpenAI models)
- **Models queried**:
  - `gpt-3.5-turbo` (Original ChatGPT, Nov 30, 2022)
  - `gpt-4` (ChatGPT Plus, Mar 14, 2023)
  - `gpt-4-turbo` (Nov 6, 2023)
  - `gpt-4o` (May 13, 2024)

### 2. Baby Name Counts
- **Source**: Social Security Administration (SSA)
- **National data**: https://www.ssa.gov/oact/babynames/names.zip
- **State-level data**: https://www.ssa.gov/oact/babynames/state/namesbystate.zip
- **Years**: 2015-2024

## Data Collection

### ChatGPT Queries
Run queries using OpenRouter API:

```bash
cd C:\Users\Owner\chatgpt_names_study

# Set API key
set OPENROUTER_API_KEY=your-key-here

# Query a single model (85 iterations = 2040 queries)
python scripts/query_openrouter.py -n 85 -m gpt-3.5-turbo --api-key YOUR_KEY

# Query all models
python scripts/query_openrouter.py -n 85 --all-models --api-key YOUR_KEY
```

**Prompts used** (24 prompts, each run multiple times with temperature=0.8):
- "Suggest 10 baby names for a boy"
- "Suggest 10 baby names for a girl"
- "What are good baby names?"
- "I need help choosing a baby name"
- "What are some unique baby names?"
- "What are classic baby names?"
- "Suggest modern baby names"
- "What are traditional baby names?"
- "Suggest trendy baby names for 2023"
- "What are timeless baby names?"
- "What are popular boy names?"
- "What are popular girl names?"
- "Suggest unique boy names"
- "Suggest unique girl names"
- "What are strong names for a boy?"
- "What are elegant names for a girl?"
- "Suggest American baby names"
- "What are English baby names?"
- "Suggest biblical baby names"
- "What are nature-inspired baby names?"
- "Give me a list of baby names"
- "What baby names are trending?"
- "What are the best baby names?"
- "Recommend some baby names for my child"

**Output**:
- `data/raw/chatgpt_responses_{model}.jsonl` - Raw responses
- `data/processed/chatgpt_names_{model}.csv` - Name frequencies

### SSA Data Processing
```bash
# Download and process SSA data
python scripts/download_ssa.py
```

**Output**:
- `data/processed/ssa_names_panel.csv` - Panel data (name × year × count)
- `data/processed/ssa_names_summary.csv` - Summary statistics

### Merge Data
```bash
python scripts/merge_data.py
```

**Output**:
- `data/analysis_ready.csv` - Final dataset for analysis

## Variables

| Variable | Description |
|----------|-------------|
| `name` | Baby name |
| `year` | Birth year |
| `count` | Number of babies with this name |
| `sex` | M or F |
| `treated` | 1 if ChatGPT recommended this name |
| `chatgpt_freq` | How many times ChatGPT recommended this name |
| `post` | 1 if year >= 2023 |
| `treated_x_post` | Interaction term for DiD |
| `log_count` | log(count) |

## Identification Strategy

### Diff-in-Diff with Continuous Treatment
- **Treatment intensity**: `chatgpt_freq` (how often ChatGPT recommends the name)
- **Pre-period**: 2015-2022
- **Post-period**: 2023-2024
- **Fixed effects**: Name FE + Year FE
- **Clustering**: Standard errors clustered by name

### Regression Specification
```
log(count) = alpha_i + gamma_t + beta * (chatgpt_freq * post) + epsilon
```

Where:
- `alpha_i` = name fixed effects
- `gamma_t` = year fixed effects
- `beta` = effect of ChatGPT recommendation intensity

## Reproducibility

### Requirements
- Python 3.10+
- pandas, numpy, requests, scipy

### Full Pipeline
```bash
# 1. Set up
cd C:\Users\Owner\chatgpt_names_study
pip install pandas numpy requests scipy

# 2. Query ChatGPT (takes ~17 min per model)
python scripts/query_openrouter.py -n 85 --all-models --api-key YOUR_KEY

# 3. Download SSA data (manual: download from SSA website)
# Place names.zip in data/raw/
python scripts/download_ssa.py --skip-download

# 4. Merge
python scripts/merge_data.py

# 5. Analysis
python scripts/did_intensity.py
python scripts/did_matched.py
```

## File Structure
```
chatgpt_names_study/
├── scripts/
│   ├── query_openrouter.py    # Query ChatGPT via OpenRouter
│   ├── download_ssa.py        # Download/process SSA data
│   ├── merge_data.py          # Merge datasets
│   ├── quick_did.py           # Basic DiD analysis
│   ├── did_matched.py         # DiD with pre-trend matching
│   └── did_intensity.py       # DiD with continuous treatment
├── data/
│   ├── raw/                   # Raw data files
│   └── processed/             # Processed data files
├── output/                    # Results and figures
└── METHODOLOGY.md             # This file
```
