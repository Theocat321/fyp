# Statistical Analysis — VodaCare A/B Study

## Overview

Computes formal statistical tests from the raw per-conversation experiment data (`exp_A*.json`, `exp_B*.json`). No estimated standard deviations — everything is computed directly from the 200 individual conversation records.

## Requirements

```bash
pip install numpy scipy
```

## Usage

```bash
# Print results to console
python statistical_analysis.py

# Custom file paths
python statistical_analysis.py \
    --exp-a path/to/exp_A.json \
    --exp-b path/to/exp_B.json

# Export results
python statistical_analysis.py --csv results.csv --output results.txt
```

## Tests Computed

| Test | What it answers | Why this test |
|------|----------------|---------------|
| Mann-Whitney U | Are the score distributions different? | Non-parametric; appropriate since Shapiro-Wilk confirms non-normality |
| Welch's t-test | Are the means different? | Parametric backup; robust to unequal variance |
| Cohen's d | How large is the effect? | Standardised effect size for cross-study comparison |
| Bootstrap 95% CI | Plausible range for the true difference | Distribution-free; 10,000 resamples |
| Chi-squared / Fisher's exact | Do categorical outcomes differ? | Critical failure rates, termination distributions |
| Wilcoxon signed-rank | Do paired persona/scenario means differ? | Controls for persona difficulty; each persona is its own control |
| Bonferroni correction | Which findings survive multiple testing? | Conservative correction across all metric tests |

## Key Results

| Finding | Statistic | p-value | Effect |
|---------|-----------|---------|--------|
| **Empathy (A > B)** | d = 1.89, U = 9032 | p < .001 | Large |
| **Overall score (A > B)** | d = 0.44, U = 6234 | p = .003 | Small |
| **Critical failure (A < B)** | OR = 0.09, 2% vs 18% | p < .001 | — |
| Task success | d = 0.06 | p = .45 | Negligible |
| Clarity | d = −0.03 | p = .98 | Negligible |

Empathy and overall score survive Bonferroni correction (α = .007). Task success and clarity show no difference.

## Shapiro-Wilk Results

All score distributions are significantly non-normal (p < .05), confirming that Mann-Whitney U is the appropriate primary test. Welch's t-test is reported alongside for completeness.
