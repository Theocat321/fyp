"""
Statistical Analysis for VodaCare A/B Study
============================================
Computes Welch's t-tests, Cohen's d effect sizes, 95% confidence intervals,
and chi-squared/Fisher's exact tests from summary statistics.

NOTE: Standard deviations are estimated from reported distributions (Figures 5-6).
If raw session-level data is available, replace the estimated SDs with actual
computed values for more precise results.

Usage:
    python statistical_analysis.py
    python statistical_analysis.py --output results.txt
    python statistical_analysis.py --csv results.csv
"""

import argparse
import csv
import io
import sys
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings('ignore')


# ============================================================================
# CONFIGURATION — Replace estimated SDs with actual values if available
# ============================================================================

# Sample sizes
N_SELF_A, N_SELF_B = 50, 33        # Rated human sessions
N_LAJ_A, N_LAJ_B = 52, 33          # All human sessions (LAJ evaluated)
N_SIM_A, N_SIM_B = 100, 100        # Simulated conversations
N_TEL_A, N_TEL_B = 54, 36          # Telemetry sessions

# Human self-ratings (1-5 scale)
# SDs estimated from Figures 5 & 6 distributions
SELF_RATINGS = {
    "Overall":      {"mA": 3.90, "mB": 3.91, "sA": 0.90, "sB": 0.85},
    "Task Success": {"mA": 4.06, "mB": 4.06, "sA": 1.10, "sB": 0.85},
    "Clarity":      {"mA": 4.04, "mB": 3.91, "sA": 0.85, "sB": 0.80},
    "Empathy":      {"mA": 4.50, "mB": 3.90, "sA": 0.70, "sB": 1.00},
    "Accuracy":     {"mA": 4.04, "mB": 3.88, "sA": 0.85, "sB": 0.80},
}

# LLM-as-Judge — Human conversations (0-1 scale)
LAJ_HUMAN = {
    "Overall":      {"mA": 0.89, "mB": 0.82, "sA": 0.08, "sB": 0.10},
    "Task Success": {"mA": 0.83, "mB": 0.83, "sA": 0.18, "sB": 0.18},
    "Clarity":      {"mA": 0.91, "mB": 0.89, "sA": 0.07, "sB": 0.08},
    "Empathy":      {"mA": 0.96, "mB": 0.60, "sA": 0.06, "sB": 0.15},
}

# LLM-as-Judge — Simulated conversations (0-1 scale)
LAJ_SIM = {
    "Overall":      {"mA": 0.563, "mB": 0.514, "sA": 0.15, "sB": 0.15},
    "Task Success": {"mA": 0.347, "mB": 0.351, "sA": 0.22, "sB": 0.22},
    "Clarity":      {"mA": 0.709, "mB": 0.721, "sA": 0.12, "sB": 0.12},
    "Empathy":      {"mA": 0.844, "mB": 0.545, "sA": 0.12, "sB": 0.18},
}

# Behavioural telemetry
TELEMETRY = {
    "Session duration (s)":   {"mA": 323, "mB": 428, "sA": 120, "sB": 150},
    "User turns":             {"mA": 3.9, "mB": 4.4, "sA": 1.5,  "sB": 1.8},
    "Typing dur/turn (s)":    {"mA": 19,  "mB": 12,  "sA": 8,    "sB": 5},
    "Reply latency (s)":      {"mA": 3.9, "mB": 3.5, "sA": 1.5,  "sB": 1.2},
}

# Simulation outcomes (counts out of 100 per group)
SIM_OUTCOMES_A = {"Resolved": 40, "Escalation": 32, "Stalemate": 12, "Patience exceeded": 16}
SIM_OUTCOMES_B = {"Resolved": 35, "Escalation": 29, "Stalemate": 17, "Patience exceeded": 19}
SIM_CRITICAL_FAILURE = {"A": 5, "B": 18}       # out of 100
SIM_HEURISTIC_PASS = {"A": 81, "B": 73}        # out of 100


