import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from unittest.mock import MagicMock, patch
from app.agent import SupportAgent


@pytest.fixture
def agent():
    return SupportAgent()


# --- topic detection ---

class TestDetectTopic:
    def test_plans_keyword(self, agent):
        assert agent._detect_topic("I want to upgrade my plan") == "plans"

    def test_billing_keyword(self, agent):
        assert agent._detect_topic("I have a question about my bill") == "billing"

    def test_roaming_keyword(self, agent):
        assert agent._detect_topic("Does roaming work in France?") == "roaming"

    def test_network_keyword(self, agent):
        assert agent._detect_topic("I have no signal") == "network"

    def test_balance_keyword(self, agent):
        assert agent._detect_topic("How much data do I have left?") == "balance"

    def test_device_keyword(self, agent):
        assert agent._detect_topic("I need to set up my eSIM") == "device"

    def test_support_keyword(self, agent):
        assert agent._detect_topic("I want to speak to a human") == "support"

    def test_unknown(self, agent):
        assert agent._detect_topic("What's the weather like?") == "unknown"

    def test_case_insensitive(self, agent):
        assert agent._detect_topic("ROAMING in Europe") == "roaming"

    def test_quick_reply_chip(self, agent):
        assert agent._detect_topic("Set up eSIM") == "device"
        assert agent._detect_topic("EU roaming") == "roaming"
        assert agent._detect_topic("View my bill") == "billing"

    def test_word_boundary(self, agent):
        # "plan" keyword should not match "airplane"
        result = agent._detect_topic("I took an airplane")
        assert result != "plans"


# --- session management ---

class TestEnsureSession:
    def test_creates_session_when_none(self, agent):
        sid = agent._ensure_session(None)
        assert sid is not None
        assert sid in agent.sessions

    def test_reuses_existing_session_id(self, agent):
        sid = agent._ensure_session("abc123")
        assert sid == "abc123"
        assert "abc123" in agent.sessions

    def test_does_not_overwrite_existing_history(self, agent):
        agent.sessions["existing"] = [("user", "hello")]
        agent._ensure_session("existing")
        assert agent.sessions["existing"] == [("user", "hello")]

    def test_new_session_is_empty(self, agent):
        sid = agent._ensure_session(None)
        assert agent.sessions[sid] == []


# --- system prompt ---

class TestSystemPrompt:
    def test_open_mode_contains_provider(self, agent):
        prompt = agent._system_prompt(None)
        assert "VodaCare" in prompt

    def test_strict_mode_contains_provider(self, agent):
        agent.mode = "strict"
        prompt = agent._system_prompt(None)
        assert "VodaCare" in prompt

    def test_open_mode_mentions_broad_chat(self, agent):
        agent.mode = "open"
        prompt = agent._system_prompt(None)
        assert "broadly" in prompt.lower() or "broad" in prompt.lower()

    def test_group_file_loaded_if_present(self, agent, tmp_path, monkeypatch):
        prompt_file = tmp_path / "sys_prompt_a.txt"
        prompt_file.write_text("Custom group A prompt")
        # Point root to tmp_path by patching Path resolution
        with patch("app.agent.Path") as MockPath:
            mock_root = MagicMock()
            MockPath.return_value.resolve.return_value.parents.__getitem__.return_value = mock_root
            mock_p = MagicMock()
            mock_p.exists.return_value = True
            mock_p.read_text.return_value = "Custom group A prompt"
            mock_root.__truediv__.return_value = mock_p
            result = agent._system_prompt("A")
        assert result == "Custom group A prompt"


# --- build_reply (no LLM) ---

class TestBuildReply:
    def test_no_client_returns_error(self, agent):
        assert agent._llm_client is None
        reply, _, _ = agent._build_reply("plans", "I need a plan", "sid1", None)
        assert "problem" in reply.lower() or "working" in reply.lower()

    def test_escalate_true_for_support_topic(self, agent):
        _, _, escalate = agent._build_reply("support", "help me", "sid1", None)
        assert escalate is True

    def test_escalate_true_for_agent_keyword(self, agent):
        _, _, escalate = agent._build_reply("plans", "I want an agent", "sid1", None)
        assert escalate is True

    def test_escalate_true_for_human_keyword(self, agent):
        _, _, escalate = agent._build_reply("balance", "talk to human please", "sid1", None)
        assert escalate is True

    def test_escalate_false_for_normal_message(self, agent):
        _, _, escalate = agent._build_reply("billing", "what is my bill?", "sid1", None)
        assert escalate is False

    def test_with_llm_client_returns_llm_reply(self, agent):
        agent._llm_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Here is your plan info."
        agent._llm_client.chat.completions.create.return_value.choices = [mock_choice]
        agent.sessions["sid1"] = []
        reply, _, _ = agent._build_reply("plans", "show me plans", "sid1", None)
        assert reply == "Here is your plan info."


# --- chat ---

class TestChat:
    def test_returns_required_keys(self, agent):
        result = agent.chat("Hello", None)
        assert {"reply", "suggestions", "topic", "escalate", "session_id"}.issubset(result)

    def test_creates_new_session(self, agent):
        result = agent.chat("test", None)
        assert result["session_id"] in agent.sessions

    def test_reuses_provided_session_id(self, agent):
        result = agent.chat("test", "sess-xyz")
        assert result["session_id"] == "sess-xyz"

    def test_appends_to_history(self, agent):
        agent.chat("How do I roam abroad?", "hist-test")
        history = agent.sessions["hist-test"]
        assert any(role == "user" and "roam" in text.lower() for role, text in history)
        assert any(role == "assistant" for role, _ in history)

    def test_escalate_flag_in_result(self, agent):
        result = agent.chat("I want to talk to a human agent", None)
        assert result["escalate"] is True
