from __future__ import annotations

import re
import uuid
from typing import Dict, List, Tuple

from .config import (
    get_provider_name,
    get_openai_api_key,
    get_openai_model,
    get_openai_base_url,
    get_assistant_mode,
)


class SupportAgent:
    def __init__(self):
        self.provider = get_provider_name()
        self.mode = get_assistant_mode()  # 'open' or 'strict'
        # In-memory chat history per session
        self.sessions: Dict[str, List[Tuple[str, str]]] = {}
        # LLM client (optional)
        self._llm_client = None
        self._llm_model = get_openai_model()
        api_key = get_openai_api_key()
        base_url = get_openai_base_url()
        if api_key:
            try:
                # Lazy import to avoid hard dependency if not used
                from openai import OpenAI  # type: ignore

                if base_url:
                    self._llm_client = OpenAI(api_key=api_key, base_url=base_url)
                else:
                    self._llm_client = OpenAI(api_key=api_key)
            except Exception:
                # If import or client init fails, stay in rule-based mode
                self._llm_client = None

        # Minimal knowledge base with topic -> details
        self.knowledge: Dict[str, Dict] = {
            "plans": {
                "desc": "Plans and upgrades",
                "reply": (
                    "We offer SIM‑only and device plans with flexible data. "
                    "Popular choices include 25GB, 100GB and Unlimited. You can upgrade any time in your account."
                ),
                "suggestions": [
                    "Show plan options",
                    "How to upgrade",
                    "What is unlimited?",
                ],
                "keywords": ["plan", "plans", "upgrade", "contract", "tariff", "unlimited"],
            },
            "balance": {
                "desc": "Data and usage",
                "reply": "Check remaining data and minutes in the app or text BALANCE to 12345.",
                "suggestions": ["Check data balance", "Data add-ons", "Usage alerts"],
                "keywords": ["data", "balance", "usage", "allowance", "left"],
            },
            "billing": {
                "desc": "Bills and payments",
                "reply": "Bills are monthly. Pay by card or Direct Debit. For a breakdown, open Billing in your account.",
                "suggestions": ["View my bill", "Change payment method", "Late payment"],
                "keywords": ["bill", "billing", "payment", "invoice", "charge"],
            },
            "roaming": {
                "desc": "Roaming and international",
                "reply": (
                    "Roaming works on most plans. In the EU you can usually use your allowance like at home. For other countries, check our roaming page for rates."
                ),
                "suggestions": ["EU roaming", "Roaming rates", "Enable roaming"],
                "keywords": ["roam", "roaming", "international", "abroad", "travel"],
            },
            "network": {
                "desc": "Coverage and issues",
                "reply": "Share your postcode and device model and I’ll check coverage and any local issues.",
                "suggestions": ["Coverage map", "Report an outage", "Network reset steps"],
                "keywords": ["signal", "coverage", "network", "no service", "5g", "4g"],
            },
            "support": {
                "desc": "Live support",
                "reply": "I can connect you with a specialist. Advisors are available 8am–8pm. Should I connect you?",
                "suggestions": ["Talk to an agent", "Open a ticket", "Live chat hours"],
                "keywords": ["agent", "human", "person", "support", "advisor", "representative"],
            },
            "device": {
                "desc": "Devices and SIM",
                "reply": "For SIM swap, eSIM setup, or lost/stolen devices, I can guide you through the steps in your account.",
                "suggestions": ["SIM swap", "Set up eSIM", "Lost my phone"],
                "keywords": ["device", "phone", "sim", "esim", "lost", "stolen"],
            },
        }

        # Map of quick reply chips to intents to keep UX tight
        self.quick_map = {
            "Show plan options": "plans",
            "How to upgrade": "plans",
            "What is unlimited?": "plans",
            "Check data balance": "balance",
            "Data add-ons": "balance",
            "Usage alerts": "balance",
            "View my bill": "billing",
            "Change payment method": "billing",
            "Late payment": "billing",
            "EU roaming": "roaming",
            "Roaming rates": "roaming",
            "Enable roaming": "roaming",
            "Coverage map": "network",
            "Report an outage": "network",
            "Network reset steps": "network",
            "Talk to an agent": "support",
            "Open a ticket": "support",
            "Live chat hours": "support",
            "SIM swap": "device",
            "Set up eSIM": "device",
            "Lost my phone": "device",
        }

        # General suggestions appended or used when unknown in open mode
        self.general_suggestions = [
            "Ask me anything",
            "Tell me more",
            "Something else",
        ]

    def _ensure_session(self, session_id: str | None) -> str:
        if not session_id:
            session_id = uuid.uuid4().hex
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        return session_id

    def _detect_topic(self, text: str) -> str:
        t = text.lower().strip()
        # Check if it's a quick chip exact match
        if text in self.quick_map:
            return self.quick_map[text]
        # Keyword based intent detection
        for topic, info in self.knowledge.items():
            for kw in info["keywords"]:
                # word boundary rough check
                if re.search(rf"\b{re.escape(kw)}\b", t):
                    return topic
        # Fallback
        return "unknown"

    def _llm_reply(self, user_text: str, topic: str, sid: str) -> str | None:
        if not self._llm_client:
            return None
        try:
            if self.mode == "open":
                system = (
                    f"You are a helpful support agent for {self.provider}. Keep replies concise. "
                    "You can chat broadly, and for telecom topics (plans, upgrades, data/balance, billing, roaming, network/coverage, devices/SIM) give clear, practical guidance. "
                    "Ask brief follow‑ups when needed. Don't guess."
                )
            else:
                system = (
                    f"You are a helpful mobile network support agent for {self.provider}. Keep replies concise. "
                    "Focus on telecom topics like plans, upgrades, data/balance, billing, roaming, network/coverage and devices/SIM. "
                    "Ask brief follow‑ups when needed. Don't guess."
                )
            # Build short context using session last few turns
            messages = [{"role": "system", "content": system}]
            history = self.sessions.get(sid, [])
            for role, text in history[-6:]:
                messages.append({"role": role, "content": text})
            messages.append({"role": "user", "content": user_text})

            resp = self._llm_client.chat.completions.create(
                model=self._llm_model,
                messages=messages,  # type: ignore
                temperature=0.5 if self.mode == "open" else 0.3,
                max_tokens=220,
            )
            content = resp.choices[0].message.content if resp.choices else None
            return content or None
        except Exception:
            return None

    def _build_reply(self, topic: str, user_text: str, sid: str) -> tuple[str, List[str], bool]:
        if topic == "unknown":
            if self.mode == "open":
                reply = self._llm_reply(user_text, topic, sid) or (
                    f"Hi — I’m {self.provider} Support. I can chat broadly and help with plans, data/balance, billing, roaming, coverage or devices. How can I help?"
                )
                suggestions = [
                    *self.general_suggestions,
                    "Show plan options",
                    "Check data balance",
                    "View my bill",
                    "Roaming rates",
                    "Coverage map",
                    "Talk to an agent",
                ]
            else:
                reply = self._llm_reply(user_text, topic, sid) or (
                    f"Hi — I’m {self.provider} Support. I can help with plans, data/balance, billing, roaming, coverage or devices. What do you need help with?"
                )
                suggestions = [
                    "Show plan options",
                    "Check data balance",
                    "View my bill",
                    "Roaming rates",
                    "Coverage map",
                    "Talk to an agent",
                ]
            return reply, suggestions, False

        info = self.knowledge[topic]
        # Prefer LLM reply when available; otherwise canned text
        reply = self._llm_reply(user_text, topic, sid) or info["reply"]
        suggestions = (
            [*info["suggestions"], self.general_suggestions[0]]
            if self.mode == "open"
            else info["suggestions"]
        )
        escalate = topic == "support" or any(
            w in user_text.lower() for w in ["agent", "human", "person", "escalate"]
        )
        return reply, suggestions, escalate

    def chat(self, message: str, session_id: str | None) -> dict:
        sid = self._ensure_session(session_id)
        self.sessions[sid].append(("user", message))

        topic = self._detect_topic(message)
        reply, suggestions, escalate = self._build_reply(topic, message, sid)

        self.sessions[sid].append(("assistant", reply))
        return {
            "reply": reply,
            "suggestions": suggestions,
            "topic": topic,
            "escalate": escalate,
            "session_id": sid,
        }