# ============================================================================
# STATISTICAL FUNCTIONS
# ============================================================================

def cohens_d(m1, m2, s1, s2, n1, n2):
    """Cohen's d with pooled standard deviation."""
    sp = np.sqrt(((n1 - 1) * s1**2 + (n2 - 1) * s2**2) / (n1 + n2 - 2))
    return (m1 - m2) / sp if sp > 0 else 0.0


def effect_label(d):
    """Classify effect size magnitude."""
    d = abs(d)
    if d < 0.2:   return "negligible"
    elif d < 0.5: return "small"
    elif d < 0.8: return "medium"
    else:         return "large"


def welch_t(m1, m2, s1, s2, n1, n2):
    """Welch's t-test from summary statistics. Returns (t, p, df)."""
    se = np.sqrt(s1**2 / n1 + s2**2 / n2)
    if se == 0:
        return 0.0, 1.0, 0.0
    t_stat = (m1 - m2) / se
    num = (s1**2 / n1 + s2**2 / n2) ** 2
    denom = (s1**2 / n1)**2 / (n1 - 1) + (s2**2 / n2)**2 / (n2 - 1)
    df = num / denom if denom > 0 else 0
    p_val = 2 * stats.t.sf(abs(t_stat), df)
    return t_stat, p_val, df


def ci_diff(m1, m2, s1, s2, n1, n2, alpha=0.05):
    """95% CI for difference in means (Welch approximation)."""
    diff = m1 - m2
    se = np.sqrt(s1**2 / n1 + s2**2 / n2)
    num = (s1**2 / n1 + s2**2 / n2) ** 2
    denom = (s1**2 / n1)**2 / (n1 - 1) + (s2**2 / n2)**2 / (n2 - 1)
    df = num / denom if denom > 0 else 0
    t_crit = stats.t.ppf(1 - alpha / 2, df)
    return diff - t_crit * se, diff + t_crit * se


def sig_stars(p):
    """Return significance stars."""
    if p < 0.001:  return "***"
    elif p < 0.01: return "**"
    elif p < 0.05: return "*"
    elif p < 0.10: return "†"
    else:          return ""


# ============================================================================
# ANALYSIS RUNNER
# ============================================================================

def run_t_tests(data, nA, nB, label, decimal=2):
    """Run Welch's t-tests for a set of metrics. Returns list of result dicts."""
    results = []
    for metric, v in data.items():
        t, p, df = welch_t(v["mA"], v["mB"], v["sA"], v["sB"], nA, nB)
        d = cohens_d(v["mA"], v["mB"], v["sA"], v["sB"], nA, nB)
        ci_lo, ci_hi = ci_diff(v["mA"], v["mB"], v["sA"], v["sB"], nA, nB)
        results.append({
            "source": label,
            "metric": metric,
            "mean_A": v["mA"],
            "mean_B": v["mB"],
            "delta": v["mA"] - v["mB"],
            "t": t,
            "df": df,
            "p": p,
            "sig": sig_stars(p),
            "d": d,
            "effect": effect_label(d),
            "ci_lo": ci_lo,
            "ci_hi": ci_hi,
        })
    return results


