#!/usr/bin/env python3
"""
Generate HTML comparison reports for LLM-simulated vs Human testing results.

This script loads experiment results from JSON files and generates a beautiful
HTML report showing side-by-side comparison of LLM testing metrics vs human
evaluation metrics.

Usage:
    # Compare single LLM experiment with human results
    python generate_comparison_report.py \
        --llm-results outputs/exp_A_*.json \
        --human-results outputs/human_evaluation.json \
        --output comparison_report.html

    # Compare multiple LLM experiments
    python generate_comparison_report.py \
        --llm-results "outputs/exp_A_*.json,outputs/exp_B_*.json" \
        --human-results outputs/human_evaluation.json \
        --output full_comparison.html
"""
import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from glob import glob
from statistics import mean, stdev

logger = logging.getLogger(__name__)


def load_llm_results(pattern: str) -> List[Dict[str, Any]]:
    """
    Load LLM experiment results from JSON files matching pattern.

    Args:
        pattern: Glob pattern for LLM result files

    Returns:
        List of experiment result dictionaries
    """
    files = glob(pattern)
    logger.info(f"Found {len(files)} LLM result files matching pattern: {pattern}")

    results = []
    for file_path in files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                results.append(data)
                logger.debug(f"Loaded {file_path}")
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            continue

    return results


def load_human_results(file_path: str) -> Dict[str, Any]:
    """
    Load human evaluation results from JSON file.

    Args:
        file_path: Path to human evaluation JSON file

    Returns:
        Human evaluation result dictionary
    """
    logger.info(f"Loading human results from: {file_path}")

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            logger.debug(f"Loaded human results with {len(data.get('conversations', []))} conversations")
            return data
    except Exception as e:
        logger.error(f"Failed to load human results: {e}")
        raise


