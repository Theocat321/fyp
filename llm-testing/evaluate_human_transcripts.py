#!/usr/bin/env python3
"""
Evaluate human conversation transcripts using LLM-as-Judge framework.

This script fetches real user conversations from Supabase, evaluates them using
the same LLM judge and heuristic systems as simulated conversations, and compares
human self-ratings with LAJ ratings.

Usage:
    # Evaluate a specific session
    python3 evaluate_human_transcripts.py --session-id abc123

    # Evaluate all sessions
    python3 evaluate_human_transcripts.py --all

    # Filter by participant group
    python3 evaluate_human_transcripts.py --all --participant-group A

    # Save results to file
    python3 evaluate_human_transcripts.py --all --output results.json
"""
import argparse
import json
import logging
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

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
from src.persona.models import Persona, BehavioralTraits, ConversationParameters
from src.scenario.models import Scenario, SuccessCriteria

# Add server app to path to use its storage module
server_path = Path(__file__).parent.parent / "server"
sys.path.insert(0, str(server_path))

from app.storage import SupabaseStore


logger = logging.getLogger(__name__)


class HumanTranscriptEvaluator:
    """Evaluates human conversation transcripts using LLM-as-Judge framework."""

    def __init__(self):
        """Initialize evaluator with LLM judge and heuristics."""
        self.llm_judge = LLMJudge(
            api_key=settings.openai_api_key,
            model=settings.openai_model_judge,
            rubric=settings.rubric
        )
        self.heuristic_evaluator = HeuristicEvaluator()
        self.store = SupabaseStore()

        if not self.store.is_configured():
            raise RuntimeError(
                "Supabase not configured. Set SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables."
            )

    def fetch_messages(
        self,
        session_id: Optional[str] = None,
        participant_group: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch messages from Supabase.

        Args:
            session_id: Optional specific session to fetch
            participant_group: Optional filter by participant group (A or B)

        Returns:
            List of message records from database
        """
        logger.info("Fetching messages from Supabase...")

        # Fetch all messages (we'll filter in Python)
        messages, status = self.store.select_rows(
            table="messages",
            params={},
            select="*",
            order="created_at.asc"
        )

        if status != 200:
            raise RuntimeError(f"Failed to fetch messages (status {status})")

        logger.info(f"Fetched {len(messages)} total messages")

        # Filter out simulated conversations
        real_messages = [
            msg for msg in messages
            if not msg.get('session_id', '').startswith('sim_')
        ]

        # Apply filters
        if session_id:
            real_messages = [
                msg for msg in real_messages
                if msg.get('session_id') == session_id
            ]

        if participant_group:
            real_messages = [
                msg for msg in real_messages
                if msg.get('participant_group') == participant_group
            ]

        logger.info(f"Filtered to {len(real_messages)} real user messages")
        return real_messages

    def fetch_feedback(
        self,
        session_id: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Fetch feedback records from Supabase.

        Args:
            session_id: Optional specific session to fetch

        Returns:
            Dictionary mapping session_id to feedback record
        """
        logger.info("Fetching feedback from Supabase...")

        params = {}
        if session_id:
            params['session_id'] = session_id

        feedback_records, status = self.store.select_rows(
            table="feedback",
            params=params,
            select="*"
        )

        if status != 200:
            logger.warning(f"Failed to fetch feedback (status {status})")
            return {}

        logger.info(f"Fetched {len(feedback_records)} feedback records")

        # Map by session_id
        feedback_map = {}
        for record in feedback_records:
            sid = record.get('session_id')
            if sid:
                feedback_map[sid] = record

        return feedback_map

    def fetch_participants(
        self,
        participant_group: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Fetch participant records from Supabase.

        Args:
            participant_group: Optional filter by group (A or B)

        Returns:
            Dictionary mapping participant_id to participant record
        """
        logger.info("Fetching participants from Supabase...")

        params = {}
        if participant_group:
            params['group'] = participant_group

        participant_records, status = self.store.select_rows(
            table="participants",
            params=params,
            select="*"
        )

        if status != 200:
            logger.warning(f"Failed to fetch participants (status {status})")
            return {}

        logger.info(f"Fetched {len(participant_records)} participant records")

        # Map by participant_id
        participant_map = {}
        for record in participant_records:
            pid = record.get('participant_id')
            if pid:
                participant_map[pid] = record

        return participant_map

    def group_messages_by_session(
        self,
        messages: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group messages by session_id.

        Args:
            messages: List of message records

        Returns:
            Dictionary mapping session_id to list of messages
        """
        sessions = defaultdict(list)
        for msg in messages:
            session_id = msg.get('session_id')
            if session_id:
                sessions[session_id].append(msg)

        return dict(sessions)

    def build_transcript(
        self,
        messages: List[Dict[str, Any]]
    ) -> List[ConversationTurn]:
        """
        Build conversation transcript from messages.

        Args:
            messages: List of message records for a session

        Returns:
            List of ConversationTurn objects
        """
        # Sort by timestamp
        sorted_messages = sorted(
            messages,
            key=lambda x: x.get('created_at', '')
        )

        transcript = []
        turn_number = 1

        for msg in sorted_messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            created_at = msg.get('created_at')

            # Parse timestamp
            try:
                timestamp = datetime.fromisoformat(created_at) if created_at else datetime.now()
            except (ValueError, TypeError):
                timestamp = datetime.now()

            # Create turn
            turn = ConversationTurn(
                turn_number=turn_number,
                speaker=role,
                message=content,
                timestamp=timestamp
            )
            transcript.append(turn)

            # Increment turn after assistant response
            if role == 'assistant':
                turn_number += 1

        return transcript

    def create_placeholder_persona(self) -> Persona:
        """Create a generic persona placeholder for real users."""
        return Persona(
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

    def create_placeholder_scenario(self, scenario_id: Optional[str] = None) -> Scenario:
        """Create a generic scenario placeholder for real conversations."""
        scenario_name = scenario_id if scenario_id else "real_conversation"
        return Scenario(
            id=scenario_name,
            name=f"Real User Support Conversation: {scenario_name}",
            topic="support",
            context="Real customer support interaction",
            happy_path_steps=[],
            success_criteria=SuccessCriteria(
                must_provide=["Resolution or clear next steps"],
                must_avoid=["Leaving user without help"]
            )
        )

    def evaluate_conversation(
        self,
        session_id: str,
        transcript: List[ConversationTurn],
        participant_group: str,
        participant_id: str,
        scenario_id: Optional[str] = None,
        feedback: Optional[Dict[str, Any]] = None
    ) -> ConversationRun:
        """
        Evaluate a single conversation using LLM judge and heuristics.

        Args:
            session_id: Session identifier
            transcript: List of conversation turns
            participant_group: Variant group (A or B)
            participant_id: Participant identifier
            scenario_id: Optional scenario identifier
            feedback: Optional feedback record for comparison

        Returns:
            ConversationRun with evaluation results
        """
        logger.info(f"Evaluating conversation: {session_id}")

        # Create placeholders
        placeholder_persona = self.create_placeholder_persona()
        placeholder_scenario = self.create_placeholder_scenario(scenario_id)

        # Evaluate with LLM judge
        try:
            llm_scores = self.llm_judge.evaluate(
                persona=placeholder_persona,
                scenario=placeholder_scenario,
                transcript=transcript
            )
        except Exception as e:
            logger.error(f"LLM judge failed for {session_id}: {e}")
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
        total_turns = max([t.turn_number for t in transcript]) if transcript else 0
        termination = TerminationInfo(
            reason="natural_end",
            turn_number=total_turns,
            details="Real user conversation ended naturally"
        )

        # Calculate average latency (unknown for real users)
        avg_latency = 0.0

        # Create config snapshot with feedback comparison if available
        config_snapshot = {
            "source": "human_transcript",
            "judge_model": settings.openai_model_judge,
            "scenario_id": scenario_id or "unknown"
        }

        # Add feedback comparison to config if available
        if feedback:
            config_snapshot["human_feedback"] = self._extract_feedback_ratings(feedback)
            config_snapshot["laj_vs_human_comparison"] = self._compare_ratings(
                llm_scores, feedback
            )

        # Create conversation run
        run = ConversationRun(
            run_id=f"human_{session_id}",
            experiment_id="human_transcripts",
            persona_id="real_user",
            scenario_id=scenario_id or "real_conversation",
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
            config_snapshot=config_snapshot
        )

        logger.info(
            f"Evaluated {session_id}: "
            f"overall={llm_scores.overall_weighted:.3f}, "
            f"turns={total_turns}"
        )

        return run

    def _extract_feedback_ratings(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant ratings from feedback record."""
        return {
            "rating_overall": feedback.get("rating_overall"),
            "rating_helpfulness": feedback.get("rating_helpfulness"),
            "rating_friendliness": feedback.get("rating_friendliness"),
            "rating_task_success": feedback.get("rating_task_success"),
            "rating_clarity": feedback.get("rating_clarity"),
            "rating_empathy": feedback.get("rating_empathy"),
            "rating_accuracy": feedback.get("rating_accuracy"),
            "resolved": feedback.get("resolved"),
            "recommend_nps": feedback.get("recommend_nps")
        }

    def _compare_ratings(
        self,
        llm_scores: EvaluationScores,
        feedback: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare LAJ ratings with human self-ratings.

        Converts LAJ scores (0-1) to 1-5 scale for comparison.
        """
        # Convert LAJ scores to 1-5 scale
        laj_task_success = round(llm_scores.task_success * 4 + 1, 1)
        laj_clarity = round(llm_scores.clarity * 4 + 1, 1)
        laj_empathy = round(llm_scores.empathy * 4 + 1, 1)

        # Get human ratings
        human_task_success = feedback.get("rating_task_success")
        human_clarity = feedback.get("rating_clarity")
        human_empathy = feedback.get("rating_empathy")

        comparison = {
            "task_success": {
                "laj": laj_task_success,
                "human": human_task_success,
                "delta": round(laj_task_success - human_task_success, 2) if human_task_success else None
            },
            "clarity": {
                "laj": laj_clarity,
                "human": human_clarity,
                "delta": round(laj_clarity - human_clarity, 2) if human_clarity else None
            },
            "empathy": {
                "laj": laj_empathy,
                "human": human_empathy,
                "delta": round(laj_empathy - human_empathy, 2) if human_empathy else None
            }
        }

        return comparison

    def compute_summary(
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

        # By scenario
        scores_by_scenario = defaultdict(list)
        for conv in conversations:
            scores_by_scenario[conv.scenario_id].append(conv.llm_evaluation.overall_weighted)

        avg_by_scenario = {
            scenario: sum(scores) / len(scores)
            for scenario, scores in scores_by_scenario.items()
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
            scores_by_persona=avg_by_variant,
            scores_by_scenario=avg_by_scenario
        )


def setup_logging(log_level: str = "INFO"):
    """Configure logging."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Evaluate human conversation transcripts using LLM-as-Judge"
    )

    parser.add_argument(
        "--session-id",
        type=str,
        help="Evaluate a specific session ID"
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Evaluate all sessions"
    )

    parser.add_argument(
        "--participant-group",
        type=str,
        choices=["A", "B"],
        help="Filter by participant group (A or B)"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="outputs/human_evaluation.json",
        help="Output path for evaluation results"
    )

    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)

    # Validate arguments
    if not args.all and not args.session_id:
        logger.error("Must specify either --all or --session-id")
        parser.print_help()
        sys.exit(1)

    # Initialize evaluator
    try:
        evaluator = HumanTranscriptEvaluator()
    except RuntimeError as e:
        logger.error(str(e))
        sys.exit(1)

    # Fetch data
    try:
        messages = evaluator.fetch_messages(
            session_id=args.session_id,
            participant_group=args.participant_group
        )

        if not messages:
            logger.error("No messages found matching criteria")
            sys.exit(1)

        feedback_map = evaluator.fetch_feedback(session_id=args.session_id)
        participant_map = evaluator.fetch_participants(
            participant_group=args.participant_group
        )

    except Exception as e:
        logger.error(f"Failed to fetch data from Supabase: {e}", exc_info=True)
        sys.exit(1)

    # Group messages by session
    sessions = evaluator.group_messages_by_session(messages)
    logger.info(f"Found {len(sessions)} sessions to evaluate")

    # Evaluate each session
    evaluated_conversations = []
    for session_id, session_messages in sessions.items():
        try:
            # Build transcript
            transcript = evaluator.build_transcript(session_messages)

            if not transcript:
                logger.warning(f"Skipping {session_id}: empty transcript")
                continue

            # Get metadata
            first_msg = session_messages[0]
            participant_group = first_msg.get('participant_group', 'unknown')
            participant_id = first_msg.get('participant_id', 'unknown')

            # Get scenario from participant record
            scenario_id = None
            if participant_id in participant_map:
                scenario_id = participant_map[participant_id].get('scenario_id')

            # Get feedback
            feedback = feedback_map.get(session_id)

            # Evaluate
            run = evaluator.evaluate_conversation(
                session_id=session_id,
                transcript=transcript,
                participant_group=participant_group,
                participant_id=participant_id,
                scenario_id=scenario_id,
                feedback=feedback
            )
            evaluated_conversations.append(run)

        except Exception as e:
            logger.error(
                f"Failed to evaluate {session_id}: {e}",
                exc_info=True
            )
            continue

    if not evaluated_conversations:
        logger.error("No conversations were successfully evaluated")
        sys.exit(1)

    # Compute summary
    summary = evaluator.compute_summary(evaluated_conversations)

    # Create experiment run
    experiment = ExperimentRun(
        experiment_id=f"human_transcripts_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        experiment_name="human_transcript_evaluation",
        variant="mixed" if not args.participant_group else args.participant_group,
        conversations=evaluated_conversations,
        summary=summary,
        started_at=datetime.now(),
        completed_at=datetime.now(),
        total_duration_seconds=0,
        personas_tested=["real_user"],
        scenarios_tested=list(set(c.scenario_id for c in evaluated_conversations)),
        seed=0,
        openai_model_simulator="N/A",
        openai_model_judge=settings.openai_model_judge,
        vodacare_api_url="N/A"
    )

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(experiment.model_dump(mode='json'), f, indent=2, default=str)

    logger.info(f"Evaluation results written to {output_path}")

    # Print summary to console
    print("\n" + "="*80)
    print("HUMAN TRANSCRIPT EVALUATION SUMMARY")
    print("="*80)
    print(f"Total conversations: {summary.total_conversations}")
    print(f"Successful (task_success >= 0.7): {summary.successful_conversations}")
    print()
    print("AVERAGE LAJ SCORES")
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

    if summary.scores_by_persona:
        print("SCORES BY VARIANT")
        for variant, score in sorted(summary.scores_by_persona.items()):
            print(f"  {variant}: {score:.3f}")
        print()

    if summary.scores_by_scenario:
        print("SCORES BY SCENARIO")
        for scenario, score in sorted(summary.scores_by_scenario.items()):
            print(f"  {scenario}: {score:.3f}")
        print()

    # Print LAJ vs Human comparison summary if available
    comparisons = []
    for conv in evaluated_conversations:
        if "laj_vs_human_comparison" in conv.config_snapshot:
            comparisons.append(conv.config_snapshot["laj_vs_human_comparison"])

    if comparisons:
        print("LAJ vs HUMAN RATINGS COMPARISON")
        print(f"  Conversations with feedback: {len(comparisons)}")

        # Calculate average deltas
        task_deltas = [c["task_success"]["delta"] for c in comparisons if c["task_success"]["delta"] is not None]
        clarity_deltas = [c["clarity"]["delta"] for c in comparisons if c["clarity"]["delta"] is not None]
        empathy_deltas = [c["empathy"]["delta"] for c in comparisons if c["empathy"]["delta"] is not None]

        if task_deltas:
            print(f"  Avg Task Success delta: {sum(task_deltas)/len(task_deltas):+.2f}")
        if clarity_deltas:
            print(f"  Avg Clarity delta: {sum(clarity_deltas)/len(clarity_deltas):+.2f}")
        if empathy_deltas:
            print(f"  Avg Empathy delta: {sum(empathy_deltas)/len(empathy_deltas):+.2f}")
        print()

    print("="*80)


if __name__ == "__main__":
    main()
