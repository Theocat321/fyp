#!/usr/bin/env python3
"""
Pull and analyse behavioural telemetry from Supabase interaction_events.

Computes per-session metrics (typing duration, response latency, session length,
conversation depth) aggregated by participant group, and exports written feedback
from support_feedback.comments_other.

Usage:
    python3 pull_behaviour_data.py
    python3 pull_behaviour_data.py --output behaviour_data.json
"""
import argparse
import json
import logging
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class BehaviourPuller:

    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not (self.url and self.key):
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _get(self, table: str, params: dict) -> list:
        """Fetch all rows from a table with pagination."""
        rows = []
        offset = 0
        limit = 1000
        while True:
            resp = requests.get(
                f"{self.url}/rest/v1/{table}",
                headers=self.headers,
                params={**params, "offset": offset, "limit": limit},
                timeout=15,
            )
            if resp.status_code not in (200, 206):
                logger.error(f"Failed to fetch {table}: status {resp.status_code}")
                break
            batch = resp.json() if isinstance(resp.json(), list) else []
            if not batch:
                break
            rows.extend(batch)
            offset += limit
            if len(batch) < limit:
                break
        return rows

    def fetch_interaction_events(self) -> list:
        logger.info("Fetching interaction_events...")
        events = self._get("interaction_events", {"select": "*", "order": "client_ts.asc"})
        # Filter to human sessions only
        human = [e for e in events if not str(e.get("session_id", "")).startswith("sim_")]
        logger.info(f"Fetched {len(events)} total events → {len(human)} human-session events")
        return human

    def fetch_feedback(self) -> list:
        logger.info("Fetching support_feedback...")
        feedback = self._get("support_feedback", {"select": "*"})
        human = [f for f in feedback if not str(f.get("session_id", "")).startswith("sim_")]
        logger.info(f"Fetched {len(feedback)} total feedback → {len(human)} human")
        return human

    def fetch_messages(self) -> list:
        logger.info("Fetching messages...")
        messages = self._get("messages", {"select": "session_id,role,participant_group,created_at"})
        human = [m for m in messages if not str(m.get("session_id", "")).startswith("sim_")]
        logger.info(f"Fetched {len(messages)} total messages → {len(human)} human")
        return human

    def _parse_ts(self, ts):
        """Parse a timestamp (ISO string or epoch ms) to epoch seconds."""
        if ts is None:
            return None
        if isinstance(ts, (int, float)):
            # epoch ms if large, else seconds
            return ts / 1000 if ts > 1e10 else float(ts)
        try:
            dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
            return dt.timestamp()
        except Exception:
            return None

    def compute_session_metrics(self, events: list, messages: list, feedback: list) -> dict:
        """Compute per-session behavioural metrics."""

        # Index feedback and messages by session
        feedback_by_session = {f["session_id"]: f for f in feedback if f.get("session_id")}
        messages_by_session = defaultdict(list)
        for m in messages:
            sid = m.get("session_id")
            if sid:
                messages_by_session[sid].append(m)

        # Group events by session
        events_by_session = defaultdict(list)
        for e in events:
            sid = e.get("session_id")
            if sid:
                events_by_session[sid].append(e)

        sessions = {}
        for sid, evts in events_by_session.items():
            group = None
            for e in evts:
                if e.get("participant_group"):
                    group = e["participant_group"]
                    break

            # Fall back to messages for group
            if not group and sid in messages_by_session:
                for m in messages_by_session[sid]:
                    if m.get("participant_group"):
                        group = m["participant_group"]
                        break

            if group not in ("A", "B"):
                continue

            # Session duration: first to last client_ts
            timestamps = [self._parse_ts(e.get("client_ts")) for e in evts]
            timestamps = [t for t in timestamps if t is not None]
            session_duration_s = (max(timestamps) - min(timestamps)) if len(timestamps) >= 2 else None

            # Typing durations (typing_end events with duration_ms)
            typing_durations = [
                e["duration_ms"] for e in evts
                if e.get("event") == "typing_end" and e.get("duration_ms") is not None
            ]

            # Response latency: reply_done events carry duration_ms = server processing time
            reply_latencies = [
                e["duration_ms"] for e in evts
                if e.get("event") == "reply_done" and e.get("duration_ms") is not None
            ]

            # Message counts from messages table
            session_messages = messages_by_session.get(sid, [])
            user_turns = sum(1 for m in session_messages if m.get("role") == "user")
            assistant_turns = sum(1 for m in session_messages if m.get("role") == "assistant")

            # Event type breakdown
            event_counts = defaultdict(int)
            for e in evts:
                event_counts[e.get("event", "unknown")] += 1

            # Feedback
            fb = feedback_by_session.get(sid, {})
            written_feedback = fb.get("comments_other", "").strip() if fb.get("comments_other") else None
            resolved = fb.get("resolved")

            sessions[sid] = {
                "session_id": sid,
                "group": group,
                "session_duration_s": round(session_duration_s, 1) if session_duration_s is not None else None,
                "user_turns": user_turns,
                "assistant_turns": assistant_turns,
                "total_events": len(evts),
                "event_counts": dict(event_counts),
                "typing_durations_ms": typing_durations,
                "avg_typing_duration_ms": round(sum(typing_durations) / len(typing_durations)) if typing_durations else None,
                "reply_latencies_ms": reply_latencies,
                "avg_reply_latency_ms": round(sum(reply_latencies) / len(reply_latencies)) if reply_latencies else None,
                "has_feedback": bool(fb),
                "resolved": resolved,
                "written_feedback": written_feedback,
            }

        return sessions

    def aggregate_by_group(self, sessions: dict) -> dict:
        """Aggregate session metrics by group."""
        groups = {"A": [], "B": []}
        for s in sessions.values():
            g = s.get("group")
            if g in groups:
                groups[g].append(s)

        def avg(vals):
            vals = [v for v in vals if v is not None]
            return round(sum(vals) / len(vals), 1) if vals else None

        def pct(items, pred):
            n = len(items)
            return round(100 * sum(1 for i in items if pred(i)) / n, 1) if n else None

        summary = {}
        for group, slist in groups.items():
            if not slist:
                continue

            typing = [s["avg_typing_duration_ms"] for s in slist if s.get("avg_typing_duration_ms")]
            latency = [s["avg_reply_latency_ms"] for s in slist if s.get("avg_reply_latency_ms")]
            duration = [s["session_duration_s"] for s in slist if s.get("session_duration_s")]
            user_turns = [s["user_turns"] for s in slist if s["user_turns"] > 0]

            written = [s["written_feedback"] for s in slist if s.get("written_feedback")]

            summary[group] = {
                "n_sessions": len(slist),
                "n_with_feedback": sum(1 for s in slist if s["has_feedback"]),
                "avg_session_duration_s": avg(duration),
                "avg_user_turns": avg(user_turns),
                "avg_typing_duration_ms": avg(typing),
                "avg_reply_latency_ms": avg(latency),
                "resolved_pct": pct(slist, lambda s: s.get("resolved") is True),
                "written_feedback_count": len(written),
                "written_feedback": written,
            }

        return summary