def run_chi_squared():
    """Run chi-squared and Fisher's exact tests on simulation outcomes."""
    results = []

    # Overall outcome distribution (4-category)
    obs = np.array([list(SIM_OUTCOMES_A.values()), list(SIM_OUTCOMES_B.values())])
    chi2, p, dof, _ = stats.chi2_contingency(obs)
    results.append({
        "test": "Outcome distribution (4-cat)",
        "statistic": f"χ²({dof}) = {chi2:.3f}",
        "p": p,
        "sig": sig_stars(p),
        "note": "Resolved/Escalation/Stalemate/Patience",
    })

    # Critical failure rate (2x2)
    cf = np.array([[SIM_CRITICAL_FAILURE["A"], 100 - SIM_CRITICAL_FAILURE["A"]],
                    [SIM_CRITICAL_FAILURE["B"], 100 - SIM_CRITICAL_FAILURE["B"]]])
    chi2_cf, p_cf, _, _ = stats.chi2_contingency(cf, correction=True)
    fisher = stats.fisher_exact(cf)
    results.append({
        "test": f"Critical failure (A:{SIM_CRITICAL_FAILURE['A']}% vs B:{SIM_CRITICAL_FAILURE['B']}%)",
        "statistic": f"χ²(1,Yates) = {chi2_cf:.3f}; Fisher OR = {fisher.statistic:.3f}",
        "p": fisher.pvalue,
        "sig": sig_stars(fisher.pvalue),
        "note": "Fisher's exact preferred for small cells",
    })

    # Heuristic pass rate (2x2)
    hp = np.array([[SIM_HEURISTIC_PASS["A"], 100 - SIM_HEURISTIC_PASS["A"]],
                    [SIM_HEURISTIC_PASS["B"], 100 - SIM_HEURISTIC_PASS["B"]]])
    chi2_hp, p_hp, _, _ = stats.chi2_contingency(hp, correction=True)
    fisher_hp = stats.fisher_exact(hp)
    results.append({
        "test": f"Heuristic pass (A:{SIM_HEURISTIC_PASS['A']}% vs B:{SIM_HEURISTIC_PASS['B']}%)",
        "statistic": f"χ²(1,Yates) = {chi2_hp:.3f}; Fisher OR = {fisher_hp.statistic:.3f}",
        "p": fisher_hp.pvalue,
        "sig": sig_stars(fisher_hp.pvalue),
        "note": "",
    })

    return results


def bonferroni_note(all_results):
    """Count tests and compute Bonferroni threshold."""
    n_tests = len(all_results)
    alpha_corrected = 0.05 / n_tests
    surviving = [r for r in all_results if r["p"] < alpha_corrected]
    return n_tests, alpha_corrected, surviving


# ============================================================================
# OUTPUT FORMATTERS
# ============================================================================

def print_t_table(results, title, nA, nB):
    """Pretty-print a t-test results table."""
    print(f"\n{'=' * 90}")
    print(f"  {title}")
    print(f"  Group A: n={nA} | Group B: n={nB}")
    print(f"{'=' * 90}")
    print(f"  {'Metric':<18} {'M_A':>7} {'M_B':>7} {'Δ':>8} {'t':>7} {'df':>6} {'p':>8}     {'d':>6} {'Effect':>10} {'95% CI':>20}")
    print(f"  {'-' * 105}")
    for r in results:
        print(f"  {r['metric']:<18} {r['mean_A']:>7.2f} {r['mean_B']:>7.2f} {r['delta']:>+8.2f} "
              f"{r['t']:>7.2f} {r['df']:>6.1f} {r['p']:>8.4f}{r['sig']:<3} "
              f"{r['d']:>6.2f} {r['effect']:>10} "
              f"[{r['ci_lo']:>+.3f}, {r['ci_hi']:>+.3f}]")


def print_chi_table(results):
    """Pretty-print chi-squared results."""
    print(f"\n{'=' * 90}")
    print(f"  SIMULATION OUTCOMES — Chi-squared / Fisher's Exact Tests")
    print(f"  Variant A: n=100 | Variant B: n=100")
    print(f"{'=' * 90}")
    for r in results:
        print(f"\n  {r['test']}")
        print(f"    {r['statistic']}")
        print(f"    p = {r['p']:.4f} {r['sig']}")
        if r["note"]:
            print(f"    ({r['note']})")


