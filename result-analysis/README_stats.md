# Statistical Analysis — VodaCare A/B Study

## Overview

This script computes formal statistical tests for the VodaCare dissertation from the summary statistics reported in Section 5. It produces Welch's t-tests, Cohen's d effect sizes, 95% confidence intervals, chi-squared tests, and Fisher's exact tests.

## Requirements

```bash
pip install numpy scipy
```

## Usage

```bash
# Print results to console
python statistical_analysis.py

# Save console output to a text file
python statistical_analysis.py --output results.txt

# Export structured results to CSV (for tables/charts)
python statistical_analysis.py --csv results.csv

# Both
python statistical_analysis.py --output results.txt --csv results.csv
```

## What It Computes

| Section | Test | Data Source |
|---------|------|-------------|
| Human self-ratings (1–5) | Welch's t-test, Cohen's d, 95% CI | Table 5 |
| Human LAJ scores (0–1) | Welch's t-test, Cohen's d, 95% CI | Table 4 |
| Simulation LAJ scores (0–1) | Welch's t-test, Cohen's d, 95% CI | Table 2 |
| Behavioural telemetry | Welch's t-test, Cohen's d | Table 9 |
| Simulation outcomes | χ² (Yates), Fisher's exact | Table 3 |
| Multiple comparisons | Bonferroni correction | All t-tests |

## ⚠️ Important: Estimated Standard Deviations

The script currently uses **estimated SDs** derived from the reported rating distributions (Figures 5–6) and domain-typical variance for Likert/rubric scales. These are conservative estimates.

**To use actual SDs from your raw data:**

1. Open `statistical_analysis.py`
2. Find the configuration section at the top (lines ~30–70)
3. Replace the `"sA"` and `"sB"` values with SDs computed from your Supabase data
4. Re-run the script

For example, if your raw empathy self-ratings have SD = 0.65 for Group A and SD = 0.95 for Group B:

```python
"Empathy": {"mA": 4.50, "mB": 3.90, "sA": 0.65, "sB": 0.95},
```

## Key Results (with estimated SDs)

- **Empathy** is statistically significant across all three evaluation methods, surviving Bonferroni correction for the LAJ measures
- **Session duration** and **typing duration per turn** show significant behavioural differences
- **Critical failure rate** (5% vs 18%) is significant by Fisher's exact test (p = .007)
- **Task success**, **clarity**, and **overall satisfaction** show no significant differences — consistent with the "scenario-driven, not variant-driven" finding

## Integrating into the Dissertation

The suggested placement is a new subsection **5.1.1 Statistical Methods** or as additions to each existing results subsection. The Bonferroni correction note fits well in Section 5.4 (Three-Way Convergence) to strengthen the triangulation argument.
