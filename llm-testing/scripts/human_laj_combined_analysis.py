#!/usr/bin/env python3
"""
Combined Human Self-Ratings + LLM-as-Judge Analysis.
Fetches human conversations, evaluates with LLM-as-Judge, and compares Group A vs B.
Usage: python3 human_laj_combined_analysis.py [--output combined_report.json]
"""
import argparse
import json
import logging
import re
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "server"))

import requests
from dotenv import load_dotenv

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

load_dotenv(Path(__file__).parent.parent.parent / ".env")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class HumanLAJAnalyzer:

    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not (self.supabase_url and self.supabase_key):
            raise RuntimeError("Supabase not configured")
        self.headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json",
        }
        api_key = os.getenv("OPENAI_API_KEY")
        self.llm_client = OpenAI(api_key=api_key) if api_key and OpenAI else None
        self.llm_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def fetch_all_messages(self) -> List[Dict[str, Any]]:
        logger.info("Fetching all messages from Supabase...")
        all_messages = []
        offset = 0
        limit = 1000
        while True:
            resp = requests.get(
                f"{self.supabase_url}/rest/v1/messages?offset={offset}&limit={limit}",
                headers=self.headers, timeout=10
            )
            if resp.status_code != 200:
                break
            batch = resp.json() if isinstance(resp.json(), list) else []
            if not batch:
                break
            all_messages.extend(batch)
            offset += limit

        # filter out simulated conversations
        human_messages = [
            m for m in all_messages
            if m.get('participant_id') and not str(m.get('participant_id')).lower().startswith('llm')
        ]
        logger.info(f"Fetched {len(human_messages)} human messages")
        return human_messages

    def fetch_feedback(self) -> List[Dict[str, Any]]:
        logger.info("Fetching feedback from Supabase...")
        resp = requests.get(f"{self.supabase_url}/rest/v1/support_feedback", headers=self.headers, timeout=10)
        if resp.status_code != 200:
            return []
        feedback = resp.json() if isinstance(resp.json(), list) else []
        logger.info(f"Fetched {len(feedback)} feedback entries")
        return feedback

    def group_messages_by_session(self, messages: List[Dict[str, Any]]) -> Dict[str, List]:
        sessions = defaultdict(list)
        for msg in messages:
            if sid := msg.get('session_id'):
                sessions[sid].append(msg)
        return dict(sessions)

    def evaluate_session_with_llm(self, session_id: str, messages: List[Dict]) -> Dict[str, Any]:
        if not self.llm_client:
            logger.warning(f"LLM client not available, skipping LAJ for {session_id}")
            return {"task_success": 0, "clarity": 0, "empathy": 0, "overall": 0, "error": "LLM not configured"}

        # build transcript in same format as simulation
        lines = []
        for i, msg in enumerate(sorted(messages, key=lambda m: m.get('created_at', '')), 1):
            role = "USER" if msg.get('role') == 'user' else "ASSISTANT"
            lines.append(f"[Turn {i}] {role}: {msg.get('content', '')}")
        transcript_text = "\n".join(lines)

        # prompt matches the simulation framework scoring format
        prompt = f"""Evaluate this customer service conversation based on the following criteria.

# TRANSCRIPT
{transcript_text}

# EVALUATION RUBRIC

TASK_SUCCESS (weight: 0.6)
Did the assistant successfully help the customer accomplish their goal? Did they address the customer's needs?

CLARITY (weight: 0.2)
Were the assistant's responses clear, well-structured, and easy to understand?

EMPATHY (weight: 0.2)
Was the assistant appropriately empathetic and supportive of the customer's situation?

# YOUR TASK
Provide scores from 0.0 to 1.0 for each dimension, where:
- 0.0 = Complete failure
- 0.5 = Adequate but with issues
- 1.0 = Excellent performance

Format your response EXACTLY as follows:

TASK_SUCCESS: [score]
Rationale: [explanation]

CLARITY: [score]
Rationale: [explanation]

EMPATHY: [score]
Rationale: [explanation]

OVERALL ASSESSMENT:
[Summary of conversation quality]
"""

        try:
            response = self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": "You are an expert evaluator of customer service conversations. Provide objective, detailed assessments based on the given criteria."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3, max_tokens=1000
            )
            evaluation_text = response.choices[0].message.content.strip()

            # parse scores using same method as simulation
            def extract_score(text: str, dimension: str) -> float:
                match = re.search(rf"{dimension}:\s*([0-9]*\.?[0-9]+)", text, re.IGNORECASE)
                if match:
                    try:
                        return max(0.0, min(1.0, float(match.group(1))))
                    except ValueError:
                        return 0.5
                return 0.5

            task_success = extract_score(evaluation_text, "TASK_SUCCESS")
            clarity = extract_score(evaluation_text, "CLARITY")
            empathy = extract_score(evaluation_text, "EMPATHY")

            # weighted overall matching simulation weights
            overall = task_success * 0.6 + clarity * 0.2 + empathy * 0.2

            return {"task_success": task_success, "clarity": clarity, "empathy": empathy, "overall": overall, "rationale": evaluation_text}

        except Exception as e:
            logger.debug(f"LLM evaluation error for {session_id}: {e}")
            return {"task_success": 0, "clarity": 0, "empathy": 0, "overall": 0, "error": str(e)}

    def generate_combined_report(self, output_file: Optional[str] = None) -> Dict[str, Any]:
        logger.info("Generating combined report...")
        messages = self.fetch_all_messages()
        feedback = self.fetch_feedback()
        sessions = self.group_messages_by_session(messages)
        feedback_by_session = {f.get('session_id'): f for f in feedback if f.get('session_id')}

        logger.info(f"Evaluating {len(sessions)} sessions with LLM-as-Judge...")
        laj_results = {}
        for i, (session_id, session_messages) in enumerate(sessions.items(), 1):
            if i % 10 == 0:
                logger.info(f"  Evaluated {i}/{len(sessions)} sessions...")
            laj_results[session_id] = self.evaluate_session_with_llm(session_id, session_messages)

        group_data = {"A": [], "B": []}
        for feedback_entry in feedback:
            session_id = feedback_entry.get('session_id')
            group = feedback_entry.get('participant_group', 'unspecified')
            combined = {
                "session_id": session_id,
                "human_ratings": {
                    "overall": feedback_entry.get('rating_overall'),
                    "task_success": feedback_entry.get('rating_task_success'),
                    "clarity": feedback_entry.get('rating_clarity'),
                    "empathy": feedback_entry.get('rating_empathy'),
                    "accuracy": feedback_entry.get('rating_accuracy'),
                },
                "laj_evaluation": laj_results.get(session_id, {}),
                "message_count": len(sessions.get(session_id, []))
            }
            if group in group_data:
                group_data[group].append(combined)

        report = {
            "analysis_type": "Human Self-Ratings + LLM-as-Judge Evaluation",
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_sessions": len(sessions),
                "total_messages": len(messages),
                "feedback_collected": len(feedback),
                "laj_evaluations": len(laj_results)
            },
            "by_group": {}
        }

        def avg(vals):
            return round(sum(vals) / len(vals), 2) if vals else 0

        for group in ["A", "B"]:
            entries = group_data[group]
            if not entries:
                continue

            h = lambda k: [e["human_ratings"].get(k) for e in entries if e["human_ratings"].get(k)]
            l = lambda k: [e["laj_evaluation"].get(k, 0) for e in entries if e["laj_evaluation"].get(k) is not None]

            report["by_group"][group] = {
                "count": len(entries),
                "human_ratings": {
                    k: {"avg": avg(h(k)), "count": len(h(k))}
                    for k in ["overall", "task_success", "clarity", "empathy", "accuracy"]
                },
                "laj_evaluation": {
                    k: {"avg": avg(l(k)), "count": len(l(k))}
                    for k in ["overall", "task_success", "clarity", "empathy"]
                },
                "sessions": entries
            }

        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Report saved to {output_file}")

        return report


def main():
    parser = argparse.ArgumentParser(description="Analyze human conversations with human ratings + LLM evaluation")
    parser.add_argument("--output", type=str, default="human_laj_combined_analysis.json")
    args = parser.parse_args()

    try:
        analyzer = HumanLAJAnalyzer()
        report = analyzer.generate_combined_report(args.output)
        print(f"\nCombined Human + LLM Analysis")
        print(f"Total sessions: {report['summary']['total_sessions']}")
        print(f"Feedback collected: {report['summary']['feedback_collected']}")
        print(f"Groups: {list(report['by_group'].keys())}")
        print(f"\nFull report saved to: {args.output}")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
