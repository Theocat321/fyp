import logging
from typing import List, Dict, Optional, Tuple
from src.persona.models import Persona

logger = logging.getLogger(__name__)


class TerminationChecker:

    def __init__(self, max_turns: int = 10):
        self.max_turns = max_turns

    def should_terminate(
        self,
        persona: Persona,
        conversation_history: List[Dict[str, str]],
        turn_number: int
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        # Check 1: Max turns
        if turn_number >= self.max_turns:
            logger.info(f"Terminating: max turns ({self.max_turns}) reached")
            return True, "max_turns", f"Reached maximum of {self.max_turns} turns"

        # Need at least one exchange to check other conditions
        if turn_number < 2:
            return False, None, None

        last_user_msg = None
        last_assistant_msg = None
        for msg in reversed(conversation_history):
            if msg["role"] == "user" and last_user_msg is None:
                last_user_msg = msg["content"].lower()
            elif msg["role"] == "assistant" and last_assistant_msg is None:
                last_assistant_msg = msg["content"].lower()
            if last_user_msg and last_assistant_msg:
                break

        # Check 2: User satisfaction
        if last_user_msg:
            satisfaction_indicators = [
                "thank you", "thanks so much", "that helps",
                "perfect", "great", "excellent", "got it",
                "understand now", "makes sense", "that's all",
                "all set", "that's everything", "appreciate it",
                "that's what i needed", "that clarifies"
            ]
            if any(ind in last_user_msg for ind in satisfaction_indicators):
                closing_indicators = [
                    "that's all", "that's everything", "all set",
                    "that's what i needed", "that clarifies"
                ]
                if any(c in last_user_msg for c in closing_indicators):
                    logger.info("Terminating: user satisfaction (explicit close)")
                    return True, "satisfaction", "User expressed satisfaction and closure"
                # After multiple turns, a simple thanks is likely genuine closure
                if turn_number >= 3:
                    logger.info("Terminating: likely satisfaction after exchange")
                    return True, "satisfaction", "User expressed thanks after productive exchange"

        # Check 3: Escalation requested
        if last_user_msg:
            escalation_phrases = [
                "speak to a person", "human agent", "real person",
                "supervisor", "manager", "escalate", "someone else",
                "not helping", "this isn't working", "tired of this"
            ]
            if any(phrase in last_user_msg for phrase in escalation_phrases):
                logger.info("Terminating: escalation requested")
                return True, "escalation", "User requested to speak with human agent"

        # Check 4: Stalemate
        if turn_number >= 4:
            is_stalemate, stalemate_reason = self._check_stalemate(conversation_history)
            if is_stalemate:
                logger.info(f"Terminating: stalemate — {stalemate_reason}")
                return True, "stalemate", stalemate_reason

        # Check 5: Patience exceeded
        if turn_number > persona.conversation_parameters.max_patience_turns:
            logger.info(f"Terminating: exceeded patience threshold ({persona.conversation_parameters.max_patience_turns})")
            return True, "patience_exceeded", f"Exceeded {persona.name}'s patience limit"

        return False, None, None

    def _check_stalemate(self, conversation_history: List[Dict[str, str]]) -> Tuple[bool, Optional[str]]:
        user_messages = [msg["content"].lower() for msg in conversation_history if msg["role"] == "user"]
        if len(user_messages) < 3:
            return False, None

        last_three = user_messages[-3:]
        repetition_indicators = [
            "i already asked", "i said", "like i said", "as i mentioned",
            "i told you", "i need", "still", "again"
        ]
        if sum(1 for msg in last_three if any(ind in msg for ind in repetition_indicators)) >= 2:
            return True, "User repeatedly asking similar questions"

        frustration_words = ["ridiculous", "useless", "waste", "pathetic", "terrible", "awful", "horrible", "worst"]
        if any(word in last_three[-1] for word in frustration_words):
            return True, "User showing strong frustration"

        return False, None