def main():
    parser = argparse.ArgumentParser(description="Pull behavioural data from Supabase")
    parser.add_argument("--output", default="behaviour_data.json")
    args = parser.parse_args()

    try:
        puller = BehaviourPuller()
    except RuntimeError as e:
        logger.error(str(e))
        sys.exit(1)

    events = puller.fetch_interaction_events()
    feedback = puller.fetch_feedback()
    messages = puller.fetch_messages()

    if not events:
        logger.warning("No interaction events found. Is telemetry being logged?")

    sessions = puller.compute_session_metrics(events, messages, feedback)
    summary = puller.aggregate_by_group(sessions)

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_sessions": len(sessions),
        "summary_by_group": summary,
        "sessions": list(sessions.values()),
    }

    with open(args.output, "w") as f:
        json.dump(output, f, indent=2)
    logger.info(f"Written to {args.output}")

    # Print summary
    print("\n" + "=" * 65)
    print("BEHAVIOURAL DATA SUMMARY")
    print("=" * 65)
    print(f"Total sessions with telemetry: {len(sessions)}")
    print()
    for group, stats in summary.items():
        print(f"Group {group} (n={stats['n_sessions']})")
        print(f"  Sessions with feedback:    {stats['n_with_feedback']}")
        print(f"  Avg session duration:      {stats['avg_session_duration_s']}s")
        print(f"  Avg user turns:            {stats['avg_user_turns']}")
        print(f"  Avg typing duration:       {stats['avg_typing_duration_ms']}ms")
        print(f"  Avg reply latency:         {stats['avg_reply_latency_ms']}ms")
        print(f"  Resolved %:                {stats['resolved_pct']}%")
        print(f"  Written feedback entries:  {stats['written_feedback_count']}")
        print()

    # Print written feedback
    for group, stats in summary.items():
        if stats.get("written_feedback"):
            print(f"--- Written feedback Group {group} ---")
            for i, text in enumerate(stats["written_feedback"], 1):
                print(f"  [{i}] {text}")
            print()

    print("=" * 65)


if __name__ == "__main__":
    main()
