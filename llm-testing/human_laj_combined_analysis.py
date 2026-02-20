#!/usr/bin/env python3
"""
Combined Human Self-Ratings + LLM-as-Judge Analysis

Fetches all human conversations, collects both:
1. Human self-ratings from feedback table
2. LLM-as-Judge evaluations of the conversations

Separates results by Group A and B for A/B testing comparison.

Usage:
    python3 human_laj_combined_analysis.py
    python3 human_laj_combined_analysis.py --output combined_report.json
"""
import argparse
import json
import logging
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import defaultdict

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "server"))

import requests
from dotenv import load_dotenv

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# Load environment
load_dotenv(Path(__file__).parent.parent / ".env")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HumanLAJAnalyzer:
    """Analyze human conversations with both self-ratings and LLM-as-Judge."""

    def __init__(self):
        """Initialize analyzer."""
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not (self.supabase_url and self.supabase_key):
            raise RuntimeError("Supabase not configured")

        self.headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json",
        }

        # Initialize OpenAI if available
        api_key = os.getenv("OPENAI_API_KEY")
        self.llm_client = OpenAI(api_key=api_key) if api_key and OpenAI else None
        self.llm_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def fetch_all_messages(self) -> List[Dict[str, Any]]:
        """Fetch all messages from database."""
        logger.info("Fetching all messages from Supabase...")

        all_messages = []
        offset = 0
        limit = 1000

        while True:
            resp = requests.get(
                f"{self.supabase_url}/rest/v1/messages?offset={offset}&limit={limit}",
                headers=self.headers,
                timeout=10
            )

            if resp.status_code != 200:
                break

            batch = resp.json() if isinstance(resp.json(), list) else []
            if not batch:
                break

            all_messages.extend(batch)
            offset += limit

        # Filter to human data
        human_messages = [
            m for m in all_messages
            if m.get('participant_id')
            and not str(m.get('participant_id')).lower().startswith('llm')
        ]

        logger.info(f"Fetched {len(human_messages)} human messages")
        return human_messages

    def fetch_feedback(self) -> List[Dict[str, Any]]:
        """Fetch feedback from database."""
        logger.info("Fetching feedback from Supabase...")

        resp = requests.get(
            f"{self.supabase_url}/rest/v1/support_feedback",
            headers=self.headers,
            timeout=10
        )

        if resp.status_code != 200:
            return []

        feedback = resp.json() if isinstance(resp.json(), list) else []
        logger.info(f"Fetched {len(feedback)} feedback entries")
        return feedback

    def group_messages_by_session(self, messages: List[Dict[str, Any]]) -> Dict[str, List]:
        """Group messages by session ID."""
        sessions = defaultdict(list)
        for msg in messages:
            sid = msg.get('session_id')
            if sid:
                sessions[sid].append(msg)
        return dict(sessions)

    def evaluate_session_with_llm(self, session_id: str, messages: List[Dict]) -> Dict[str, Any]:
        """Evaluate a session using LLM-as-Judge (matches simulation framework)."""
        if not self.llm_client:
            logger.warning(f"LLM client not available, skipping LAJ for {session_id}")
            return {
                "task_success": 0,
                "clarity": 0,
                "empathy": 0,
                "policy_compliance": 0,
                "overall": 0,
                "error": "LLM not configured"
            }

        # Build transcript in same format as simulation
        transcript_lines = []
        for i, msg in enumerate(sorted(messages, key=lambda m: m.get('created_at', '')), 1):
            role = "USER" if msg.get('role') == 'user' else "ASSISTANT"
            content = msg.get('content', '')
            transcript_lines.append(f"[Turn {i}] {role}: {content}")
        transcript_text = "\n".join(transcript_lines)

        # Build prompt matching the simulation framework
        prompt = f"""Evaluate this customer service conversation based on the following criteria.

# TRANSCRIPT
{transcript_text}

# EVALUATION RUBRIC

TASK_SUCCESS (weight: 0.5)
Did the assistant successfully help the customer accomplish their goal? Did they address the customer's needs?

CLARITY (weight: 0.2)
Were the assistant's responses clear, well-structured, and easy to understand?

EMPATHY (weight: 0.2)
Was the assistant appropriately empathetic and supportive of the customer's situation?

POLICY_COMPLIANCE (weight: 0.1)
Were there any policy violations, hallucinations, or harmful recommendations?

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

POLICY_COMPLIANCE: [score]
Rationale: [explanation]

OVERALL ASSESSMENT:
[Summary of conversation quality]
"""

        # Evaluate with LLM
        try:
            response = self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert evaluator of customer service conversations. Provide objective, detailed assessments based on the given criteria."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1000
            )

            evaluation_text = response.choices[0].message.content.strip()

            # Parse scores using same method as simulation
            import re

            def extract_score(text: str, dimension: str) -> float:
                pattern = rf"{dimension}:\s*([0-9]*\.?[0-9]+)"
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        score = float(match.group(1))
                        return max(0.0, min(1.0, score))
                    except ValueError:
                        return 0.5
                return 0.5

            task_success = extract_score(evaluation_text, "TASK_SUCCESS")
            clarity = extract_score(evaluation_text, "CLARITY")
            empathy = extract_score(evaluation_text, "EMPATHY")
            policy_compliance = extract_score(evaluation_text, "POLICY_COMPLIANCE")

            # Calculate weighted overall (matching simulation weights)
            overall = (
                task_success * 0.5 +
                clarity * 0.2 +
                empathy * 0.2 +
                policy_compliance * 0.1
            )

            return {
                "task_success": task_success,
                "clarity": clarity,
                "empathy": empathy,
                "policy_compliance": policy_compliance,
                "overall": overall,
                "rationale": evaluation_text
            }

        except Exception as e:
            logger.debug(f"LLM evaluation error for {session_id}: {e}")
            return {
                "task_success": 0,
                "clarity": 0,
                "empathy": 0,
                "policy_compliance": 0,
                "overall": 0,
                "error": str(e)
            }

    def generate_combined_report(self, output_file: Optional[str] = None) -> Dict[str, Any]:
        """Generate combined human + LLM report."""
        logger.info("Generating combined report...")

        # Fetch all data
        messages = self.fetch_all_messages()
        feedback = self.fetch_feedback()
        sessions = self.group_messages_by_session(messages)

        # Map feedback by session
        feedback_by_session = {f.get('session_id'): f for f in feedback if f.get('session_id')}

        # Evaluate sessions with LLM
        logger.info(f"Evaluating {len(sessions)} sessions with LLM-as-Judge...")
        laj_results = {}
        for i, (session_id, session_messages) in enumerate(sessions.items(), 1):
            if i % 10 == 0:
                logger.info(f"  Evaluated {i}/{len(sessions)} sessions...")
            laj_results[session_id] = self.evaluate_session_with_llm(session_id, session_messages)

        # Organize by group
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

        # Calculate summary statistics
        def calc_stats(entries, key):
            values = [e[key] for e in entries if key in e and e[key]]
            return {
                "count": len(values),
                "avg": round(sum(values) / len(values), 3) if values else 0,
                "min": round(min(values), 3) if values else 0,
                "max": round(max(values), 3) if values else 0,
            }

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

        # Add group statistics
        for group in ["A", "B"]:
            entries = group_data[group]
            if not entries:
                continue

            # Extract nested values for human ratings
            human_overall = [e["human_ratings"].get("overall") for e in entries if e["human_ratings"].get("overall")]
            human_task = [e["human_ratings"].get("task_success") for e in entries if e["human_ratings"].get("task_success")]
            human_clarity = [e["human_ratings"].get("clarity") for e in entries if e["human_ratings"].get("clarity")]
            human_empathy = [e["human_ratings"].get("empathy") for e in entries if e["human_ratings"].get("empathy")]
            human_accuracy = [e["human_ratings"].get("accuracy") for e in entries if e["human_ratings"].get("accuracy")]

            # Extract values for LLM evaluation
            laj_overall = [e["laj_evaluation"].get("overall", 0) for e in entries if e["laj_evaluation"].get("overall") is not None]
            laj_task = [e["laj_evaluation"].get("task_success", 0) for e in entries if e["laj_evaluation"].get("task_success") is not None]
            laj_clarity = [e["laj_evaluation"].get("clarity", 0) for e in entries if e["laj_evaluation"].get("clarity") is not None]
            laj_empathy = [e["laj_evaluation"].get("empathy", 0) for e in entries if e["laj_evaluation"].get("empathy") is not None]
            laj_policy = [e["laj_evaluation"].get("policy_compliance", 0) for e in entries if e["laj_evaluation"].get("policy_compliance") is not None]

            report["by_group"][group] = {
                "count": len(entries),
                "human_ratings": {
                    "overall": {"avg": round(sum(human_overall) / len(human_overall), 2) if human_overall else 0, "count": len(human_overall)},
                    "task_success": {"avg": round(sum(human_task) / len(human_task), 2) if human_task else 0, "count": len(human_task)},
                    "clarity": {"avg": round(sum(human_clarity) / len(human_clarity), 2) if human_clarity else 0, "count": len(human_clarity)},
                    "empathy": {"avg": round(sum(human_empathy) / len(human_empathy), 2) if human_empathy else 0, "count": len(human_empathy)},
                    "accuracy": {"avg": round(sum(human_accuracy) / len(human_accuracy), 2) if human_accuracy else 0, "count": len(human_accuracy)},
                },
                "laj_evaluation": {
                    "overall": {"avg": round(sum(laj_overall) / len(laj_overall), 2) if laj_overall else 0, "count": len(laj_overall)},
                    "task_success": {"avg": round(sum(laj_task) / len(laj_task), 2) if laj_task else 0, "count": len(laj_task)},
                    "clarity": {"avg": round(sum(laj_clarity) / len(laj_clarity), 2) if laj_clarity else 0, "count": len(laj_clarity)},
                    "empathy": {"avg": round(sum(laj_empathy) / len(laj_empathy), 2) if laj_empathy else 0, "count": len(laj_empathy)},
                    "policy_compliance": {"avg": round(sum(laj_policy) / len(laj_policy), 2) if laj_policy else 0, "count": len(laj_policy)},
                },
                "sessions": entries
            }

        # Save report
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Report saved to {output_file}")

        return report


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Analyze human conversations with human ratings + LLM evaluation")
    parser.add_argument(
        "--output",
        type=str,
        default="human_laj_combined_analysis.json",
        help="Output file (default: human_laj_combined_analysis.json)"
    )

    args = parser.parse_args()

    try:
        analyzer = HumanLAJAnalyzer()
        report = analyzer.generate_combined_report(args.output)

        print("\n" + "="*70)
        print("COMBINED HUMAN + LLM ANALYSIS REPORT")
        print("="*70)
        print(f"Total sessions analyzed: {report['summary']['total_sessions']}")
        print(f"Feedback collected: {report['summary']['feedback_collected']}")
        print(f"Groups: {list(report['by_group'].keys())}")
        print("="*70)
        print(f"\n✅ Full report saved to: {args.output}")

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
