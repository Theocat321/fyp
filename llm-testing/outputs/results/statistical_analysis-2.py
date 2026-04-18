"""
Statistical Analysis for VodaCare A/B Study
============================================
Computes statistical tests from ACTUAL per-conversation data extracted
from the experiment JSON files.

Tests included:
  - Mann-Whitney U (non-parametric, appropriate for non-normal score distributions)
  - Welch's t-test (parametric comparison)
  - Cohen's d effect sizes with 95% confidence intervals
  - Chi-squared and Fisher's exact tests for categorical outcomes
  - Per-persona and per-scenario paired comparisons (Wilcoxon signed-rank)
  - Bonferroni correction for multiple comparisons

Usage:
    python statistical_analysis.py
    python statistical_analysis.py --csv results.csv
    python statistical_analysis.py --output results.txt
"""

import argparse
import csv
import json
import sys
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings('ignore')


# ============================================================================
# DATA LOADING
# ============================================================================

def load_experiment(filepath):
    """Load experiment JSON and extract per-conversation scores."""
    with open(filepath) as f:
        data = json.load(f)

    records = []
    for c in data["conversations"]:
        ev = c["llm_evaluation"]
        records.append({
            "persona": c["persona_id"],
            "scenario": c["scenario_id"],
            "variant": c["variant"],
            "task_success": ev["task_success"],
            "clarity": ev["clarity"],
            "empathy": ev["empathy"],
            "policy_compliance": ev["policy_compliance"],
            "overall": ev["overall_weighted"],
            "termination": c["termination"]["reason"],
            "total_turns": c["total_turns"],
            "latency_ms": c["average_latency_ms"],
            "heuristic_pass": c["heuristic_results"]["all_passed"],
            "critical_failure": len(c["heuristic_results"]["critical_failures"]) > 0,
        })
    return records, data.get("summary", {})


# ============================================================================
# STATISTICAL FUNCTIONS
# ============================================================================

def cohens_d(x, y):
    """Cohen's d with pooled SD from raw arrays."""
    nx, ny = len(x), len(y)
    mx, my = np.mean(x), np.mean(y)
    sx, sy = np.std(x, ddof=1), np.std(y, ddof=1)
    sp = np.sqrt(((nx - 1) * sx**2 + (ny - 1) * sy**2) / (nx + ny - 2))
    return (mx - my) / sp if sp > 0 else 0.0


def effect_label(d):
    d = abs(d)
    if d < 0.2:   return "negligible"
    elif d < 0.5: return "small"
    elif d < 0.8: return "medium"
    else:         return "large"


def sig_stars(p):
    if p < 0.001:  return "***"
    elif p < 0.01: return "**"
    elif p < 0.05: return "*"
    elif p < 0.10: return "\u2020"
    else:          return ""


def ci_difference(x, y, alpha=0.05):
    """Bootstrap 95% CI for difference in means."""
    rng = np.random.default_rng(42)
    n_boot = 10000
    diffs = []
    for _ in range(n_boot):
        bx = rng.choice(x, size=len(x), replace=True)
        by = rng.choice(y, size=len(y), replace=True)
        diffs.append(np.mean(bx) - np.mean(by))
    lo = np.percentile(diffs, 100 * alpha / 2)
    hi = np.percentile(diffs, 100 * (1 - alpha / 2))
    return lo, hi


# ============================================================================
# ANALYSIS
# ============================================================================

def run_metric_tests(a_vals, b_vals, metric_name):
    """Run Mann-Whitney U and Welch's t-test on a single metric."""
    a, b = np.array(a_vals), np.array(b_vals)
    mw_stat, mw_p = stats.mannwhitneyu(a, b, alternative='two-sided')
    t_stat, t_p = stats.ttest_ind(a, b, equal_var=False)
    d = cohens_d(a, b)
    ci_lo, ci_hi = ci_difference(a, b)
    # Rank-biserial correlation (effect size for Mann-Whitney)
    n1, n2 = len(a), len(b)
    r_rb = 1 - (2 * mw_stat) / (n1 * n2)

    return {
        "metric": metric_name,
        "n_A": len(a), "n_B": len(b),
        "mean_A": np.mean(a), "sd_A": np.std(a, ddof=1),
        "mean_B": np.mean(b), "sd_B": np.std(b, ddof=1),
        "delta": np.mean(a) - np.mean(b),
        "cohens_d": d, "effect": effect_label(d),
        "ci_lo": ci_lo, "ci_hi": ci_hi,
        "mw_U": mw_stat, "mw_p": mw_p,
        "welch_t": t_stat, "welch_p": t_p,
        "r_rb": r_rb,
    }


