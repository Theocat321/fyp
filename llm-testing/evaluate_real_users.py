#!/usr/bin/env python3
"""
Evaluate real user conversations using the same pipeline as simulated users.

This ensures real and simulated users are evaluated consistently for comparison.

Usage:
    python3 evaluate_real_users.py --csv real_conversations.csv --output real_evaluation.json
"""
import argparse
import csv
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from collections import defaultdict

from config.settings import settings
from src.evaluator.llm_judge import LLMJudge
from src.evaluator.heuristics import HeuristicEvaluator
from src.artifacts.models import (
    ConversationTurn,
    ConversationRun,
    EvaluationScores,
    HeuristicResults,
    TerminationInfo,
    ExperimentRun,
    SummaryStatistics
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RealUserEvaluator:
    """Evaluates real user conversations using same pipeline as simulated users."""

    def __init__(self):
        """Initialize evaluator with LLM judge and heuristics."""
        self.llm_judge = LLMJudge(
            api_key=settings.openai_api_key,
            model=settings.openai_model_judge,
            rubric=settings.rubric
        )
        self.heuristic_evaluator = HeuristicEvaluator()

    def load_conversations_from_csv(self, csv_path: Path) -> List[Dict[str, Any]]:
        """
        Load conversations from CSV file.

        Expected CSV format:
        session_id,participant_id,participant_group,role,content,created_at

        Returns:
            List of conversation dicts grouped by session_id
        """
        logger.info(f"Loading conversations from {csv_path}")

        # Read CSV
        rows = []
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)

        logger.info(f"Loaded {len(rows)} messages from CSV")

        # Group by session
        sessions = defaultdict(list)
        for row in rows:
            session_id = row['session_id']
            sessions[session_id].append(row)

        # Convert to conversation format
        conversations = []
        for session_id, messages in sessions.items():
            # Sort by timestamp
            messages.sort(key=lambda x: x.get('created_at', ''))

            # Build transcript
            transcript = []
            turn_number = 1
            participant_group = None
            participant_id = None

            for i, msg in enumerate(messages):
                role = msg['role']
                content = msg['content']

                # Track participant info
                if not participant_group:
                    participant_group = msg.get('participant_group', 'unknown')
                if not participant_id:
                    participant_id = msg.get('participant_id', 'unknown')

                # Create turn (user and assistant share same turn number)
                turn = ConversationTurn(
                    turn_number=turn_number if role == 'user' else turn_number,
                    speaker=role,
                    message=content,
                    timestamp=datetime.fromisoformat(msg['created_at']) if msg.get('created_at') else datetime.now()
                )
                transcript.append(turn)

                # Increment turn after assistant response
                if role == 'assistant':
                    turn_number += 1

            conversations.append({
                'session_id': session_id,
                'participant_id': participant_id,
                'participant_group': participant_group,
                'transcript': transcript
            })

        logger.info(f"Parsed {len(conversations)} conversations")
        return conversations

    def evaluate_conversation(
        self,
        session_id: str,
        transcript: List[ConversationTurn],
        participant_group: str,
        participant_id: str
    ) -> ConversationRun:
        """
        Evaluate a single conversation using LLM judge and heuristics.

        Args:
            session_id: Session identifier
            transcript: List of conversation turns
            participant_group: Variant group
            participant_id: Participant identifier

        Returns:
            ConversationRun with evaluation results
        """
        logger.info(f"Evaluating conversation: {session_id}")

        # We don't have persona/scenario for real users, so create placeholders
        # The LLM judge will evaluate based on transcript only
        from src.persona.models import Persona, BehavioralTraits, ConversationParameters
        from src.scenario.models import Scenario, SuccessCriteria

        # Create a generic persona placeholder
        placeholder_persona = Persona(
            id="real_user",
            name="Real User",
            age=0,
            location="Unknown",
            demographics={},
            personality={},
            behavioral_traits=BehavioralTraits(
                patience_level="unknown",
                tone=["natural"],
                response_style="real user conversation",
                detail_preference="unknown"
            ),
            goals=["Resolve support issue"],
            conversation_parameters=ConversationParameters(
                max_patience_turns=10,
                escalation_threshold=5,
                tech_literacy="unknown"
            ),
            seed_utterance=""
        )

        # Create a generic scenario placeholder
        placeholder_scenario = Scenario(
            id="real_conversation",
            name="Real User Support Conversation",
            topic="support",
            context="Real customer support interaction",
            happy_path_steps=[],
            success_criteria=SuccessCriteria(
                must_provide=["Resolution or clear next steps"],
                must_avoid=["Leaving user without help"]
            )
        )

        # Evaluate with LLM judge
        try:
            llm_scores = self.llm_judge.evaluate(
                persona=placeholder_persona,
                scenario=placeholder_scenario,
                transcript=transcript
            )
        except Exception as e:
            logger.error(f"LLM judge failed: {e}")
            llm_scores = EvaluationScores(
                task_success=0.0,
                clarity=0.0,
                empathy=0.0,
                policy_compliance=0.0,
                overall_weighted=0.0,
                rationale=f"Evaluation failed: {str(e)}"
            )

        # Run heuristic checks
        heuristic_checks = self.heuristic_evaluator.evaluate(transcript)
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

        # Determine termination reason
        total_turns = max([t.turn_number for t in transcript])
        termination = TerminationInfo(
            reason="natural_end",
            turn_number=total_turns,
            details="Real user conversation ended naturally"
        )

        # Calculate average latency (unknown for real users)
        avg_latency = 0.0

        # Create conversation run
        run = ConversationRun(
            run_id=f"real_{session_id}",
            experiment_id="real_users",
            persona_id="real_user",
            scenario_id="real_conversation",
            variant=participant_group,
            transcript=transcript,
            termination=termination,
            llm_evaluation=llm_scores,
            heuristic_results=heuristic_results,
            seed=0,
            started_at=transcript[0].timestamp if transcript else datetime.now(),
            completed_at=transcript[-1].timestamp if transcript else datetime.now(),
            total_turns=total_turns,
            average_latency_ms=avg_latency,
            config_snapshot={
                "source": "real_user_data",
                "judge_model": settings.openai_model_judge
            }
        )

        logger.info(
            f"✓ Evaluated {session_id}: "
            f"overall={llm_scores.overall_weighted:.3f}, "
            f"turns={total_turns}"
        )

        return run

    def compute_summary(self, conversations: List[ConversationRun]) -> SummaryStatistics:
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

        # Count successful
        successful = sum(
            1 for conv in conversations
            if conv.llm_evaluation.task_success >= 0.7
        )

        # Average scores
        avg_task_success = sum(c.llm_evaluation.task_success for c in conversations) / total
        avg_clarity = sum(c.llm_evaluation.clarity for c in conversations) / total
        avg_empathy = sum(c.llm_evaluation.empathy for c in conversations) / total
        avg_policy_compliance = sum(c.llm_evaluation.policy_compliance for c in conversations) / total
        avg_overall = sum(c.llm_evaluation.overall_weighted for c in conversations) / total

        # Termination reasons
        termination_reasons = defaultdict(int)
        for conv in conversations:
            termination_reasons[conv.termination.reason] += 1

        # Heuristic metrics
        heuristic_pass_rate = sum(
            1 for conv in conversations if conv.heuristic_results.all_passed
        ) / total

        critical_failure_rate = sum(
            1 for conv in conversations if conv.heuristic_results.critical_failures
        ) / total

        # Performance
        avg_length = sum(c.total_turns for c in conversations) / total
        avg_latency = sum(c.average_latency_ms for c in conversations) / total

        # By variant
        scores_by_variant = defaultdict(list)
        for conv in conversations:
            scores_by_variant[conv.variant].append(conv.llm_evaluation.overall_weighted)

        avg_by_variant = {
            variant: sum(scores) / len(scores)
            for variant, scores in scores_by_variant.items()
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
            scores_by_persona=avg_by_variant  # Using variant as grouping
        )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Evaluate real user conversations using same pipeline as simulated users"
    )

    parser.add_argument(
        "--csv",
        type=str,
        required=True,
        help="Path to CSV file with real conversations"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="outputs/real_user_evaluation.json",
        help="Output path for evaluation results"
    )

    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Only output summary statistics, not full conversations"
    )

    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        sys.exit(1)

    # Initialize evaluator
    evaluator = RealUserEvaluator()

    # Load conversations
    raw_conversations = evaluator.load_conversations_from_csv(csv_path)

    if not raw_conversations:
        logger.error("No conversations found in CSV")
        sys.exit(1)

    # Evaluate each conversation
    evaluated_conversations = []
    for conv_data in raw_conversations:
        try:
            run = evaluator.evaluate_conversation(
                session_id=conv_data['session_id'],
                transcript=conv_data['transcript'],
                participant_group=conv_data['participant_group'],
                participant_id=conv_data['participant_id']
            )
            evaluated_conversations.append(run)
        except Exception as e:
            logger.error(
                f"Failed to evaluate {conv_data['session_id']}: {e}",
                exc_info=True
            )
            continue

    # Compute summary
    summary = evaluator.compute_summary(evaluated_conversations)

    # Create experiment run
    experiment = ExperimentRun(
        experiment_id=f"real_users_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        experiment_name="real_user_evaluation",
        variant="mixed",  # Real users may have mixed variants
        conversations=evaluated_conversations,
        summary=summary,
        started_at=datetime.now(),
        completed_at=datetime.now(),
        total_duration_seconds=0,
        personas_tested=["real_user"],
        scenarios_tested=["real_conversation"],
        seed=0,
        openai_model_simulator="N/A",
        openai_model_judge=settings.openai_model_judge,
        vodacare_api_url="N/A"
    )

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.summary_only:
        # Write summary only
        with open(output_path, 'w') as f:
            json.dump(summary.model_dump(mode='json'), f, indent=2, default=str)
        logger.info(f"Summary written to {output_path}")
    else:
        # Write full experiment
        with open(output_path, 'w') as f:
            json.dump(experiment.model_dump(mode='json'), f, indent=2, default=str)
        logger.info(f"Full evaluation written to {output_path}")

    # Print summary to console
    print("\n" + "="*80)
    print("REAL USER EVALUATION SUMMARY")
    print("="*80)
    print(f"Total conversations: {summary.total_conversations}")
    print(f"Successful (task_success >= 0.7): {summary.successful_conversations}")
    print()
    print("AVERAGE SCORES")
    print(f"  Task Success: {summary.avg_task_success:.3f}")
    print(f"  Clarity: {summary.avg_clarity:.3f}")
    print(f"  Empathy: {summary.avg_empathy:.3f}")
    print(f"  Policy Compliance: {summary.avg_policy_compliance:.3f}")
    print(f"  Overall Weighted: {summary.avg_overall_score:.3f}")
    print()
    print("HEURISTIC CHECKS")
    print(f"  Pass rate: {summary.heuristic_pass_rate * 100:.1f}%")
    print(f"  Critical failures: {summary.critical_failure_rate * 100:.1f}%")
    print()
    print("="*80)


if __name__ == "__main__":
    main()
