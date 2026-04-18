import logging
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

    def __init__(
        self,
        user_simulator: UserSimulator,
        api_client: VodaCareClient,
        termination_checker: TerminationChecker
    ):
        self.user_simulator = user_simulator
        self.api_client = api_client
        self.termination_checker = termination_checker

    def run_conversation(self, persona: Persona, scenario: Scenario, variant: str, seed: int) -> Dict[str, Any]:
        session_id = f"sim_{persona.id}_{scenario.id}_{seed}"
        participant_id = f"llm_test_{seed}"

        logger.info(f"Starting: {persona.id} × {scenario.id} (variant={variant}, seed={seed})")

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

                user_message = self.user_simulator.generate_response(
                    persona=persona,
                    scenario=scenario,
                    conversation_history=conversation_history,
                    turn_number=turn_number
                )
                logger.info(f"User: {user_message[:100]}...")

                transcript.append(ConversationTurn(
                    turn_number=turn_number, speaker="user",
                    message=user_message, timestamp=datetime.now()
                ))
                conversation_history.append({"role": "user", "content": user_message})

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
                    logger.info(f"Assistant: {assistant_message[:100]}... ({latency:.0f}ms)")
                except Exception as e:
                    logger.error(f"API error: {e}")
                    assistant_message = f"[ERROR: {str(e)}]"
                    latency = 0

                transcript.append(ConversationTurn(
                    turn_number=turn_number, speaker="assistant",
                    message=assistant_message, timestamp=datetime.now(),
                    metadata={"latency_ms": latency}
                ))
                conversation_history.append({"role": "assistant", "content": assistant_message})

                should_end, reason, details = self.termination_checker.should_terminate(
                    persona=persona,
                    conversation_history=conversation_history,
                    turn_number=turn_number
                )
                if should_end:
                    logger.info(f"Ending: {reason} — {details}")
                    termination = TerminationInfo(reason=reason, turn_number=turn_number, details=details)
                    break

        except Exception as e:
            logger.error(f"Conversation error: {e}", exc_info=True)
            termination = TerminationInfo(reason="error", turn_number=turn_number, details=str(e))

        completed_at = datetime.now()
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        logger.info(f"Done: {turn_number} turns, avg latency {avg_latency:.0f}ms, reason: {termination.reason}")

        return {
            "transcript": transcript,
            "termination": termination,
            "total_turns": turn_number,
            "average_latency_ms": avg_latency,
            "session_id": session_id,
            "started_at": started_at,
            "completed_at": completed_at
        }
