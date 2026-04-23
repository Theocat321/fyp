import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from datetime import datetime
from src.evaluator.heuristics import HeuristicEvaluator
from src.artifacts.models import ConversationTurn


def turn(speaker, message, n=1):
    return ConversationTurn(turn_number=n, speaker=speaker, message=message, timestamp=datetime.now())


def transcript(*pairs):
    return [turn(s, m, i + 1) for i, (s, m) in enumerate(pairs)]


@pytest.fixture
def ev():
    return HeuristicEvaluator()


# --- hallucinated plans ---

class TestHallucinatedPlans:
    def test_valid_price_passes(self, ev):
        t = transcript(("assistant", "The £25 plan includes unlimited calls."))
        result = ev._check_hallucinated_plans(t)
        assert result.passed is True

    def test_invalid_price_fails(self, ev):
        t = transcript(("assistant", "Try our £99 premium plan."))
        result = ev._check_hallucinated_plans(t)
        assert result.passed is False
        assert "99" in result.details
        assert result.severity == "critical"

    def test_no_prices_passes(self, ev):
        t = transcript(("assistant", "Let me help you with your account."))
        result = ev._check_hallucinated_plans(t)
        assert result.passed is True

    def test_per_month_pattern(self, ev):
        t = transcript(("assistant", "That's 42 per month for the Unlimited Max plan."))
        result = ev._check_hallucinated_plans(t)
        assert result.passed is True

    def test_slash_month_pattern(self, ev):
        t = transcript(("assistant", "Only 99/month for our new offer."))
        result = ev._check_hallucinated_plans(t)
        assert result.passed is False

    def test_only_checks_assistant_messages(self, ev):
        t = transcript(
            ("user", "What about a £999 plan?"),
            ("assistant", "We offer plans from £8."),
        )
        result = ev._check_hallucinated_plans(t)
        assert result.passed is True

    def test_multiple_valid_prices(self, ev):
        t = transcript(("assistant", "We have £8, £15, and £25 plans available."))
        result = ev._check_hallucinated_plans(t)
        assert result.passed is True


# --- contradictions ---

class TestContradictions:
    def test_no_prices_passes(self, ev):
        t = transcript(("assistant", "Sure, I can help with that."))
        result = ev._check_contradictions(t)
        assert result.passed is True

    def test_same_price_same_context_passes(self, ev):
        t = [
            turn("assistant", "The £25 per month plan is great.", 1),
            turn("assistant", "The £25 per month plan suits your needs.", 2),
        ]
        result = ev._check_contradictions(t)
        assert result.passed is True

    def test_different_prices_no_contradiction(self, ev):
        t = [
            turn("assistant", "The £25 per month plan is affordable.", 1),
            turn("assistant", "The £42 monthly plan has unlimited data.", 2),
        ]
        result = ev._check_contradictions(t)
        assert result.passed is True

    def test_same_price_different_context_fails(self, ev):
        t = [
            turn("assistant", "The £32 per month plan is our core option.", 1),
            turn("assistant", "The £32 monthly plan includes international calls.", 2),
        ]
        result = ev._check_contradictions(t)
        assert result.passed is False
        assert result.severity == "critical"


# --- response length ---

class TestResponseLength:
    def test_normal_length_passes(self, ev):
        msg = " ".join(["word"] * 50)
        t = transcript(("assistant", msg))
        result = ev._check_response_length(t)
        assert result.passed is True

    def test_too_short_fails(self, ev):
        t = transcript(("assistant", "Hi there."))
        result = ev._check_response_length(t)
        assert result.passed is False
        assert "short" in result.details.lower()
        assert result.severity == "warning"

    def test_too_long_fails(self, ev):
        msg = " ".join(["word"] * 401)
        t = transcript(("assistant", msg))
        result = ev._check_response_length(t)
        assert result.passed is False
        assert "long" in result.details.lower()

    def test_exactly_30_words_passes(self, ev):
        msg = " ".join(["word"] * 30)
        t = transcript(("assistant", msg))
        result = ev._check_response_length(t)
        assert result.passed is True

    def test_exactly_400_words_passes(self, ev):
        msg = " ".join(["word"] * 400)
        t = transcript(("assistant", msg))
        result = ev._check_response_length(t)
        assert result.passed is True

    def test_only_checks_assistant(self, ev):
        t = transcript(("user", "Hi"))  # user message, too short, should not flag
        result = ev._check_response_length(t)
        assert result.passed is True


# --- escalation ---

class TestEscalationAppropriateness:
    def test_no_escalation_needed_passes(self, ev):
        t = transcript(
            ("user", "How do I check my balance?"),
            ("assistant", "You can check it in the app."),
        )
        result = ev._check_escalation_appropriateness(t)
        assert result.passed is True
        assert "no escalation" in result.details.lower()

    def test_user_requests_escalation_and_offered_passes(self, ev):
        t = transcript(
            ("user", "I want to speak to someone human please"),
            ("assistant", "I can transfer you to a specialist right now."),
        )
        result = ev._check_escalation_appropriateness(t)
        assert result.passed is True

    def test_user_requests_escalation_not_offered_fails(self, ev):
        t = transcript(
            ("user", "This is useless, I need a human"),
            ("assistant", "Here is some information about our plans."),
        )
        result = ev._check_escalation_appropriateness(t)
        assert result.passed is False
        assert result.severity == "warning"

    def test_escalation_keyword_manager(self, ev):
        t = transcript(
            ("user", "I want to speak to a manager"),
            ("assistant", "I understand. Let me escalate this for you."),
        )
        result = ev._check_escalation_appropriateness(t)
        assert result.passed is True


# --- full evaluate ---

def test_evaluate_returns_four_checks(ev):
    t = transcript(
        ("user", "Help me with roaming"),
        ("assistant", " ".join(["word"] * 50)),
    )
    results = ev.evaluate(t)
    assert len(results) == 4
    names = {r.check_name for r in results}
    assert "no_hallucinated_plans" in names
    assert "no_contradictions" in names
    assert "appropriate_response_length" in names
    assert "escalation_appropriateness" in names
