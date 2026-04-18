import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any
from collections import defaultdict

from src.persona.loader import PersonaLoader
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
        self.openai_api_key = openai_api_key
        self.vodacare_api_url = vodacare_api_url
        self.openai_model_simulator = openai_model_simulator
        self.openai_model_judge = openai_model_judge
        self.api_timeout = api_timeout
        self.max_turns = max_turns
        self.base_seed = base_seed
        self.rubric = rubric

        self.persona_loader = PersonaLoader()
        self.scenario_loader = ScenarioLoader()

        self.user_simulator = UserSimulator(
            api_key=openai_api_key,
            model=openai_model_simulator,
            base_seed=base_seed
        )
        self.api_client = VodaCareClient(base_url=vodacare_api_url, timeout=api_timeout)
        self.termination_checker = TerminationChecker(max_turns=max_turns)
        self.orchestrator = ConversationOrchestrator(
            user_simulator=self.user_simulator,
            api_client=self.api_client,
            termination_checker=self.termination_checker
        )
        self.llm_judge = LLMJudge(api_key=openai_api_key, model=openai_model_judge, rubric=rubric)
        self.heuristic_evaluator = HeuristicEvaluator()

    def run_experiment(
        self,
        variant: str,
        persona_ids: List[str],
        scenario_ids: List[str],
        experiment_name: str = "unnamed_experiment"
    ) -> ExperimentRun:
        experiment_id = f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        logger.info(f"Starting: {experiment_name} ({experiment_id}) — variant={variant}, "
                    f"{len(persona_ids)} personas × {len(scenario_ids)} scenarios")

        started_at = datetime.now()
        conversations: List[ConversationRun] = []

        personas = [self.persona_loader.load(pid) for pid in persona_ids]
        scenarios = [self.scenario_loader.load(sid) for sid in scenario_ids]
        total = len(personas) * len(scenarios)
        current = 0

        for persona in personas:
            for scenario in scenarios:
                current += 1
                logger.info(f"[{current}/{total}] {persona.id} × {scenario.id}")

                try:
                    conv_result = self.orchestrator.run_conversation(
                        persona=persona,
                        scenario=scenario,
                        variant=variant,
                        seed=self.base_seed + current
                    )

                    llm_scores = self.llm_judge.evaluate(
                        persona=persona,
                        scenario=scenario,
                        transcript=conv_result["transcript"]
                    )

                    heuristic_checks = self.heuristic_evaluator.evaluate(conv_result["transcript"])
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

                    conversation_run = ConversationRun(
                        run_id=f"run_{experiment_id}_{current:03d}",
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
                        f"✓ {conv_result['total_turns']} turns, "
                        f"score: {llm_scores.overall_weighted:.3f}, "
                        f"reason: {conv_result['termination'].reason}"
                    )

                except Exception as e:
                    logger.error(f"✗ {persona.id} × {scenario.id}: {e}", exc_info=True)
                    continue

        completed_at = datetime.now()
        duration = (completed_at - started_at).total_seconds()
        logger.info(f"Done in {duration:.1f}s — {len(conversations)}/{total} conversations succeeded")

        return ExperimentRun(
            experiment_id=experiment_id,
            experiment_name=experiment_name,
            variant=variant,
            conversations=conversations,
            summary=self._compute_summary(conversations),
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

    def _compute_summary(self, conversations: List[ConversationRun]) -> SummaryStatistics:
        if not conversations:
            return SummaryStatistics(
                total_conversations=0, successful_conversations=0,
                avg_task_success=0.0, avg_clarity=0.0, avg_empathy=0.0,
                avg_overall_score=0.0, termination_reasons={},
                heuristic_pass_rate=0.0, critical_failure_rate=0.0,
                avg_conversation_length=0.0, avg_latency_ms=0.0
            )

        total = len(conversations)
        successful = sum(1 for c in conversations if c.llm_evaluation.task_success >= 0.7)  # task_success >= 0.7

        avg_task_success = sum(c.llm_evaluation.task_success for c in conversations) / total
        avg_clarity = sum(c.llm_evaluation.clarity for c in conversations) / total
        avg_empathy = sum(c.llm_evaluation.empathy for c in conversations) / total
        avg_overall = sum(c.llm_evaluation.overall_weighted for c in conversations) / total

        termination_reasons = defaultdict(int)
        for c in conversations:
            termination_reasons[c.termination.reason] += 1

        heuristic_pass_rate = sum(1 for c in conversations if c.heuristic_results.all_passed) / total
        critical_failure_rate = sum(1 for c in conversations if c.heuristic_results.critical_failures) / total
        avg_length = sum(c.total_turns for c in conversations) / total
        avg_latency = sum(c.average_latency_ms for c in conversations) / total

        scores_by_persona = defaultdict(list)
        for c in conversations:
            scores_by_persona[c.persona_id].append(c.llm_evaluation.overall_weighted)
        avg_by_persona = {k: sum(v) / len(v) for k, v in scores_by_persona.items()}

        scores_by_scenario = defaultdict(list)
        for c in conversations:
            scores_by_scenario[c.scenario_id].append(c.llm_evaluation.overall_weighted)
        avg_by_scenario = {k: sum(v) / len(v) for k, v in scores_by_scenario.items()}

        return SummaryStatistics(
            total_conversations=total,
            successful_conversations=successful,
            avg_task_success=avg_task_success,
            avg_clarity=avg_clarity,
            avg_empathy=avg_empathy,
            avg_overall_score=avg_overall,
            termination_reasons=dict(termination_reasons),
            heuristic_pass_rate=heuristic_pass_rate,
            critical_failure_rate=critical_failure_rate,
            avg_conversation_length=avg_length,
            avg_latency_ms=avg_latency,
            scores_by_persona=avg_by_persona,
            scores_by_scenario=avg_by_scenario
        )
