"""Heuristic evaluators for conversation quality."""
import logging
import re
from typing import List
from src.artifacts.models import ConversationTurn, HeuristicCheckResult

logger = logging.getLogger(__name__)

# Valid Vodafone plans (based on plan catalog in sys_prompt_a.txt and sys_prompt_b.txt)
VALID_PLANS = [
    "8",   # Lite Mobile
    "15",  # Everyday Mobile
    "25",  # Streamer Plan
    "32",  # Unlimited Core
    "42",  # Unlimited Max
    "55",  # Family Connect
    "70",  # Pro+ Mobile
    "85"   # International Traveller
]


class HeuristicEvaluator:
    """
    Performs deterministic heuristic checks on conversation quality.
    """

    def __init__(self):
        """Initialize the heuristic evaluator."""
        pass

    def evaluate(self, transcript: List[ConversationTurn]) -> List[HeuristicCheckResult]:
        """
        Run all heuristic checks on a conversation.

        Args:
            transcript: List of conversation turns

        Returns:
            List of heuristic check results
        """
        results = []

        # Run each check
        results.append(self._check_hallucinated_plans(transcript))
        results.append(self._check_contradictions(transcript))
        results.append(self._check_response_length(transcript))
        results.append(self._check_escalation_appropriateness(transcript))

        return results

    def _check_hallucinated_plans(
        self,
        transcript: List[ConversationTurn]
    ) -> HeuristicCheckResult:
        """
        Check if assistant mentioned any non-existent plans.

        Args:
            transcript: Conversation turns

        Returns:
            Check result
        """
        assistant_messages = [
            turn.message
            for turn in transcript
            if turn.speaker == "assistant"
        ]

        full_text = " ".join(assistant_messages)

        # Look for price mentions in format £XX or XX
        price_pattern = r'£(\d+)|(\d+)\s*(?:per month|monthly|\/month|\/mo)'

        mentioned_prices = set()
        for match in re.finditer(price_pattern, full_text, re.IGNORECASE):
            price = match.group(1) or match.group(2)
            mentioned_prices.add(price)

        # Check if any mentioned prices are not in valid plans
        invalid_prices = mentioned_prices - set(VALID_PLANS)

        if invalid_prices:
            return HeuristicCheckResult(
                check_name="no_hallucinated_plans",
                passed=False,
                details=f"Mentioned invalid plan prices: {', '.join(sorted(invalid_prices))}",
                severity="critical"
            )

        return HeuristicCheckResult(
            check_name="no_hallucinated_plans",
            passed=True,
            details=f"All mentioned prices are valid: {', '.join(sorted(mentioned_prices))}",
            severity="info"
        )

    def _check_contradictions(
        self,
        transcript: List[ConversationTurn]
    ) -> HeuristicCheckResult:
        """
        Check for contradictory information across turns.

        Args:
            transcript: Conversation turns

        Returns:
            Check result
        """
        assistant_messages = [
            (turn.turn_number, turn.message)
            for turn in transcript
            if turn.speaker == "assistant"
        ]

        # Simple check: look for contradictory yes/no statements
        # This is a basic implementation - could be more sophisticated

        contradictions_found = []

        # Check for price contradictions
        price_statements = {}
        for turn_num, message in assistant_messages:
            # Look for plan prices
            matches = re.finditer(
                r'£(\d+)\s+(?:per month|monthly|plan)',
                message,
                re.IGNORECASE
            )
            for match in matches:
                price = match.group(1)
                context = match.group(0)
                if price in price_statements:
                    prev_turn, prev_context = price_statements[price]
                    if prev_context.lower() != context.lower():
                        contradictions_found.append(
                            f"Price £{price} mentioned differently in turns {prev_turn} and {turn_num}"
                        )
                else:
                    price_statements[price] = (turn_num, context)

        if contradictions_found:
            return HeuristicCheckResult(
                check_name="no_contradictions",
                passed=False,
                details="; ".join(contradictions_found),
                severity="critical"
            )

        return HeuristicCheckResult(
            check_name="no_contradictions",
            passed=True,
            details="No obvious contradictions detected",
            severity="info"
        )

    def _check_response_length(
        self,
        transcript: List[ConversationTurn]
    ) -> HeuristicCheckResult:
        """
        Check if responses are appropriate length (50-300 words).

        Args:
            transcript: Conversation turns

        Returns:
            Check result
        """
        assistant_messages = [
            turn.message
            for turn in transcript
            if turn.speaker == "assistant"
        ]

        issues = []
        for i, message in enumerate(assistant_messages, 1):
            word_count = len(message.split())

            if word_count < 30:
                issues.append(f"Turn {i}: Too short ({word_count} words)")
            elif word_count > 400:
                issues.append(f"Turn {i}: Too long ({word_count} words)")

        if issues:
            return HeuristicCheckResult(
                check_name="appropriate_response_length",
                passed=False,
                details="; ".join(issues),
                severity="warning"
            )

        return HeuristicCheckResult(
            check_name="appropriate_response_length",
            passed=True,
            details="All responses within acceptable length range",
            severity="info"
        )

    def _check_escalation_appropriateness(
        self,
        transcript: List[ConversationTurn]
    ) -> HeuristicCheckResult:
        """
        Check if escalation was offered when appropriate.

        Args:
            transcript: Conversation turns

        Returns:
            Check result
        """
        # Look for signs user needed escalation
        user_messages = [
            turn.message.lower()
            for turn in transcript
            if turn.speaker == "user"
        ]

        escalation_signals = [
            "speak to someone", "human", "person", "supervisor",
            "manager", "not helping", "useless", "waste of time",
            "escalate"
        ]

        user_requested_escalation = any(
            any(signal in msg for signal in escalation_signals)
            for msg in user_messages
        )

        # Check if assistant offered escalation
        assistant_messages = [
            turn.message.lower()
            for turn in transcript
            if turn.speaker == "assistant"
        ]

        escalation_offered = any(
            any(phrase in msg for phrase in [
                "transfer you", "speak to", "specialist", "team member",
                "human agent", "escalate", "supervisor"
            ])
            for msg in assistant_messages
        )

        if user_requested_escalation and not escalation_offered:
            return HeuristicCheckResult(
                check_name="escalation_appropriateness",
                passed=False,
                details="User requested escalation but it was not offered",
                severity="warning"
            )

        return HeuristicCheckResult(
            check_name="escalation_appropriateness",
            passed=True,
            details="Escalation handling appropriate" if user_requested_escalation
                   else "No escalation needed",
            severity="info"
        )