def run_categorical_tests(a_records, b_records):
    """Chi-squared and Fisher's exact on termination outcomes."""
    results = []

    # Termination reason distribution
    reasons = ["satisfaction", "escalation", "stalemate", "patience_exceeded"]
    counts_a = [sum(1 for r in a_records if r["termination"] == reason) for reason in reasons]
    counts_b = [sum(1 for r in b_records if r["termination"] == reason) for reason in reasons]
    table = np.array([counts_a, counts_b])
    chi2, p, dof, _ = stats.chi2_contingency(table)
    results.append({
        "test": "Outcome distribution (4-category)",
        "counts_A": dict(zip(reasons, counts_a)),
        "counts_B": dict(zip(reasons, counts_b)),
        "statistic": f"χ²({dof}) = {chi2:.3f}",
        "p": p, "sig": sig_stars(p),
    })

    # Critical failure rate
    cf_a = sum(1 for r in a_records if r["critical_failure"])
    cf_b = sum(1 for r in b_records if r["critical_failure"])
    n_a, n_b = len(a_records), len(b_records)
    cf_table = np.array([[cf_a, n_a - cf_a], [cf_b, n_b - cf_b]])
    chi2_cf, p_cf, _, _ = stats.chi2_contingency(cf_table, correction=True)
    fisher = stats.fisher_exact(cf_table)
    results.append({
        "test": f"Critical failure (A:{cf_a}/{n_a} vs B:{cf_b}/{n_b})",
        "statistic": f"χ²(1,Yates) = {chi2_cf:.3f}; Fisher OR = {fisher.statistic:.3f}",
        "p": fisher.pvalue, "sig": sig_stars(fisher.pvalue),
    })

    # Heuristic pass rate
    hp_a = sum(1 for r in a_records if r["heuristic_pass"])
    hp_b = sum(1 for r in b_records if r["heuristic_pass"])
    hp_table = np.array([[hp_a, n_a - hp_a], [hp_b, n_b - hp_b]])
    chi2_hp, p_hp, _, _ = stats.chi2_contingency(hp_table, correction=True)
    fisher_hp = stats.fisher_exact(hp_table)
    results.append({
        "test": f"Heuristic pass (A:{hp_a}/{n_a} vs B:{hp_b}/{n_b})",
        "statistic": f"χ²(1,Yates) = {chi2_hp:.3f}; Fisher OR = {fisher_hp.statistic:.3f}",
        "p": fisher_hp.pvalue, "sig": sig_stars(fisher_hp.pvalue),
    })

    return results


def run_paired_analysis(a_records, b_records, grouping_key, label):
    """
    Paired comparison: for each persona (or scenario), compute the mean score
    per variant, then run Wilcoxon signed-rank test on the paired differences.
    """
    metrics = ["task_success", "clarity", "empathy", "overall"]
    results = []

    for metric in metrics:
        groups_a, groups_b = {}, {}
        for r in a_records:
            groups_a.setdefault(r[grouping_key], []).append(r[metric])
        for r in b_records:
            groups_b.setdefault(r[grouping_key], []).append(r[metric])

        common = sorted(set(groups_a.keys()) & set(groups_b.keys()))
        paired_a = [np.mean(groups_a[k]) for k in common]
        paired_b = [np.mean(groups_b[k]) for k in common]

        if len(common) < 5:
            continue

        diffs = np.array(paired_a) - np.array(paired_b)
        w_stat, w_p = stats.wilcoxon(diffs, alternative='two-sided')
        results.append({
            "grouping": label,
            "metric": metric,
            "n_pairs": len(common),
            "mean_diff": np.mean(diffs),
            "median_diff": np.median(diffs),
            "W": w_stat,
            "p": w_p,
            "sig": sig_stars(w_p),
        })

    return results


# ============================================================================
# OUTPUT
# ============================================================================

def print_header(title, width=100):
    print(f"\n{'=' * width}")
    print(f"  {title}")
    print(f"{'=' * width}")


def print_metric_table(results, title):
    print_header(title)
    print(f"\n  {'Metric':<20} {'M_A':>6} {'SD_A':>6} {'M_B':>6} {'SD_B':>6} "
          f"{'Δ':>7} {'d':>6} {'Effect':>10} {'U':>8} {'p(MW)':>8}     {'t':>7} {'p(t)':>8}     {'95% CI Δ':>18}")
    print(f"  {'-' * 125}")
    for r in results:
        print(f"  {r['metric']:<20} "
              f"{r['mean_A']:>6.3f} {r['sd_A']:>6.3f} "
              f"{r['mean_B']:>6.3f} {r['sd_B']:>6.3f} "
              f"{r['delta']:>+7.3f} "
              f"{r['cohens_d']:>6.2f} {r['effect']:>10} "
              f"{r['mw_U']:>8.0f} {r['mw_p']:>8.4f}{sig_stars(r['mw_p']):<3} "
              f"{r['welch_t']:>7.2f} {r['welch_p']:>8.4f}{sig_stars(r['welch_p']):<3} "
              f"[{r['ci_lo']:>+.3f}, {r['ci_hi']:>+.3f}]")