def export_csv(all_t_results, chi_results, filepath):
    """Export all results to CSV."""
    with open(filepath, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(["Source", "Metric", "Mean_A", "Mean_B", "Delta",
                     "t", "df", "p", "Sig", "Cohens_d", "Effect_Size",
                     "CI_Lower", "CI_Upper"])
        for r in all_t_results:
            w.writerow([r["source"], r["metric"], f"{r['mean_A']:.3f}",
                        f"{r['mean_B']:.3f}", f"{r['delta']:.3f}",
                        f"{r['t']:.3f}", f"{r['df']:.1f}", f"{r['p']:.4f}",
                        r["sig"], f"{r['d']:.3f}", r["effect"],
                        f"{r['ci_lo']:.4f}", f"{r['ci_hi']:.4f}"])

        w.writerow([])
        w.writerow(["Source", "Test", "Statistic", "p", "Sig", "Note"])
        for r in chi_results:
            w.writerow(["Simulation Outcomes", r["test"], r["statistic"],
                        f"{r['p']:.4f}", r["sig"], r["note"]])
    print(f"\n  CSV exported to: {filepath}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="VodaCare A/B Study — Statistical Analysis")
    parser.add_argument("--csv", type=str, help="Export results to CSV file")
    parser.add_argument("--output", type=str, help="Save console output to text file")
    args = parser.parse_args()

    # Redirect output if --output specified
    if args.output:
        original_stdout = sys.stdout
        sys.stdout = open(args.output, 'w')

    print("=" * 90)
    print("  STATISTICAL ANALYSIS — VodaCare A/B Study")
    print("  Dissertation: How do LLM System Prompts Affect User Behavior")
    print("=" * 90)
    print("\n  Tests: Welch's t-test (unequal variances), Cohen's d, 95% CIs,")
    print("         Chi-squared with Yates correction, Fisher's exact test")
    print("  Note:  SDs estimated from reported distributions. Replace with")
    print("         actual SDs from raw data for final submission.")

    # Run all t-tests
    r_self = run_t_tests(SELF_RATINGS, N_SELF_A, N_SELF_B, "Human Self-Rating")
    r_laj_h = run_t_tests(LAJ_HUMAN, N_LAJ_A, N_LAJ_B, "Human LAJ")
    r_laj_s = run_t_tests(LAJ_SIM, N_SIM_A, N_SIM_B, "Simulation LAJ")
    r_tel = run_t_tests(TELEMETRY, N_TEL_A, N_TEL_B, "Telemetry")
    r_chi = run_chi_squared()

    # Print tables
    print_t_table(r_self, "HUMAN SELF-RATINGS (1-5 scale) — Welch's t-tests", N_SELF_A, N_SELF_B)
    print_t_table(r_laj_h, "LLM-AS-JUDGE — Human Conversations (0-1 scale)", N_LAJ_A, N_LAJ_B)
    print_t_table(r_laj_s, "LLM-AS-JUDGE — Simulated Conversations (0-1 scale)", N_SIM_A, N_SIM_B)
    print_t_table(r_tel, "BEHAVIOURAL TELEMETRY", N_TEL_A, N_TEL_B)
    print_chi_table(r_chi)

    # Bonferroni correction
    all_t = r_self + r_laj_h + r_laj_s + r_tel
    n_tests, alpha_c, surviving = bonferroni_note(all_t)
    print(f"\n{'=' * 90}")
    print(f"  MULTIPLE COMPARISONS — Bonferroni Correction")
    print(f"{'=' * 90}")
    print(f"  Total t-tests conducted: {n_tests}")
    print(f"  Bonferroni-corrected α: {alpha_c:.4f}")
    print(f"  Tests surviving correction: {len(surviving)}")
    for r in surviving:
        print(f"    ✓ {r['source']} — {r['metric']}: p = {r['p']:.4f}, d = {r['d']:.2f}")

    # Significance legend
    print(f"\n  *** p < .001  ** p < .01  * p < .05  † p < .10")

    # CSV export
    if args.csv:
        export_csv(all_t, r_chi, args.csv)

    if args.output:
        sys.stdout.close()
        sys.stdout = original_stdout
        print(f"Output saved to: {args.output}")


if __name__ == "__main__":
    main()
