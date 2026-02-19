#!/usr/bin/env python3
"""Verify that experiment data is being saved to Supabase database."""
import requests
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from collections import defaultdict

# Load environment
load_dotenv(Path(__file__).parent.parent / ".env")

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not (supabase_url and supabase_key):
    print("❌ Supabase not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env")
    exit(1)

headers = {
    "apikey": supabase_key,
    "Authorization": f"Bearer {supabase_key}",
    "Content-Type": "application/json",
}

def get_count(table):
    """Get count of rows in a table."""
    resp = requests.get(
        f"{supabase_url}/rest/v1/{table}?select=id&limit=1",
        headers={**headers, "Prefer": "count=exact"},
        timeout=5
    )
    try:
        content_range = resp.headers.get("content-range", "")
        if "/" in content_range:
            return int(content_range.split("/")[1])
    except:
        pass
    return 0

def get_recent_messages(limit=10):
    """Get recent messages from experiment."""
    resp = requests.get(
        f"{supabase_url}/rest/v1/messages?limit={limit}&order=created_at.desc",
        headers=headers,
        timeout=5
    )
    return resp.json() if isinstance(resp.json(), list) else []

def get_recent_participants(limit=10):
    """Get recent participants from experiment."""
    resp = requests.get(
        f"{supabase_url}/rest/v1/participants?limit={limit}&order=created_at.desc",
        headers=headers,
        timeout=5
    )
    return resp.json() if isinstance(resp.json(), list) else []

def get_sessions_by_persona():
    """Group messages by persona to show coverage."""
    resp = requests.get(
        f"{supabase_url}/rest/v1/messages?select=session_id&limit=500",
        headers=headers,
        timeout=5
    )
    messages = resp.json() if isinstance(resp.json(), list) else []

    sessions_by_persona = defaultdict(int)
    for msg in messages:
        session_id = msg.get('session_id', '')
        # Parse persona from session_id: sim_persona_XX_...
        if session_id.startswith('sim_'):
            parts = session_id.split('_')
            if len(parts) >= 3:
                persona = '_'.join(parts[:3])
                sessions_by_persona[persona] += 1

    return dict(sorted(sessions_by_persona.items()))

print("=" * 70)
print("DATABASE VERIFICATION REPORT")
print("=" * 70)

# Count check
print("\n📊 TABLE COUNTS:")
msg_count = get_count("messages")
part_count = get_count("participants")
print(f"  Messages: {msg_count:,}")
print(f"  Participants: {part_count:,}")

if msg_count == 0:
    print("\n⚠️  No messages found in database!")
else:
    print(f"\n✅ Data is being saved! Messages and participants detected.")

    # Recent participants
    print("\n👤 RECENT PARTICIPANTS:")
    recent_parts = get_recent_participants(5)
    for p in recent_parts:
        pid = p.get('participant_id', 'unknown')[:20]
        name = p.get('name', 'unnamed')[:30]
        group = p.get('group', '?')
        ts = p.get('created_at', '')[:10]
        print(f"  [{ts}] {pid}: {name} (group: {group})")

    # Recent messages
    print("\n📨 RECENT MESSAGES:")
    recent = get_recent_messages(5)
    for msg in recent:
        ts = msg.get('created_at', '')[:10]
        session = msg.get('session_id', 'unknown')[:40]
        role = msg.get('role', '?')
        content = msg.get('content', '')[:40]
        print(f"  [{ts}] {session}")
        print(f"      {role}: {content}...")

    # Coverage by persona
    print("\n👥 EXPERIMENT COVERAGE (by persona):")
    coverage = get_sessions_by_persona()
    for persona, count in sorted(coverage.items()):
        print(f"  {persona}: {count} messages")

    if coverage:
        total_personas = len(coverage)
        print(f"\n  Total personas: {total_personas}")

print("\n" + "=" * 70)