def print_categorical(results):
    print_header("CATEGORICAL OUTCOMES — Chi-squared / Fisher's Exact")
    for r in results:
        print(f"\n  {r['test']}")
        if "counts_A" in r:
            print(f"    A: {r['counts_A']}")
            print(f"    B: {r['counts_B']}")
        print(f"    {r['statistic']}")
        print(f"    p = {r['p']:.4f} {r['sig']}")


def print_paired(results, title):
    print_header(title)
    print(f"\n  {'Metric':<20} {'Pairs':>6} {'Mean Δ':>8} {'Median Δ':>9} {'W':>8} {'p':>8}")
    print(f"  {'-' * 70}")
    for r in results:
        print(f"  {r['metric']:<20} {r['n_pairs']:>6} {r['mean_diff']:>+8.3f} "
              f"{r['median_diff']:>+9.3f} {r['W']:>8.0f} {r['p']:>8.4f}{r['sig']}")


def export_csv(metric_results, categorical, paired_persona, paired_scenario, filepath):
    with open(filepath, 'w', newline='') as f:
        w = csv.writer(f)

        # Metric tests
        w.writerow(["Section", "Metric", "n_A", "n_B", "Mean_A", "SD_A", "Mean_B", "SD_B",
                     "Delta", "Cohens_d", "Effect", "CI_Lower", "CI_Upper",
                     "MW_U", "MW_p", "Welch_t", "Welch_p"])
        for r in metric_results:
            w.writerow([r.get("source", ""), r["metric"], r["n_A"], r["n_B"],
                        f"{r['mean_A']:.4f}", f"{r['sd_A']:.4f}",
                        f"{r['mean_B']:.4f}", f"{r['sd_B']:.4f}",
                        f"{r['delta']:.4f}", f"{r['cohens_d']:.4f}", r["effect"],
                        f"{r['ci_lo']:.4f}", f"{r['ci_hi']:.4f}",
                        f"{r['mw_U']:.0f}", f"{r['mw_p']:.6f}",
                        f"{r['welch_t']:.4f}", f"{r['welch_p']:.6f}"])

        w.writerow([])
        w.writerow(["Section", "Test", "Statistic", "p", "Sig"])
        for r in categorical:
            w.writerow(["Categorical", r["test"], r["statistic"],
                        f"{r['p']:.6f}", r["sig"]])

        w.writerow([])
        w.writerow(["Section", "Grouping", "Metric", "Pairs", "Mean_Diff", "Median_Diff", "W", "p"])
        for r in paired_persona + paired_scenario:
            w.writerow(["Paired", r["grouping"], r["metric"], r["n_pairs"],
                        f"{r['mean_diff']:.4f}", f"{r['median_diff']:.4f}",
                        f"{r['W']:.0f}", f"{r['p']:.6f}"])

    print(f"\n  CSV exported to: {filepath}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="VodaCare A/B — Statistical Analysis (Raw Data)")
    parser.add_argument("--exp-a", default="/mnt/user-data/uploads/exp_A_full_baseline_20260219_193356.json")
    parser.add_argument("--exp-b", default="/mnt/user-data/uploads/exp_B_full_study_variant_b_20260129_165436.json")
    parser.add_argument("--csv", type=str, help="Export results to CSV")
    parser.add_argument("--output", type=str, help="Save console output to text file")
    args = parser.parse_args()

    if args.output:
        original_stdout = sys.stdout
        sys.stdout = open(args.output, 'w')

    # Load data
    a_records, sum_a = load_experiment(args.exp_a)
    b_records, sum_b = load_experiment(args.exp_b)

    print("=" * 100)
    print("  STATISTICAL ANALYSIS — VodaCare A/B Study (From Raw Experiment Data)")
    print("=" * 100)
    print(f"\n  Variant A (Kindness):      {len(a_records)} conversations")
    print(f"  Variant B (Confirmation):  {len(b_records)} conversations")
    print(f"\n  Tests: Mann-Whitney U, Welch's t-test, Cohen's d, Bootstrap 95% CIs,")
    print(f"         Chi-squared, Fisher's exact, Wilcoxon signed-rank (paired)")

    # ── 1. MAIN METRIC COMPARISONS ──
    metrics = ["task_success", "clarity", "empathy", "policy_compliance", "overall"]
    metric_results = []
    for m in metrics:
        a_vals = [r[m] for r in a_records]
        b_vals = [r[m] for r in b_records]
        res = run_metric_tests(a_vals, b_vals, m)
        res["source"] = "Simulation LAJ"
        metric_results.append(res)

    print_metric_table(metric_results, "SIMULATION LAJ SCORES (0-1) — Per-Conversation Tests (n=100 each)")

    # Conversation length and latency
    tel_metrics = [
        ("total_turns", "Conversation length"),
        ("latency_ms", "Avg latency (ms)"),
    ]
    tel_results = []
    for field, label in tel_metrics:
        a_vals = [r[field] for r in a_records]
        b_vals = [r[field] for r in b_records]
        res = run_metric_tests(a_vals, b_vals, label)
        res["source"] = "Telemetry"
        tel_results.append(res)

    print_metric_table(tel_results, "SIMULATION TELEMETRY")

    # ── 2. CATEGORICAL OUTCOMES ──
    cat_results = run_categorical_tests(a_records, b_records)
    print_categorical(cat_results)

    # ── 3. PAIRED ANALYSIS (Per-Persona) ──
    paired_persona = run_paired_analysis(a_records, b_records, "persona", "Per-Persona")
    print_paired(paired_persona, "PAIRED ANALYSIS — Per-Persona (Wilcoxon signed-rank, n=20 personas)")

    # ── 4. PAIRED ANALYSIS (Per-Scenario) ──
    paired_scenario = run_paired_analysis(a_records, b_records, "scenario", "Per-Scenario")
    print_paired(paired_scenario, "PAIRED ANALYSIS — Per-Scenario (Wilcoxon signed-rank, n=5 scenarios)")

    # ── 5. BONFERRONI CORRECTION ──
    all_p = [(r["source"], r["metric"], r["mw_p"]) for r in metric_results + tel_results]
    n_tests = len(all_p)
    alpha_c = 0.05 / n_tests

    print_header(f"MULTIPLE COMPARISONS — Bonferroni Correction (k={n_tests}, α_corrected={alpha_c:.4f})")
    surviving = [(s, m, p) for s, m, p in all_p if p < alpha_c]
    print(f"\n  Tests surviving correction ({len(surviving)}/{n_tests}):")
    for s, m, p in sorted(surviving, key=lambda x: x[2]):
        print(f"    ✓ {m:<22} p = {p:.6f}")

    not_surviving = [(s, m, p) for s, m, p in all_p if p >= alpha_c and p < 0.05]
    if not_surviving:
        print(f"\n  Significant at α=.05 but NOT surviving Bonferroni:")
        for s, m, p in sorted(not_surviving, key=lambda x: x[2]):
            print(f"    ~ {m:<22} p = {p:.6f}")

    # ── 6. DESCRIPTIVE STATS SUMMARY ──
    print_header("DESCRIPTIVE STATISTICS SUMMARY")
    for m in metrics:
        a_vals = np.array([r[m] for r in a_records])
        b_vals = np.array([r[m] for r in b_records])
        print(f"\n  {m}:")
        print(f"    A: M={np.mean(a_vals):.3f}, SD={np.std(a_vals, ddof=1):.3f}, "
              f"Mdn={np.median(a_vals):.3f}, IQR=[{np.percentile(a_vals, 25):.2f}, {np.percentile(a_vals, 75):.2f}]")
        print(f"    B: M={np.mean(b_vals):.3f}, SD={np.std(b_vals, ddof=1):.3f}, "
              f"Mdn={np.median(b_vals):.3f}, IQR=[{np.percentile(b_vals, 25):.2f}, {np.percentile(b_vals, 75):.2f}]")
        # Normality check
        _, sw_p_a = stats.shapiro(a_vals)
        _, sw_p_b = stats.shapiro(b_vals)
        print(f"    Shapiro-Wilk: A p={sw_p_a:.4f}, B p={sw_p_b:.4f} "
              f"{'(non-normal)' if sw_p_a < 0.05 or sw_p_b < 0.05 else '(normal)'}")

    print(f"\n\n  {'=' * 60}")
    print(f"  *** p < .001  ** p < .01  * p < .05  † p < .10")
    print(f"  {'=' * 60}")

    # CSV
    all_metric = metric_results + tel_results
    if args.csv:
        export_csv(all_metric, cat_results, paired_persona, paired_scenario, args.csv)

    if args.output:
        sys.stdout.close()
        sys.stdout = original_stdout
        print(f"Output saved to: {args.output}")


if __name__ == "__main__":
    main()
