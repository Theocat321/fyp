"""Conversation orchestrator for running multi-turn interactions."""
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any

from src.persona.models import Persona
from src.scenario.models import Scenario
from src.simulator.user_simulator import UserSimulator
from src.api.client import VodaCareClient
from src.orchestrator.termination import TerminationChecker
from src.artifacts.models import ConversationTurn, TerminationInfo

logger = logging.getLogger(__name__)


class ConversationOrchestrator:
    """
    Orchestrates multi-turn conversations between simulated user and chatbot.
    """

    def __init__(
        self,
        user_simulator: UserSimulator,
        api_client: VodaCareClient,
        termination_checker: TerminationChecker
    ):
        """
        Initialize the orchestrator.

        Args:
            user_simulator: User simulator instance
            api_client: API client for chatbot
            termination_checker: Termination logic checker
        """
        self.user_simulator = user_simulator
        self.api_client = api_client
        self.termination_checker = termination_checker

    def run_conversation(
        self,
        persona: Persona,
        scenario: Scenario,
        variant: str,
        seed: int
    ) -> Dict[str, Any]:
        """
        Run a complete conversation between persona and chatbot.

        Args:
            persona: The persona to simulate
            scenario: The scenario context
            variant: System prompt variant ("A" or "B")
            seed: Random seed for reproducibility

        Returns:
            Dictionary containing:
                - transcript: List of ConversationTurn objects
                - termination: TerminationInfo object
                - total_turns: Number of turns
                - average_latency_ms: Average response latency
                - session_id: Session identifier used
        """
        session_id = f"sim_{persona.id}_{scenario.id}_{seed}"
        participant_id = f"llm_test_{seed}"

        logger.info(
            f"Starting conversation: {persona.id} × {scenario.id} "
            f"(variant={variant}, seed={seed})"
        )

        # Register participant in database
        try:
            self.api_client.register_participant(
                participant_id=participant_id,
                session_id=session_id,
                group=variant,
                name=f"Simulated: {persona.name}"
            )
        except Exception as e:
            logger.warning(f"Failed to register participant: {e}")

        transcript: List[ConversationTurn] = []
        conversation_history: List[Dict[str, str]] = []
        latencies: List[float] = []

        turn_number = 0
        started_at = datetime.now()

        try:
            while True:
                turn_number += 1
                logger.info(f"--- Turn {turn_number} ---")

                # Generate user message
                user_message = self.user_simulator.generate_response(
                    persona=persona,
                    scenario=scenario,
                    conversation_history=conversation_history,
                    turn_number=turn_number
                )

                logger.info(f"User: {user_message[:100]}...")

                # Record user turn
                user_turn = ConversationTurn(
                    turn_number=turn_number,
                    speaker="user",
                    message=user_message,
                    timestamp=datetime.now()
                )
                transcript.append(user_turn)

                # Add to conversation history for simulator
                conversation_history.append({
                    "role": "user",
                    "content": user_message
                })

                # Get assistant response
                try:
                    api_response = self.api_client.send_message(
                        message=user_message,
                        session_id=session_id,
                        participant_group=variant,
                        participant_id=participant_id
                    )

                    assistant_message = api_response["response"]
                    latency = api_response["latency_ms"]
                    latencies.append(latency)

                    logger.info(
                        f"Assistant: {assistant_message[:100]}... "
                        f"(latency: {latency:.0f}ms)"
                    )

                except Exception as e:
                    logger.error(f"API error: {e}")
                    # Record error in transcript
                    assistant_message = f"[ERROR: {str(e)}]"
                    latency = 0

                # Record assistant turn
                assistant_turn = ConversationTurn(
                    turn_number=turn_number,
                    speaker="assistant",
                    message=assistant_message,
                    timestamp=datetime.now(),
                    metadata={"latency_ms": latency}
                )
                transcript.append(assistant_turn)

                # Add to conversation history for simulator
                conversation_history.append({
                    "role": "assistant",
                    "content": assistant_message
                })

                # Check termination conditions
                should_end, reason, details = self.termination_checker.should_terminate(
                    persona=persona,
                    conversation_history=conversation_history,
                    turn_number=turn_number
                )

                if should_end:
                    logger.info(f"Conversation ending: {reason} - {details}")
                    termination = TerminationInfo(
                        reason=reason,
                        turn_number=turn_number,
                        details=details
                    )
                    break

        except Exception as e:
            logger.error(f"Conversation error: {e}", exc_info=True)
            # Create termination info for error case
            termination = TerminationInfo(
                reason="error",
                turn_number=turn_number,
                details=f"Error occurred: {str(e)}"
            )

        completed_at = datetime.now()

        # Calculate average latency
        avg_latency = sum(latencies) / len(latencies) if latencies else 0

        logger.info(
            f"Conversation completed: {turn_number} turns, "
            f"avg latency: {avg_latency:.0f}ms, reason: {termination.reason}"
        )

        return {
            "transcript": transcript,
            "termination": termination,
            "total_turns": turn_number,
            "average_latency_ms": avg_latency,
            "session_id": session_id,
            "started_at": started_at,
            "completed_at": completed_at
        }
