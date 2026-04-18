import argparse
import csv
import json
import sys
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings('ignore')


def load_experiment(filepath):
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


def cohens_d(x, y):
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
    rng = np.random.default_rng(42)
    diffs = [np.mean(rng.choice(x, len(x), replace=True)) - np.mean(rng.choice(y, len(y), replace=True))
             for _ in range(10000)]
    return np.percentile(diffs, 100 * alpha / 2), np.percentile(diffs, 100 * (1 - alpha / 2))


def run_metric_tests(a_vals, b_vals, metric_name):
    a, b = np.array(a_vals), np.array(b_vals)
    mw_stat, mw_p = stats.mannwhitneyu(a, b, alternative='two-sided')
    t_stat, t_p = stats.ttest_ind(a, b, equal_var=False)
    d = cohens_d(a, b)
    ci_lo, ci_hi = ci_difference(a, b)
    n1, n2 = len(a), len(b)
    return {
        "metric": metric_name,
        "n_A": n1, "n_B": n2,
        "mean_A": np.mean(a), "sd_A": np.std(a, ddof=1),
        "mean_B": np.mean(b), "sd_B": np.std(b, ddof=1),
        "delta": np.mean(a) - np.mean(b),
        "cohens_d": d, "effect": effect_label(d),
        "ci_lo": ci_lo, "ci_hi": ci_hi,
        "mw_U": mw_stat, "mw_p": mw_p,
        "welch_t": t_stat, "welch_p": t_p,
        "r_rb": 1 - (2 * mw_stat) / (n1 * n2),
    }


def run_categorical_tests(a_records, b_records):
    results = []
    reasons = ["satisfaction", "escalation", "stalemate", "patience_exceeded"]
    counts_a = [sum(1 for r in a_records if r["termination"] == x) for x in reasons]
    counts_b = [sum(1 for r in b_records if r["termination"] == x) for x in reasons]
    chi2, p, dof, _ = stats.chi2_contingency(np.array([counts_a, counts_b]))
    results.append({
        "test": "Outcome distribution (4-category)",
        "counts_A": dict(zip(reasons, counts_a)),
        "counts_B": dict(zip(reasons, counts_b)),
        "statistic": f"χ²({dof}) = {chi2:.3f}",
        "p": p, "sig": sig_stars(p),
    })

    n_a, n_b = len(a_records), len(b_records)
    for label, key in [("Critical failure", "critical_failure"), ("Heuristic pass", "heuristic_pass")]:
        ca = sum(1 for r in a_records if r[key])
        cb = sum(1 for r in b_records if r[key])
        table = np.array([[ca, n_a - ca], [cb, n_b - cb]])
        chi2_v, _, _, _ = stats.chi2_contingency(table, correction=True)
        fisher = stats.fisher_exact(table)
        results.append({
            "test": f"{label} (A:{ca}/{n_a} vs B:{cb}/{n_b})",
            "statistic": f"χ²(1,Yates) = {chi2_v:.3f}; Fisher OR = {fisher.statistic:.3f}",
            "p": fisher.pvalue, "sig": sig_stars(fisher.pvalue),
        })
    return results


def run_paired_analysis(a_records, b_records, grouping_key, label):
    results = []
    for metric in ["task_success", "clarity", "empathy", "overall"]:
        groups_a, groups_b = {}, {}
        for r in a_records:
            groups_a.setdefault(r[grouping_key], []).append(r[metric])
        for r in b_records:
            groups_b.setdefault(r[grouping_key], []).append(r[metric])
        common = sorted(set(groups_a) & set(groups_b))
        if len(common) < 5:
            continue
        diffs = np.array([np.mean(groups_a[k]) for k in common]) - np.array([np.mean(groups_b[k]) for k in common])
        w_stat, w_p = stats.wilcoxon(diffs, alternative='two-sided')
        results.append({
            "grouping": label, "metric": metric, "n_pairs": len(common),
            "mean_diff": np.mean(diffs), "median_diff": np.median(diffs),
            "W": w_stat, "p": w_p, "sig": sig_stars(w_p),
        })
    return results


def section(title):
    print(f"\n{title}\n{'-' * len(title)}")


def print_metric_table(results, title):
    section(title)
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
    section("Categorical outcomes — Chi-squared / Fisher's exact")
    for r in results:
        print(f"\n  {r['test']}")
        if "counts_A" in r:
            print(f"    A: {r['counts_A']}")
            print(f"    B: {r['counts_B']}")
        print(f"    {r['statistic']}")
        print(f"    p = {r['p']:.4f} {r['sig']}")


def print_paired(results, title):
    section(title)
    print(f"\n  {'Metric':<20} {'Pairs':>6} {'Mean Δ':>8} {'Median Δ':>9} {'W':>8} {'p':>8}")
    print(f"  {'-' * 70}")
    for r in results:
        print(f"  {r['metric']:<20} {r['n_pairs']:>6} {r['mean_diff']:>+8.3f} "
              f"{r['median_diff']:>+9.3f} {r['W']:>8.0f} {r['p']:>8.4f}{r['sig']}")