def calculate_llm_stats(llm_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate statistics from LLM experiment results.

    Args:
        llm_results: List of LLM experiment result dictionaries

    Returns:
        Dictionary with aggregated statistics
    """
    if not llm_results:
        return {}

    # Collect all conversations from all experiments
    all_conversations = []
    for experiment in llm_results:
        conversations = experiment.get('conversations', [])
        all_conversations.extend(conversations)

    if not all_conversations:
        return {}

    # Extract scores
    task_success_scores = []
    clarity_scores = []
    empathy_scores = []
    policy_scores = []
    overall_scores = []
    turn_counts = []
    heuristic_passes = []
    critical_failures = []

    # By variant
    scores_by_variant = {}

    for conv in all_conversations:
        eval_scores = conv.get('llm_evaluation', {})
        task_success_scores.append(eval_scores.get('task_success', 0))
        clarity_scores.append(eval_scores.get('clarity', 0))
        empathy_scores.append(eval_scores.get('empathy', 0))
        policy_scores.append(eval_scores.get('policy_compliance', 0))
        overall_scores.append(eval_scores.get('overall_weighted', 0))

        turn_counts.append(conv.get('total_turns', 0))

        heuristic_results = conv.get('heuristic_results', {})
        heuristic_passes.append(1 if heuristic_results.get('all_passed', False) else 0)
        critical_failures.append(1 if heuristic_results.get('critical_failures', []) else 0)

        # Track by variant
        variant = conv.get('variant', 'unknown')
        if variant not in scores_by_variant:
            scores_by_variant[variant] = []
        scores_by_variant[variant].append(eval_scores.get('overall_weighted', 0))

    # Calculate statistics
    stats = {
        'total_conversations': len(all_conversations),
        'avg_task_success': mean(task_success_scores),
        'std_task_success': stdev(task_success_scores) if len(task_success_scores) > 1 else 0,
        'avg_clarity': mean(clarity_scores),
        'std_clarity': stdev(clarity_scores) if len(clarity_scores) > 1 else 0,
        'avg_empathy': mean(empathy_scores),
        'std_empathy': stdev(empathy_scores) if len(empathy_scores) > 1 else 0,
        'avg_policy_compliance': mean(policy_scores),
        'std_policy_compliance': stdev(policy_scores) if len(policy_scores) > 1 else 0,
        'avg_overall': mean(overall_scores),
        'std_overall': stdev(overall_scores) if len(overall_scores) > 1 else 0,
        'avg_turns': mean(turn_counts),
        'heuristic_pass_rate': mean(heuristic_passes),
        'critical_failure_rate': mean(critical_failures),
        'successful_rate': sum(1 for s in task_success_scores if s >= 0.7) / len(task_success_scores),
        'scores_by_variant': {}
    }

    # Calculate variant averages
    for variant, scores in scores_by_variant.items():
        stats['scores_by_variant'][variant] = {
            'avg': mean(scores),
            'std': stdev(scores) if len(scores) > 1 else 0,
            'count': len(scores)
        }

    return stats


def calculate_human_stats(human_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aggregate statistics from human evaluation results.

    Args:
        human_results: Human evaluation result dictionary

    Returns:
        Dictionary with aggregated statistics
    """
    conversations = human_results.get('conversations', [])

    if not conversations:
        return {}

    # Extract LAJ scores for human conversations
    task_success_scores = []
    clarity_scores = []
    empathy_scores = []
    policy_scores = []
    overall_scores = []
    turn_counts = []
    heuristic_passes = []
    critical_failures = []

    # Extract human self-ratings
    human_task_ratings = []
    human_clarity_ratings = []
    human_empathy_ratings = []
    human_overall_ratings = []

    # By variant
    scores_by_variant = {}
    laj_human_deltas = {'task_success': [], 'clarity': [], 'empathy': []}

    for conv in conversations:
        # LAJ scores
        eval_scores = conv.get('llm_evaluation', {})
        task_success_scores.append(eval_scores.get('task_success', 0))
        clarity_scores.append(eval_scores.get('clarity', 0))
        empathy_scores.append(eval_scores.get('empathy', 0))
        policy_scores.append(eval_scores.get('policy_compliance', 0))
        overall_scores.append(eval_scores.get('overall_weighted', 0))

        turn_counts.append(conv.get('total_turns', 0))

        heuristic_results = conv.get('heuristic_results', {})
        heuristic_passes.append(1 if heuristic_results.get('all_passed', False) else 0)
        critical_failures.append(1 if heuristic_results.get('critical_failures', []) else 0)

        # Track by variant
        variant = conv.get('variant', 'unknown')
        if variant not in scores_by_variant:
            scores_by_variant[variant] = []
        scores_by_variant[variant].append(eval_scores.get('overall_weighted', 0))

        # Extract human ratings from config snapshot
        config = conv.get('config_snapshot', {})
        human_feedback = config.get('human_feedback', {})

        if human_feedback.get('rating_task_success') is not None:
            human_task_ratings.append(human_feedback['rating_task_success'])
        if human_feedback.get('rating_clarity') is not None:
            human_clarity_ratings.append(human_feedback['rating_clarity'])
        if human_feedback.get('rating_empathy') is not None:
            human_empathy_ratings.append(human_feedback['rating_empathy'])
        if human_feedback.get('rating_overall') is not None:
            human_overall_ratings.append(human_feedback['rating_overall'])

        # Extract deltas
        comparison = config.get('laj_vs_human_comparison', {})
        if comparison.get('task_success', {}).get('delta') is not None:
            laj_human_deltas['task_success'].append(comparison['task_success']['delta'])
        if comparison.get('clarity', {}).get('delta') is not None:
            laj_human_deltas['clarity'].append(comparison['clarity']['delta'])
        if comparison.get('empathy', {}).get('delta') is not None:
            laj_human_deltas['empathy'].append(comparison['empathy']['delta'])

    # Calculate statistics
    stats = {
        'total_conversations': len(conversations),
        'laj_scores': {
            'avg_task_success': mean(task_success_scores),
            'std_task_success': stdev(task_success_scores) if len(task_success_scores) > 1 else 0,
            'avg_clarity': mean(clarity_scores),
            'std_clarity': stdev(clarity_scores) if len(clarity_scores) > 1 else 0,
            'avg_empathy': mean(empathy_scores),
            'std_empathy': stdev(empathy_scores) if len(empathy_scores) > 1 else 0,
            'avg_policy_compliance': mean(policy_scores),
            'std_policy_compliance': stdev(policy_scores) if len(policy_scores) > 1 else 0,
            'avg_overall': mean(overall_scores),
            'std_overall': stdev(overall_scores) if len(overall_scores) > 1 else 0,
        },
        'human_ratings': {
            'avg_task_success': mean(human_task_ratings) if human_task_ratings else None,
            'std_task_success': stdev(human_task_ratings) if len(human_task_ratings) > 1 else 0,
            'avg_clarity': mean(human_clarity_ratings) if human_clarity_ratings else None,
            'std_clarity': stdev(human_clarity_ratings) if len(human_clarity_ratings) > 1 else 0,
            'avg_empathy': mean(human_empathy_ratings) if human_empathy_ratings else None,
            'std_empathy': stdev(human_empathy_ratings) if len(human_empathy_ratings) > 1 else 0,
            'avg_overall': mean(human_overall_ratings) if human_overall_ratings else None,
            'std_overall': stdev(human_overall_ratings) if len(human_overall_ratings) > 1 else 0,
            'count_with_ratings': len(human_task_ratings)
        },
        'laj_vs_human': {
            'avg_task_success_delta': mean(laj_human_deltas['task_success']) if laj_human_deltas['task_success'] else None,
            'avg_clarity_delta': mean(laj_human_deltas['clarity']) if laj_human_deltas['clarity'] else None,
            'avg_empathy_delta': mean(laj_human_deltas['empathy']) if laj_human_deltas['empathy'] else None,
        },
        'avg_turns': mean(turn_counts),
        'heuristic_pass_rate': mean(heuristic_passes),
        'critical_failure_rate': mean(critical_failures),
        'successful_rate': sum(1 for s in task_success_scores if s >= 0.7) / len(task_success_scores),
        'scores_by_variant': {}
    }

    # Calculate variant averages
    for variant, scores in scores_by_variant.items():
        stats['scores_by_variant'][variant] = {
            'avg': mean(scores),
            'std': stdev(scores) if len(scores) > 1 else 0,
            'count': len(scores)
        }

    return stats


def generate_html_report(
    llm_stats: Dict[str, Any],
    human_stats: Dict[str, Any],
    output_path: str
) -> None:
    """
    Generate beautiful HTML comparison report.

    Args:
        llm_stats: Aggregated LLM experiment statistics
        human_stats: Aggregated human evaluation statistics
        output_path: Path to save HTML file
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Helper to format scores
    def fmt_score(value: Optional[float], scale: str = "0-1") -> str:
        if value is None:
            return "N/A"
        if scale == "0-1":
            return f"{value:.3f}"
        elif scale == "1-5":
            return f"{value:.1f}"
        return str(value)

    def fmt_pct(value: Optional[float]) -> str:
        if value is None:
            return "N/A"
        return f"{value * 100:.1f}%"

    # HTML template with embedded CSS
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LLM vs Human Testing Comparison Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}

        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            text-align: center;
        }}

        header h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            font-weight: 700;
        }}

        header p {{
            font-size: 1rem;
            opacity: 0.9;
        }}

        .content {{
            padding: 2rem;
        }}

        .section {{
            margin-bottom: 3rem;
        }}

        .section-title {{
            font-size: 1.8rem;
            color: #667eea;
            margin-bottom: 1.5rem;
            padding-bottom: 0.5rem;
            border-bottom: 3px solid #667eea;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}

        .stat-card {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 1.5rem;
            border-left: 4px solid #667eea;
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        .stat-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
        }}

        .stat-card.human {{
            border-left-color: #f093fb;
        }}

        .stat-label {{
            font-size: 0.875rem;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.5rem;
        }}

        .stat-value {{
            font-size: 2rem;
            font-weight: 700;
            color: #667eea;
        }}

        .stat-card.human .stat-value {{
            color: #f093fb;
        }}

        .stat-detail {{
            font-size: 0.875rem;
            color: #6c757d;
            margin-top: 0.5rem;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 2rem;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }}

        th {{
            background: #667eea;
            color: white;
            padding: 1rem;
            text-align: left;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.875rem;
            letter-spacing: 0.5px;
        }}

        td {{
            padding: 1rem;
            border-bottom: 1px solid #e9ecef;
        }}

        tr:last-child td {{
            border-bottom: none;
        }}

        tr:hover {{
            background: #f8f9fa;
        }}

        .metric-name {{
            font-weight: 600;
            color: #495057;
        }}

        .score {{
            font-weight: 700;
            font-size: 1.1rem;
        }}

        .score.good {{
            color: #28a745;
        }}

        .score.medium {{
            color: #ffc107;
        }}

        .score.poor {{
            color: #dc3545;
        }}

        .delta {{
            font-weight: 600;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.875rem;
        }}

        .delta.positive {{
            background: #d4edda;
            color: #155724;
        }}

        .delta.negative {{
            background: #f8d7da;
            color: #721c24;
        }}

        .delta.neutral {{
            background: #e2e3e5;
            color: #383d41;
        }}

        .note {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 1rem;
            border-radius: 4px;
            margin: 1rem 0;
        }}

        .note-title {{
            font-weight: 700;
            color: #856404;
            margin-bottom: 0.5rem;
        }}

        .note-text {{
            color: #856404;
            font-size: 0.9rem;
        }}

        .methodology {{
            background: #e7f3ff;
            border-left: 4px solid #2196F3;
            padding: 1.5rem;
            border-radius: 4px;
            margin: 2rem 0;
        }}

        .methodology h3 {{
            color: #1976d2;
            margin-bottom: 1rem;
        }}

        .methodology ul {{
            margin-left: 1.5rem;
            color: #0d47a1;
        }}

        .methodology li {{
            margin-bottom: 0.5rem;
        }}

        footer {{
            background: #f8f9fa;
            padding: 1.5rem;
            text-align: center;
            color: #6c757d;
            font-size: 0.875rem;
        }}

        .badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.875rem;
            font-weight: 600;
            margin-left: 0.5rem;
        }}

        .badge.llm {{
            background: #667eea;
            color: white;
        }}

        .badge.human {{
            background: #f093fb;
            color: white;
        }}

        @media print {{
            body {{
                background: white;
                padding: 0;
            }}

            .container {{
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>LLM vs Human Testing Comparison</h1>
            <p>Comparative Analysis of Simulated and Human Evaluations</p>
            <p style="font-size: 0.875rem; margin-top: 0.5rem;">Generated: {timestamp}</p>
        </header>

        <div class="content">
            <!-- Overall Statistics -->
            <div class="section">
                <h2 class="section-title">Overall Statistics</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-label">LLM Conversations</div>
                        <div class="stat-value">{llm_stats.get('total_conversations', 0)}</div>
                        <div class="stat-detail">Simulated interactions</div>
                    </div>
                    <div class="stat-card human">
                        <div class="stat-label">Human Conversations</div>
                        <div class="stat-value">{human_stats.get('total_conversations', 0)}</div>
                        <div class="stat-detail">Real user interactions</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">LLM Success Rate</div>
                        <div class="stat-value">{fmt_pct(llm_stats.get('successful_rate'))}</div>
                        <div class="stat-detail">Task success >= 0.7</div>
                    </div>
                    <div class="stat-card human">
                        <div class="stat-label">Human Success Rate</div>
                        <div class="stat-value">{fmt_pct(human_stats.get('successful_rate'))}</div>
                        <div class="stat-detail">Task success >= 0.7</div>
                    </div>
                </div>
            </div>

            <!-- Rubric Scores Comparison -->
            <div class="section">
                <h2 class="section-title">Rubric Scores Comparison</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Metric</th>
                            <th>LLM Average (0-1 scale)</th>
                            <th>Human LAJ Average (0-1 scale)</th>
                            <th>Human Self-Rating (1-5 scale)</th>
                            <th>LAJ vs Human Delta</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    # Add rubric score rows
    rubric_metrics = [
        ('Task Success', 'task_success'),
        ('Clarity', 'clarity'),
        ('Empathy', 'empathy'),
        ('Policy Compliance', 'policy_compliance'),
        ('Overall Score', 'overall')
    ]

    for metric_name, metric_key in rubric_metrics:
        llm_val = llm_stats.get(f'avg_{metric_key}', 0)
        human_laj_val = human_stats.get('laj_scores', {}).get(f'avg_{metric_key}', 0)
        human_self_val = human_stats.get('human_ratings', {}).get(f'avg_{metric_key}')

        # Only show delta for metrics that have human self-ratings
        if metric_key in ['task_success', 'clarity', 'empathy']:
            delta_val = human_stats.get('laj_vs_human', {}).get(f'avg_{metric_key}_delta')
            if delta_val is not None:
                delta_class = 'positive' if delta_val > 0.2 else 'negative' if delta_val < -0.2 else 'neutral'
                delta_html = f'<span class="delta {delta_class}">{delta_val:+.2f}</span>'
            else:
                delta_html = '<span class="delta neutral">N/A</span>'
        else:
            delta_html = '<span class="delta neutral">--</span>'

        # Color coding for scores
        llm_class = 'good' if llm_val >= 0.7 else 'medium' if llm_val >= 0.5 else 'poor'
        human_laj_class = 'good' if human_laj_val >= 0.7 else 'medium' if human_laj_val >= 0.5 else 'poor'

        if human_self_val is not None:
            human_self_class = 'good' if human_self_val >= 4.0 else 'medium' if human_self_val >= 3.0 else 'poor'
            human_self_html = f'<span class="score {human_self_class}">{fmt_score(human_self_val, "1-5")}</span>'
        else:
            human_self_html = '<span class="score">N/A</span>'

        html += f"""                        <tr>
                            <td class="metric-name">{metric_name}</td>
                            <td><span class="score {llm_class}">{fmt_score(llm_val)}</span></td>
                            <td><span class="score {human_laj_class}">{fmt_score(human_laj_val)}</span></td>
                            <td>{human_self_html}</td>
                            <td>{delta_html}</td>
                        </tr>
"""

    html += """                    </tbody>
                </table>

                <div class="note">
                    <div class="note-title">Note on Scales</div>
                    <div class="note-text">
                        LLM and Human LAJ scores are on a 0-1 scale. Human self-ratings are on a 1-5 scale.
                        Delta shows LAJ rating minus human self-rating (converted to same scale).
                        Positive delta = LAJ rated higher than human. Negative delta = LAJ rated lower than human.
                    </div>
                </div>
            </div>
"""

    # Variant Comparison
    if llm_stats.get('scores_by_variant') or human_stats.get('scores_by_variant'):
        html += """
            <!-- Variant Performance -->
            <div class="section">
                <h2 class="section-title">Variant Performance Comparison</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Variant</th>
                            <th>Source</th>
                            <th>Conversations</th>
                            <th>Avg Score</th>
                            <th>Std Dev</th>
                        </tr>
                    </thead>
                    <tbody>
"""

        # LLM variants
        for variant, data in sorted(llm_stats.get('scores_by_variant', {}).items()):
            score_class = 'good' if data['avg'] >= 0.7 else 'medium' if data['avg'] >= 0.5 else 'poor'
            html += f"""                        <tr>
                            <td class="metric-name">{variant}</td>
                            <td><span class="badge llm">LLM</span></td>
                            <td>{data['count']}</td>
                            <td><span class="score {score_class}">{fmt_score(data['avg'])}</span></td>
                            <td>{fmt_score(data['std'])}</td>
                        </tr>
"""

        # Human variants
        for variant, data in sorted(human_stats.get('scores_by_variant', {}).items()):
            score_class = 'good' if data['avg'] >= 0.7 else 'medium' if data['avg'] >= 0.5 else 'poor'
            html += f"""                        <tr>
                            <td class="metric-name">{variant}</td>
                            <td><span class="badge human">Human</span></td>
                            <td>{data['count']}</td>
                            <td><span class="score {score_class}">{fmt_score(data['avg'])}</span></td>
                            <td>{fmt_score(data['std'])}</td>
                        </tr>
"""

        html += """                    </tbody>
                </table>
            </div>
"""

    # Heuristics and Quality Metrics
    html += f"""
            <!-- Heuristic & Quality Metrics -->
            <div class="section">
                <h2 class="section-title">Heuristic & Quality Metrics</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Metric</th>
                            <th>LLM Testing</th>
                            <th>Human Testing</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td class="metric-name">Heuristic Pass Rate</td>
                            <td>{fmt_pct(llm_stats.get('heuristic_pass_rate'))}</td>
                            <td>{fmt_pct(human_stats.get('heuristic_pass_rate'))}</td>
                        </tr>
                        <tr>
                            <td class="metric-name">Critical Failure Rate</td>
                            <td>{fmt_pct(llm_stats.get('critical_failure_rate'))}</td>
                            <td>{fmt_pct(human_stats.get('critical_failure_rate'))}</td>
                        </tr>
                        <tr>
                            <td class="metric-name">Avg Conversation Length (turns)</td>
                            <td>{fmt_score(llm_stats.get('avg_turns'), 'turns')}</td>
                            <td>{fmt_score(human_stats.get('avg_turns'), 'turns')}</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <!-- Methodology -->
            <div class="methodology">
                <h3>Methodology Notes</h3>
                <ul>
                    <li><strong>LLM Testing:</strong> Simulated conversations using persona-driven LLM interactions against the chatbot, evaluated using LLM-as-Judge framework.</li>
                    <li><strong>Human Testing:</strong> Real user conversations collected through controlled study, evaluated using the same LLM-as-Judge framework for consistency.</li>
                    <li><strong>LAJ Scoring:</strong> All conversations evaluated using standardized rubric on 0-1 scale (Task Success, Clarity, Empathy, Policy Compliance).</li>
                    <li><strong>Human Self-Ratings:</strong> Participants provided subjective ratings on 1-5 scale after conversations (available for subset of metrics).</li>
                    <li><strong>Heuristic Checks:</strong> Rule-based safety checks applied consistently to all conversations (no personal info leakage, response quality, etc.).</li>
                    <li><strong>Success Threshold:</strong> Conversations with Task Success >= 0.7 considered successful.</li>
                </ul>
            </div>

            <!-- Key Insights -->
            <div class="section">
                <h2 class="section-title">Key Insights</h2>
"""

    # Generate insights
    insights = []

    # Compare success rates
    llm_success = llm_stats.get('successful_rate', 0)
    human_success = human_stats.get('successful_rate', 0)
    if llm_success and human_success:
        diff = abs(llm_success - human_success)
        if diff > 0.1:
            direction = "higher" if llm_success > human_success else "lower"
            insights.append(f"LLM testing shows {direction} success rate ({fmt_pct(llm_success)}) compared to human testing ({fmt_pct(human_success)}). This may indicate differences in conversation patterns or evaluation expectations.")

    # Compare LAJ vs human self-ratings
    human_ratings = human_stats.get('human_ratings', {})
    if human_ratings.get('count_with_ratings', 0) > 0:
        task_delta = human_stats.get('laj_vs_human', {}).get('avg_task_success_delta')
        if task_delta is not None:
            if abs(task_delta) > 0.5:
                direction = "higher" if task_delta > 0 else "lower"
                insights.append(f"LAJ ratings are {direction} than human self-ratings by {abs(task_delta):.2f} points on average (1-5 scale). This suggests potential calibration differences between AI and human evaluation standards.")

    # Compare heuristic failures
    llm_failures = llm_stats.get('critical_failure_rate', 0)
    human_failures = human_stats.get('critical_failure_rate', 0)
    if llm_failures and human_failures:
        if human_failures > llm_failures * 1.5:
            insights.append(f"Human conversations have higher critical failure rate ({fmt_pct(human_failures)}) vs LLM testing ({fmt_pct(llm_failures)}). This may reflect more unpredictable edge cases in real user behavior.")

    # Variant comparison
    llm_variants = llm_stats.get('scores_by_variant', {})
    human_variants = human_stats.get('scores_by_variant', {})
    if 'A' in llm_variants and 'B' in llm_variants:
        llm_diff = abs(llm_variants['A']['avg'] - llm_variants['B']['avg'])
        if 'A' in human_variants and 'B' in human_variants:
            human_diff = abs(human_variants['A']['avg'] - human_variants['B']['avg'])
            if llm_diff > 0.1 and human_diff > 0.1:
                insights.append(f"Both LLM and human testing show measurable differences between variants A and B, suggesting the variant changes have real impact on conversation quality.")

    if insights:
        for insight in insights:
            html += f"""                <div class="note">
                    <div class="note-text">{insight}</div>
                </div>
"""
    else:
        html += """                <div class="note">
                    <div class="note-text">Detailed insights will be generated when more data is available for comparison.</div>
                </div>
"""

    html += """            </div>
        </div>

        <footer>
            <p>Generated by LLM Testing Comparison Report Generator</p>
            <p>For questions or issues, please refer to the project documentation.</p>
        </footer>
    </div>
</body>
</html>
"""

    # Write to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    logger.info(f"HTML report written to: {output_path}")


def setup_logging(log_level: str = "INFO"):
    """Configure logging."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate HTML comparison report for LLM vs Human testing results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Basic usage
    python generate_comparison_report.py \\
        --llm-results "outputs/exp_A_*.json" \\
        --human-results outputs/human_evaluation.json \\
        --output report.html

    # Multiple LLM experiments
    python generate_comparison_report.py \\
        --llm-results "outputs/exp_A_*.json,outputs/exp_B_*.json" \\
        --human-results outputs/human_evaluation.json \\
        --output full_report.html
        """
    )

    parser.add_argument(
        "--llm-results",
        type=str,
        required=True,
        help="Glob pattern(s) for LLM experiment JSON files (comma-separated for multiple patterns)"
    )

    parser.add_argument(
        "--human-results",
        type=str,
        required=True,
        help="Path to human evaluation JSON file"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="comparison_report.html",
        help="Output path for HTML report (default: comparison_report.html)"
    )

    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)

    logger.info("Starting comparison report generation...")

    try:
        # Load LLM results (support multiple patterns)
        llm_results = []
        for pattern in args.llm_results.split(','):
            pattern = pattern.strip()
            results = load_llm_results(pattern)
            llm_results.extend(results)

        if not llm_results:
            logger.error("No LLM result files found")
            sys.exit(1)

        logger.info(f"Loaded {len(llm_results)} LLM experiment files")

        # Load human results
        human_results = load_human_results(args.human_results)

        if not human_results.get('conversations'):
            logger.error("No conversations found in human results")
            sys.exit(1)

        # Calculate statistics
        logger.info("Calculating LLM statistics...")
        llm_stats = calculate_llm_stats(llm_results)

        logger.info("Calculating human statistics...")
        human_stats = calculate_human_stats(human_results)

        # Generate report
        logger.info("Generating HTML report...")
        generate_html_report(llm_stats, human_stats, args.output)

        logger.info(f"Success! Report generated: {args.output}")

        # Print summary to console
        print("\n" + "="*80)
        print("COMPARISON REPORT GENERATED")
        print("="*80)
        print(f"Output: {args.output}")
        print(f"\nLLM Experiments: {llm_stats.get('total_conversations', 0)} conversations")
        print(f"Human Testing: {human_stats.get('total_conversations', 0)} conversations")
        print("\nOpen the HTML file in a browser to view the full comparison report.")
        print("="*80)

    except Exception as e:
        logger.error(f"Failed to generate report: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
