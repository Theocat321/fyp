"""LLM-based user simulator."""
import logging
import random
from typing import List, Dict, Optional
from openai import OpenAI

from src.persona.models import Persona
from src.scenario.models import Scenario
from .prompts import format_conversation_for_simulator

logger = logging.getLogger(__name__)


class UserSimulator:
    """
    Simulates user responses using an LLM based on persona and scenario.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        base_seed: int = 42
    ):
        """
        Initialize the user simulator.

        Args:
            api_key: OpenAI API key
            model: Model to use for simulation
            base_seed: Base seed for reproducibility
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.base_seed = base_seed

    def generate_response(
        self,
        persona: Persona,
        scenario: Scenario,
        conversation_history: List[Dict[str, str]],
        turn_number: int
    ) -> str:
        """
        Generate a user response based on persona, scenario, and conversation history.

        Args:
            persona: The persona being simulated
            scenario: The scenario context
            conversation_history: Previous conversation turns
            turn_number: Current turn number (1-indexed)

        Returns:
            Simulated user response
        """
        # For turn 1, use the seed utterance
        if turn_number == 1:
            logger.info(f"Turn {turn_number}: Using seed utterance")
            return persona.seed_utterance

        # For subsequent turns, generate response with LLM
        messages = format_conversation_for_simulator(
            persona, scenario, conversation_history
        )

        # Set seed for reproducibility (base_seed + turn_number)
        seed = self.base_seed + turn_number

        try:
            logger.info(
                f"Turn {turn_number}: Generating response with {self.model} "
                f"(seed={seed})"
            )

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=300,
                seed=seed
            )

            user_response = response.choices[0].message.content.strip()

            logger.info(
                f"Turn {turn_number}: Generated response "
                f"({len(user_response)} chars)"
            )

            return user_response

        except Exception as e:
            logger.error(f"Error generating user response: {e}")
            raise RuntimeError(f"Failed to generate user response: {e}")

    def should_continue(
        self,
        persona: Persona,
        conversation_history: List[Dict[str, str]],
        turn_number: int
    ) -> bool:
        """
        Determine if the simulated user would continue the conversation.

        This is a simple heuristic - the main termination logic is in the
        orchestrator, but this can provide additional persona-based signals.

        Args:
            persona: The persona being simulated
            scenario: The scenario context
            conversation_history: Previous conversation turns
            turn_number: Current turn number

        Returns:
            True if user would likely continue, False otherwise
        """
        # Check patience threshold
        if turn_number >= persona.conversation_parameters.max_patience_turns:
            logger.info(
                f"Turn {turn_number}: Reached max patience turns "
                f"({persona.conversation_parameters.max_patience_turns})"
            )
            return False

        # If we have conversation history, look for satisfaction signals
        if conversation_history:
            last_user_message = None
            for msg in reversed(conversation_history):
                if msg["role"] == "user":
                    last_user_message = msg["content"].lower()
                    break

            if last_user_message:
                # Look for satisfaction indicators
                satisfaction_phrases = [
                    "thank you", "thanks", "that helps", "perfect",
                    "great", "got it", "understand now", "makes sense",
                    "that's all", "all sorted", "that's everything"
                ]

                if any(phrase in last_user_message for phrase in satisfaction_phrases):
                    logger.info(
                        f"Turn {turn_number}: Detected satisfaction signal"
                    )
                    return False

        return True