def export_csv(metric_results, categorical, paired_persona, paired_scenario, filepath):
    with open(filepath, 'w', newline='') as f:
        w = csv.writer(f)
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
            w.writerow(["Categorical", r["test"], r["statistic"], f"{r['p']:.6f}", r["sig"]])
        w.writerow([])
        w.writerow(["Section", "Grouping", "Metric", "Pairs", "Mean_Diff", "Median_Diff", "W", "p"])
        for r in paired_persona + paired_scenario:
            w.writerow(["Paired", r["grouping"], r["metric"], r["n_pairs"],
                        f"{r['mean_diff']:.4f}", f"{r['median_diff']:.4f}",
                        f"{r['W']:.0f}", f"{r['p']:.6f}"])
    print(f"\n  CSV → {filepath}")


def main():
    parser = argparse.ArgumentParser(description="VodaCare A/B statistical analysis")
    parser.add_argument("--exp-a", default="outputs/exp_A_full_baseline_20260219_193356.json")
    parser.add_argument("--exp-b", default="outputs/exp_B_full_study_variant_b_20260129_165436.json")
    parser.add_argument("--csv", type=str)
    parser.add_argument("--output", type=str)
    args = parser.parse_args()

    if args.output:
        original_stdout = sys.stdout
        sys.stdout = open(args.output, 'w')

    a_records, _ = load_experiment(args.exp_a)
    b_records, _ = load_experiment(args.exp_b)

    print(f"VodaCare A/B — Statistical Analysis")
    print(f"Variant A (Kindness): {len(a_records)} conversations")
    print(f"Variant B (Confirmation): {len(b_records)} conversations")

    metrics = ["task_success", "clarity", "empathy", "policy_compliance", "overall"]
    metric_results = []
    for m in metrics:
        res = run_metric_tests([r[m] for r in a_records], [r[m] for r in b_records], m)
        res["source"] = "Simulation LAJ"
        metric_results.append(res)
    print_metric_table(metric_results, "Simulation LAJ scores (0-1), n=100 each")

    tel_results = []
    for field, label in [("total_turns", "Conversation length"), ("latency_ms", "Avg latency (ms)")]:
        res = run_metric_tests([r[field] for r in a_records], [r[field] for r in b_records], label)
        res["source"] = "Telemetry"
        tel_results.append(res)
    print_metric_table(tel_results, "Simulation telemetry")

    cat_results = run_categorical_tests(a_records, b_records)
    print_categorical(cat_results)

    paired_persona = run_paired_analysis(a_records, b_records, "persona", "Per-Persona")
    print_paired(paired_persona, "Paired analysis — per-persona (Wilcoxon, n=20)")

    paired_scenario = run_paired_analysis(a_records, b_records, "scenario", "Per-Scenario")
    print_paired(paired_scenario, "Paired analysis — per-scenario (Wilcoxon, n=5)")

    all_p = [(r["source"], r["metric"], r["mw_p"]) for r in metric_results + tel_results]
    alpha_c = 0.05 / len(all_p)
    section(f"Bonferroni correction (k={len(all_p)}, α={alpha_c:.4f})")
    surviving = [(s, m, p) for s, m, p in all_p if p < alpha_c]
    print(f"\n  Surviving ({len(surviving)}/{len(all_p)}):")
    for _, m, p in sorted(surviving, key=lambda x: x[2]):
        print(f"    ✓ {m:<22} p = {p:.6f}")
    marginal = [(s, m, p) for s, m, p in all_p if alpha_c <= p < 0.05]
    if marginal:
        print(f"\n  Significant at α=.05 but not Bonferroni-corrected:")
        for _, m, p in sorted(marginal, key=lambda x: x[2]):
            print(f"    ~ {m:<22} p = {p:.6f}")

    section("Descriptive statistics")
    for m in metrics:
        a_vals = np.array([r[m] for r in a_records])
        b_vals = np.array([r[m] for r in b_records])
        _, sw_a = stats.shapiro(a_vals)
        _, sw_b = stats.shapiro(b_vals)
        normality = "(non-normal)" if sw_a < 0.05 or sw_b < 0.05 else "(normal)"
        print(f"\n  {m}:")
        print(f"    A: M={np.mean(a_vals):.3f}, SD={np.std(a_vals, ddof=1):.3f}, "
              f"Mdn={np.median(a_vals):.3f}, IQR=[{np.percentile(a_vals,25):.2f}, {np.percentile(a_vals,75):.2f}]")
        print(f"    B: M={np.mean(b_vals):.3f}, SD={np.std(b_vals, ddof=1):.3f}, "
              f"Mdn={np.median(b_vals):.3f}, IQR=[{np.percentile(b_vals,25):.2f}, {np.percentile(b_vals,75):.2f}]")
        print(f"    Shapiro-Wilk: A p={sw_a:.4f}, B p={sw_b:.4f} {normality}")

    print(f"\n*** p<.001  ** p<.01  * p<.05  † p<.10")

    if args.csv:
        export_csv(metric_results + tel_results, cat_results, paired_persona, paired_scenario, args.csv)

    if args.output:
        sys.stdout.close()
        sys.stdout = original_stdout
        print(f"Saved to {args.output}")


if __name__ == "__main__":
    main()
