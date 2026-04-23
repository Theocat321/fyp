# Statistical Analysis — VodaCare A/B Study

Formal tests on the 200 raw conversation records (`exp_A*.json`, `exp_B*.json`). All computed from actual data.

## Usage

```bash
python statistical_analysis.py
python statistical_analysis.py --exp-a path/to/exp_A.json --exp-b path/to/exp_B.json
python statistical_analysis.py --csv results.csv --output results.txt
```

Requires `numpy` and `scipy`.

## Tests

Mann-Whitney U (primary — non-normal per Shapiro-Wilk), Welch's t-test (backup), Cohen's d, bootstrap 95% CI (10k resamples), chi-squared / Fisher's exact (categorical), Wilcoxon signed-rank (paired per-persona), Bonferroni correction (α = .007).

## Results

| Finding | Statistic | p | Effect |
|---|---|---|---|
| Empathy A > B | d = 1.89, U = 9032 | < .001 | Large |
| Overall score A > B | d = 0.44, U = 6234 | .003 | Small |
| Critical failure A < B | OR = 0.09, 2% vs 18% | < .001 | — |
| Task success | d = 0.06 | .45 | Negligible |
| Clarity | d = −0.03 | .98 | Negligible |

Empathy and overall survive Bonferroni. Task success and clarity — no difference.
