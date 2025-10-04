from __future__ import annotations

import re
import uuid
from typing import Dict, List, Tuple

from .config import (
    get_provider_name,
    get_openai_api_key,
    get_openai_model,
    get_openai_base_url,
)


class SupportAgent:
    def __init__(self):
        self.provider = get_provider_name()
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
                    "We offer SIM-only and device plans with flexible data. "
                    "Popular options: 25GB, 100GB, and Unlimited. You can upgrade anytime in your account."
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
                "reply": (
                    "You can check your remaining data and minutes in the app or by texting BALANCE to 12345."
                ),
                "suggestions": ["Check data balance", "Data add-ons", "Usage alerts"],
                "keywords": ["data", "balance", "usage", "allowance", "left"],
            },
            "billing": {
                "desc": "Bills and payments",
                "reply": (
                    "Bills are generated monthly. Pay by card or Direct Debit. For a breakdown, open Billing in your account."
                ),
                "suggestions": ["View my bill", "Change payment method", "Late payment"],
                "keywords": ["bill", "billing", "payment", "invoice", "charge"],
            },
            "roaming": {
                "desc": "Roaming and international",
                "reply": (
                    "Roaming is enabled on most plans. In the EU, your allowance may be used like at home. For other countries, check our roaming page for rates."
                ),
                "suggestions": ["EU roaming", "Roaming rates", "Enable roaming"],
                "keywords": ["roam", "roaming", "international", "abroad", "travel"],
            },
            "network": {
                "desc": "Coverage and issues",
                "reply": (
                    "Sorry you're having trouble. Please share your postcode and device model and I'll run a coverage check for outages or maintenance."
                ),
                "suggestions": ["Coverage map", "Report an outage", "Network reset steps"],
                "keywords": ["signal", "coverage", "network", "no service", "5g", "4g"],
            },
            "support": {
                "desc": "Live support",
                "reply": (
                    "I can hand you over to a specialist. Our advisors are available 8am–8pm. Would you like me to connect you?"
                ),
                "suggestions": ["Talk to an agent", "Open a ticket", "Live chat hours"],
                "keywords": ["agent", "human", "person", "support", "advisor", "representative"],
            },
            "device": {
                "desc": "Devices and SIM",
                "reply": (
                    "For SIM swap, eSIM setup, or lost/stolen devices, I can guide you through secure steps in your account and verify your identity."
                ),
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
            system = (
                f"You are a concise, friendly mobile network provider support chatbot for {self.provider}. "
                "Answer helpfully for telecom topics like plans, upgrades, data/balance, billing, roaming, network/coverage, devices/SIM. "
                "Avoid hallucinations; if uncertain, ask for details or suggest contacting a human agent."
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
                temperature=0.3,
                max_tokens=220,
            )
            content = resp.choices[0].message.content if resp.choices else None
            return content or None
        except Exception:
            return None

    def _build_reply(self, topic: str, user_text: str, sid: str) -> tuple[str, List[str], bool]:
        if topic == "unknown":
            reply = self._llm_reply(user_text, topic, sid) or (
                f"I'm your {self.provider} virtual assistant. I can help with plans, "
                "data/balance, billing, roaming, coverage, or devices. Could you share a few details?"
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
        suggestions = info["suggestions"]
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
