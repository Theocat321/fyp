import logging
from typing import List, Dict
from openai import OpenAI

from src.persona.models import Persona
from src.scenario.models import Scenario
from .prompts import format_conversation_for_simulator

logger = logging.getLogger(__name__)


class UserSimulator:

    def __init__(self, api_key: str, model: str = "gpt-4o-mini", base_seed: int = 42):
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
        if turn_number == 1:
            return persona.seed_utterance

        messages = format_conversation_for_simulator(persona, scenario, conversation_history)
        seed = self.base_seed + turn_number

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=300,
                seed=seed
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating user response: {e}")
            raise RuntimeError(f"Failed to generate user response: {e}")

    def should_continue(
        self,
        persona: Persona,
        conversation_history: List[Dict[str, str]],
        turn_number: int
    ) -> bool:
        # Simple heuristic — main termination logic is in the orchestrator
        if turn_number >= persona.conversation_parameters.max_patience_turns:
            return False

        if conversation_history:
            for msg in reversed(conversation_history):
                if msg["role"] == "user":
                    last = msg["content"].lower()
                    satisfaction_phrases = [
                        "thank you", "thanks", "that helps", "perfect",
                        "great", "got it", "understand now", "makes sense",
                        "that's all", "all sorted", "that's everything"
                    ]
                    if any(phrase in last for phrase in satisfaction_phrases):
                        return False
                    break

        return True
