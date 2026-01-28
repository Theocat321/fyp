#!/usr/bin/env python3
"""
CLI entry point for running LLM testing experiments.

Usage:
    python run_experiment.py --variant A --personas all --scenarios all
    python run_experiment.py --variant B --personas persona_001_frustrated_commuter --scenarios scenario_005_network_issue
    python run_experiment.py --variant A --personas persona_001,persona_002 --scenarios all --name "quick_test"
"""
import argparse
import logging
import sys
from pathlib import Path

from config.settings import settings
from src.persona.loader import PersonaLoader
from src.scenario.loader import ScenarioLoader
from src.experiment.runner import ExperimentRunner
from src.artifacts.writer import ArtifactWriter


def setup_logging(log_level: str = "INFO"):
    """Configure logging."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("experiment.log")
        ]
    )


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run LLM testing experiments for VodaCare chatbot"
    )

    parser.add_argument(
        "--variant",
        choices=["A", "B"],
        help="System prompt variant to test (A=Kindness, B=Confirmation)"
    )

    parser.add_argument(
        "--personas",
        type=str,
        help="Persona IDs to test (comma-separated or 'all')"
    )

    parser.add_argument(
        "--scenarios",
        type=str,
        help="Scenario IDs to test (comma-separated or 'all')"
    )

    parser.add_argument(
        "--name",
        type=str,
        default="unnamed_experiment",
        help="Name for this experiment run"
    )

    parser.add_argument(
        "--list-personas",
        action="store_true",
        help="List available personas and exit"
    )

    parser.add_argument(
        "--list-scenarios",
        action="store_true",
        help="List available scenarios and exit"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be tested without running"
    )

    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )

    return parser.parse_args()


def resolve_personas(personas_arg: str, persona_loader: PersonaLoader) -> list:
    """Resolve persona argument to list of IDs."""
    if personas_arg.lower() == "all":
        return persona_loader.list_available()

    return [p.strip() for p in personas_arg.split(",")]


def resolve_scenarios(scenarios_arg: str, scenario_loader: ScenarioLoader) -> list:
    """Resolve scenario argument to list of IDs."""
    if scenarios_arg.lower() == "all":
        return scenario_loader.list_available()

    return [s.strip() for s in scenarios_arg.split(",")]


def print_summary(experiment):
    """Print experiment summary to console."""
    summary = experiment.summary

    print("\n" + "="*80)
    print("EXPERIMENT SUMMARY")
    print("="*80)
    print(f"Experiment: {experiment.experiment_name}")
    print(f"Variant: {experiment.variant}")
    print(f"Duration: {experiment.total_duration_seconds:.1f}s")
    print()

    print("CONVERSATIONS")
    print(f"  Total: {summary.total_conversations}")
    print(f"  Successful (task_success >= 0.7): {summary.successful_conversations}")
    print(f"  Success rate: {summary.successful_conversations / summary.total_conversations * 100:.1f}%")
    print()

    print("AVERAGE SCORES")
    print(f"  Task Success: {summary.avg_task_success:.3f}")
    print(f"  Clarity: {summary.avg_clarity:.3f}")
    print(f"  Empathy: {summary.avg_empathy:.3f}")
    print(f"  Policy Compliance: {summary.avg_policy_compliance:.3f}")
    print(f"  Overall Weighted: {summary.avg_overall_score:.3f}")
    print()

    print("TERMINATION REASONS")
    for reason, count in sorted(summary.termination_reasons.items()):
        pct = count / summary.total_conversations * 100
        print(f"  {reason}: {count} ({pct:.1f}%)")
    print()

    print("HEURISTIC CHECKS")
    print(f"  Pass rate: {summary.heuristic_pass_rate * 100:.1f}%")
    print(f"  Critical failures: {summary.critical_failure_rate * 100:.1f}%")
    print()

    print("PERFORMANCE")
    print(f"  Avg conversation length: {summary.avg_conversation_length:.1f} turns")
    print(f"  Avg latency: {summary.avg_latency_ms:.0f}ms")
    print()

    if summary.scores_by_persona:
        print("SCORES BY PERSONA")
        for persona_id, score in sorted(summary.scores_by_persona.items()):
            print(f"  {persona_id}: {score:.3f}")
        print()

    if summary.scores_by_scenario:
        print("SCORES BY SCENARIO")
        for scenario_id, score in sorted(summary.scores_by_scenario.items()):
            print(f"  {scenario_id}: {score:.3f}")
        print()

    print("="*80)


def main():
    """Main entry point."""
    args = parse_args()

    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    # Initialize loaders
    persona_loader = PersonaLoader()
    scenario_loader = ScenarioLoader()

    # Handle list commands
    if args.list_personas:
        print("Available personas:")
        for persona_id in persona_loader.list_available():
            print(f"  - {persona_id}")
        sys.exit(0)

    if args.list_scenarios:
        print("Available scenarios:")
        for scenario_id in scenario_loader.list_available():
            print(f"  - {scenario_id}")
        sys.exit(0)

    # Validate required arguments for non-list operations
    if not args.variant:
        logger.error("--variant is required")
        sys.exit(1)

    if not args.personas:
        logger.error("--personas is required")
        sys.exit(1)

    if not args.scenarios:
        logger.error("--scenarios is required")
        sys.exit(1)

    # Resolve personas and scenarios
    try:
        persona_ids = resolve_personas(args.personas, persona_loader)
        scenario_ids = resolve_scenarios(args.scenarios, scenario_loader)
    except Exception as e:
        logger.error(f"Error resolving personas/scenarios: {e}")
        sys.exit(1)

    # Validate
    if not persona_ids:
        logger.error("No personas specified")
        sys.exit(1)

    if not scenario_ids:
        logger.error("No scenarios specified")
        sys.exit(1)

    logger.info(f"Resolved {len(persona_ids)} personas: {', '.join(persona_ids)}")
    logger.info(f"Resolved {len(scenario_ids)} scenarios: {', '.join(scenario_ids)}")
    logger.info(f"Total conversations to run: {len(persona_ids) * len(scenario_ids)}")

    if args.dry_run:
        print("\nDRY RUN - would execute:")
        print(f"  Variant: {args.variant}")
        print(f"  Personas ({len(persona_ids)}): {', '.join(persona_ids)}")
        print(f"  Scenarios ({len(scenario_ids)}): {', '.join(scenario_ids)}")
        print(f"  Total conversations: {len(persona_ids) * len(scenario_ids)}")
        sys.exit(0)

    # Check API health
    logger.info(f"Checking VodaCare API health at {settings.vodacare_api_base_url}")
    from src.api.client import VodaCareClient
    api_client = VodaCareClient(settings.vodacare_api_base_url, settings.api_timeout)

    if not api_client.health_check():
        logger.error(
            f"VodaCare API is not accessible at {settings.vodacare_api_base_url}. "
            f"Please ensure the server is running."
        )
        sys.exit(1)

    logger.info("API health check passed")

    # Initialize runner
    runner = ExperimentRunner(
        openai_api_key=settings.openai_api_key,
        vodacare_api_url=settings.vodacare_api_base_url,
        openai_model_simulator=settings.openai_model_simulator,
        openai_model_judge=settings.openai_model_judge,
        api_timeout=settings.api_timeout,
        max_turns=settings.max_turns,
        base_seed=settings.experiment_seed,
        rubric=settings.rubric
    )

    # Run experiment
    try:
        experiment = runner.run_experiment(
            variant=args.variant,
            persona_ids=persona_ids,
            scenario_ids=scenario_ids,
            experiment_name=args.name
        )
    except KeyboardInterrupt:
        logger.warning("Experiment interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Experiment failed: {e}", exc_info=True)
        sys.exit(1)

    # Write artifacts
    writer = ArtifactWriter(settings.output_dir)

    try:
        experiment_file = writer.write_experiment(experiment)
        summary_file = writer.write_summary(experiment)

        logger.info(f"Full results: {experiment_file}")
        logger.info(f"Summary: {summary_file}")

        # Print summary to console
        print_summary(experiment)

        print(f"\nResults written to:")
        print(f"  Full: {experiment_file}")
        print(f"  Summary: {summary_file}")

    except Exception as e:
        logger.error(f"Failed to write artifacts: {e}", exc_info=True)
        sys.exit(1)

    logger.info("Experiment completed successfully")


if __name__ == "__main__":
    main()
