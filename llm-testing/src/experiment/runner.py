"""Experiment runner for orchestrating full test runs."""
import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any
from collections import defaultdict

from src.persona.models import Persona
from src.persona.loader import PersonaLoader
from src.scenario.models import Scenario
from src.scenario.loader import ScenarioLoader
from src.simulator.user_simulator import UserSimulator
from src.api.client import VodaCareClient
from src.orchestrator.conversation import ConversationOrchestrator
from src.orchestrator.termination import TerminationChecker
from src.evaluator.llm_judge import LLMJudge
from src.evaluator.heuristics import HeuristicEvaluator
from src.artifacts.models import (
    ConversationRun,
    ExperimentRun,
    SummaryStatistics,
    HeuristicResults
)

logger = logging.getLogger(__name__)


class ExperimentRunner:
    """
    Orchestrates complete experiment runs across personas and scenarios.
    """

    def __init__(
        self,
        openai_api_key: str,
        vodacare_api_url: str,
        openai_model_simulator: str = "gpt-4o-mini",
        openai_model_judge: str = "gpt-4o",
        api_timeout: int = 30,
        max_turns: int = 10,
        base_seed: int = 42,
        rubric: Dict = None
    ):
        """
        Initialize the experiment runner.

        Args:
            openai_api_key: OpenAI API key
            vodacare_api_url: VodaCare API base URL
            openai_model_simulator: Model for user simulation
            openai_model_judge: Model for evaluation
            api_timeout: API timeout in seconds
            max_turns: Maximum conversation turns
            base_seed: Base random seed
            rubric: Evaluation rubric
        """
        self.openai_api_key = openai_api_key
        self.vodacare_api_url = vodacare_api_url
        self.openai_model_simulator = openai_model_simulator
        self.openai_model_judge = openai_model_judge
        self.api_timeout = api_timeout
        self.max_turns = max_turns
        self.base_seed = base_seed
        self.rubric = rubric

        # Initialize loaders
        self.persona_loader = PersonaLoader()
        self.scenario_loader = ScenarioLoader()

        # Initialize components
        self.user_simulator = UserSimulator(
            api_key=openai_api_key,
            model=openai_model_simulator,
            base_seed=base_seed
        )

        self.api_client = VodaCareClient(
            base_url=vodacare_api_url,
            timeout=api_timeout
        )

        self.termination_checker = TerminationChecker(max_turns=max_turns)

        self.orchestrator = ConversationOrchestrator(
            user_simulator=self.user_simulator,
            api_client=self.api_client,
            termination_checker=self.termination_checker
        )

        self.llm_judge = LLMJudge(
            api_key=openai_api_key,
            model=openai_model_judge,
            rubric=rubric
        )

        self.heuristic_evaluator = HeuristicEvaluator()

    def run_experiment(
        self,
        variant: str,
        persona_ids: List[str],
        scenario_ids: List[str],
        experiment_name: str = "unnamed_experiment"
    ) -> ExperimentRun:
        """
        Run a complete experiment.

        Args:
            variant: System prompt variant ("A" or "B")
            persona_ids: List of persona IDs to test
            scenario_ids: List of scenario IDs to test
            experiment_name: Name for this experiment run

        Returns:
            ExperimentRun object with all results
        """
        experiment_id = f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        logger.info("="*80)
        logger.info(f"Starting Experiment: {experiment_name}")
        logger.info(f"Experiment ID: {experiment_id}")
        logger.info(f"Variant: {variant}")
        logger.info(f"Personas: {len(persona_ids)}")
        logger.info(f"Scenarios: {len(scenario_ids)}")
        logger.info(f"Total conversations: {len(persona_ids) * len(scenario_ids)}")
        logger.info("="*80)

        started_at = datetime.now()
        conversations: List[ConversationRun] = []

        # Load personas and scenarios
        personas = [self.persona_loader.load(pid) for pid in persona_ids]
        scenarios = [self.scenario_loader.load(sid) for sid in scenario_ids]

        # Run all persona x scenario combinations
        total = len(personas) * len(scenarios)
        current = 0

        for persona in personas:
            for scenario in scenarios:
                current += 1
                logger.info(f"\n[{current}/{total}] Running: {persona.id} × {scenario.id}")

                try:
                    # Run conversation
                    conv_result = self.orchestrator.run_conversation(
                        persona=persona,
                        scenario=scenario,
                        variant=variant,
                        seed=self.base_seed + current
                    )

                    # Evaluate with LLM judge
                    llm_scores = self.llm_judge.evaluate(
                        persona=persona,
                        scenario=scenario,
                        transcript=conv_result["transcript"]
                    )

                    # Run heuristic checks
                    heuristic_checks = self.heuristic_evaluator.evaluate(
                        conv_result["transcript"]
                    )

                    # Determine critical failures
                    critical_failures = [
                        check.check_name
                        for check in heuristic_checks
                        if not check.passed and check.severity == "critical"
                    ]

                    heuristic_results = HeuristicResults(
                        checks=heuristic_checks,
                        all_passed=all(check.passed for check in heuristic_checks),
                        critical_failures=critical_failures
                    )

                    # Create conversation run record
                    run_id = f"run_{experiment_id}_{current:03d}"

                    conversation_run = ConversationRun(
                        run_id=run_id,
                        experiment_id=experiment_id,
                        persona_id=persona.id,
                        scenario_id=scenario.id,
                        variant=variant,
                        transcript=conv_result["transcript"],
                        termination=conv_result["termination"],
                        llm_evaluation=llm_scores,
                        heuristic_results=heuristic_results,
                        seed=self.base_seed + current,
                        started_at=conv_result["started_at"],
                        completed_at=conv_result["completed_at"],
                        total_turns=conv_result["total_turns"],
                        average_latency_ms=conv_result["average_latency_ms"],
                        config_snapshot={
                            "simulator_model": self.openai_model_simulator,
                            "judge_model": self.openai_model_judge,
                            "max_turns": self.max_turns
                        }
                    )

                    conversations.append(conversation_run)

                    logger.info(
                        f"✓ Completed: {conv_result['total_turns']} turns, "
                        f"score: {llm_scores.overall_weighted:.3f}, "
                        f"reason: {conv_result['termination'].reason}"
                    )

                except Exception as e:
                    logger.error(
                        f"✗ Failed: {persona.id} × {scenario.id}: {e}",
                        exc_info=True
                    )
                    continue

        completed_at = datetime.now()
        duration = (completed_at - started_at).total_seconds()

        logger.info(f"\n{'='*80}")
        logger.info(f"Experiment completed in {duration:.1f} seconds")
        logger.info(f"Successful conversations: {len(conversations)}/{total}")

        # Compute summary statistics
        summary = self._compute_summary(conversations)

        # Create experiment run record
        experiment_run = ExperimentRun(
            experiment_id=experiment_id,
            experiment_name=experiment_name,
            variant=variant,
            conversations=conversations,
            summary=summary,
            started_at=started_at,
            completed_at=completed_at,
            total_duration_seconds=duration,
            personas_tested=persona_ids,
            scenarios_tested=scenario_ids,
            seed=self.base_seed,
            openai_model_simulator=self.openai_model_simulator,
            openai_model_judge=self.openai_model_judge,
            vodacare_api_url=self.vodacare_api_url
        )

        return experiment_run

    def _compute_summary(
        self,
        conversations: List[ConversationRun]
    ) -> SummaryStatistics:
        """Compute summary statistics from conversations."""

        if not conversations:
            return SummaryStatistics(
                total_conversations=0,
                successful_conversations=0,
                avg_task_success=0.0,
                avg_clarity=0.0,
                avg_empathy=0.0,
                avg_policy_compliance=0.0,
                avg_overall_score=0.0,
                termination_reasons={},
                heuristic_pass_rate=0.0,
                critical_failure_rate=0.0,
                avg_conversation_length=0.0,
                avg_latency_ms=0.0
            )

        total = len(conversations)

        # Count successful (task_success >= 0.7)
        successful = sum(
            1 for conv in conversations
            if conv.llm_evaluation.task_success >= 0.7
        )

        # Average scores
        avg_task_success = sum(
            conv.llm_evaluation.task_success for conv in conversations
        ) / total

        avg_clarity = sum(
            conv.llm_evaluation.clarity for conv in conversations
        ) / total

        avg_empathy = sum(
            conv.llm_evaluation.empathy for conv in conversations
        ) / total

        avg_policy_compliance = sum(
            conv.llm_evaluation.policy_compliance for conv in conversations
        ) / total

        avg_overall = sum(
            conv.llm_evaluation.overall_weighted for conv in conversations
        ) / total

        # Termination reasons
        termination_reasons = defaultdict(int)
        for conv in conversations:
            termination_reasons[conv.termination.reason] += 1

        # Heuristic metrics
        heuristic_pass_rate = sum(
            1 for conv in conversations
            if conv.heuristic_results.all_passed
        ) / total

        critical_failure_rate = sum(
            1 for conv in conversations
            if conv.heuristic_results.critical_failures
        ) / total

        # Performance metrics
        avg_length = sum(
            conv.total_turns for conv in conversations
        ) / total

        avg_latency = sum(
            conv.average_latency_ms for conv in conversations
        ) / total

        # Scores by persona
        scores_by_persona = defaultdict(list)
        for conv in conversations:
            scores_by_persona[conv.persona_id].append(
                conv.llm_evaluation.overall_weighted
            )

        avg_by_persona = {
            persona_id: sum(scores) / len(scores)
            for persona_id, scores in scores_by_persona.items()
        }

        # Scores by scenario
        scores_by_scenario = defaultdict(list)
        for conv in conversations:
            scores_by_scenario[conv.scenario_id].append(
                conv.llm_evaluation.overall_weighted
            )

        avg_by_scenario = {
            scenario_id: sum(scores) / len(scores)
            for scenario_id, scores in scores_by_scenario.items()
        }

        return SummaryStatistics(
            total_conversations=total,
            successful_conversations=successful,
            avg_task_success=avg_task_success,
            avg_clarity=avg_clarity,
            avg_empathy=avg_empathy,
            avg_policy_compliance=avg_policy_compliance,
            avg_overall_score=avg_overall,
            termination_reasons=dict(termination_reasons),
            heuristic_pass_rate=heuristic_pass_rate,
            critical_failure_rate=critical_failure_rate,
            avg_conversation_length=avg_length,
            avg_latency_ms=avg_latency,
            scores_by_persona=avg_by_persona,
            scores_by_scenario=avg_by_scenario
        )
