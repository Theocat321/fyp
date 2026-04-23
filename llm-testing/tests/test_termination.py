import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from src.orchestrator.termination import TerminationChecker
from src.persona.models import Persona, ConversationParameters, BehavioralTraits


def make_persona(max_patience=5):
    return Persona(
        id="p1",
        name="Test User",
        age=30,
        location="London",
        demographics={"occupation": "Engineer"},
        personality={"communication_style": "direct"},
        behavioral_traits=BehavioralTraits(
            patience_level="moderate",
            tone=["neutral"],
            response_style="direct",
            detail_preference="moderate",
        ),
        goals=["Get help"],
        conversation_parameters=ConversationParameters(
            max_patience_turns=max_patience,
            escalation_threshold=3,
            tech_literacy="moderate",
        ),
        seed_utterance="Hello, I need help.",
    )


def history(*messages):
    result = []
    for i, (role, content) in enumerate(messages):
        result.append({"role": role, "content": content})
    return result


@pytest.fixture
def checker():
    return TerminationChecker(max_turns=10)


persona = make_persona()


# --- max turns ---

class TestMaxTurns:
    def test_at_limit_terminates(self, checker):
        terminate, reason, _ = checker.should_terminate(persona, [], 10)
        assert terminate is True
        assert reason == "max_turns"

    def test_below_limit_does_not_terminate(self, checker):
        # use a high-patience persona so patience check doesn't fire first
        p = make_persona(max_patience=20)
        terminate, _, _ = checker.should_terminate(p, [], 9)
        assert terminate is False

    def test_custom_max_turns(self):
        checker = TerminationChecker(max_turns=5)
        terminate, reason, _ = checker.should_terminate(persona, [], 5)
        assert terminate is True
        assert reason == "max_turns"


# --- early turns (no other checks) ---

def test_turn_zero_no_terminate(checker):
    terminate, _, _ = checker.should_terminate(persona, [], 0)
    assert terminate is False


def test_turn_one_no_terminate(checker):
    h = history(("user", "hello"), ("assistant", "hi"))
    terminate, _, _ = checker.should_terminate(persona, h, 1)
    assert terminate is False


# --- satisfaction ---

class TestSatisfaction:
    def test_explicit_close_terminates(self, checker):
        h = history(
            ("user", "What are my roaming options?"),
            ("assistant", "Here are the details."),
            ("user", "that's all I needed, thanks"),
        )
        terminate, reason, _ = checker.should_terminate(persona, h, 3)
        assert terminate is True
        assert reason == "satisfaction"

    def test_thanks_after_3_turns_terminates(self, checker):
        h = history(
            ("user", "help me"),
            ("assistant", "sure"),
            ("user", "more help"),
            ("assistant", "here"),
            ("user", "thank you so much"),
        )
        terminate, reason, _ = checker.should_terminate(persona, h, 3)
        assert terminate is True
        assert reason == "satisfaction"

    def test_thanks_at_turn_2_does_not_terminate(self, checker):
        h = history(
            ("user", "hi"),
            ("assistant", "hello"),
            ("user", "thanks"),
        )
        terminate, _, _ = checker.should_terminate(persona, h, 2)
        assert terminate is False

    def test_got_it_terminates_after_3_turns(self, checker):
        h = history(
            ("user", "question"),
            ("assistant", "answer"),
            ("user", "question2"),
            ("assistant", "answer2"),
            ("user", "got it, makes sense"),
        )
        terminate, reason, _ = checker.should_terminate(persona, h, 3)
        assert terminate is True
        assert reason == "satisfaction"


# --- escalation ---

class TestEscalation:
    def test_speak_to_a_person_terminates(self, checker):
        h = history(
            ("user", "I want to speak to a person"),
            ("assistant", "I understand"),
            ("user", "speak to a person please"),
        )
        terminate, reason, _ = checker.should_terminate(persona, h, 2)
        assert terminate is True
        assert reason == "escalation"

    def test_escalate_keyword(self, checker):
        h = history(
            ("user", "Can you escalate this?"),
            ("assistant", "I'll try"),
            ("user", "please escalate now"),
        )
        terminate, reason, _ = checker.should_terminate(persona, h, 2)
        assert terminate is True
        assert reason == "escalation"

    def test_tired_of_this_terminates(self, checker):
        h = history(
            ("user", "help"),
            ("assistant", "ok"),
            ("user", "tired of this not working"),
        )
        terminate, reason, _ = checker.should_terminate(persona, h, 2)
        assert terminate is True
        assert reason == "escalation"

    def test_normal_message_no_escalation(self, checker):
        h = history(
            ("user", "What plans do you offer?"),
            ("assistant", "We have many plans."),
            ("user", "Tell me more about the unlimited plan"),
        )
        terminate, _, _ = checker.should_terminate(persona, h, 2)
        assert terminate is False


# --- stalemate ---

class TestStalemate:
    def test_repetition_triggers_stalemate(self, checker):
        h = history(
            ("user", "I already asked this"),
            ("assistant", "let me help"),
            ("user", "I said I need a refund"),
            ("assistant", "ok"),
            ("user", "I need a refund, like i said"),
            ("assistant", "I understand"),
            ("user", "I already asked about this again"),
        )
        terminate, reason, _ = checker.should_terminate(persona, h, 4)
        assert terminate is True
        assert reason == "stalemate"

    def test_frustration_word_triggers_stalemate(self, checker):
        h = history(
            ("user", "help"),
            ("assistant", "sure"),
            ("user", "more help"),
            ("assistant", "ok"),
            ("user", "second question"),
            ("assistant", "answer"),
            ("user", "this is absolutely ridiculous"),
        )
        terminate, reason, _ = checker.should_terminate(persona, h, 4)
        assert terminate is True
        assert reason == "stalemate"

    def test_stalemate_requires_turn_4(self, checker):
        h = history(
            ("user", "I already asked this"),
            ("assistant", "answer"),
            ("user", "I already asked again"),
        )
        terminate, _, _ = checker.should_terminate(persona, h, 3)
        # stalemate check not triggered before turn 4
        assert terminate is False


# --- patience exceeded ---

class TestPatienceExceeded:
    def test_exceeds_patience_terminates(self, checker):
        low_patience = make_persona(max_patience=3)
        h = history(
            ("user", "q1"), ("assistant", "a1"),
            ("user", "q2"), ("assistant", "a2"),
            ("user", "q3"), ("assistant", "a3"),
            ("user", "q4"),
        )
        terminate, reason, _ = checker.should_terminate(low_patience, h, 4)
        assert terminate is True
        assert reason == "patience_exceeded"

    def test_at_patience_limit_no_terminate(self, checker):
        low_patience = make_persona(max_patience=3)
        h = history(("user", "q"), ("assistant", "a"), ("user", "q2"))
        terminate, _, _ = checker.should_terminate(low_patience, h, 3)
        assert terminate is False
