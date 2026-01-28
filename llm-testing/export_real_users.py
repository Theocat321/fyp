#!/usr/bin/env python3
"""
Export real user conversations from Supabase to CSV for evaluation.

This script fetches messages from your Supabase database (filtering out sim_ sessions)
and exports them to CSV format for evaluation.

Usage:
    python3 export_real_users.py --output real_conversations.csv
"""
import argparse
import csv
import sys
from pathlib import Path
import os

# Add server app to path to use its storage module
sys.path.insert(0, str(Path(__file__).parent.parent / "server"))

from app.storage import SupabaseStore


def export_real_conversations(output_path: Path, limit: int = None):
    """
    Export real user conversations (excluding sim_ sessions) to CSV.

    Args:
        output_path: Path to output CSV file
        limit: Optional limit on number of messages to fetch
    """
    store = SupabaseStore()

    if not store.is_configured():
        print("ERROR: Supabase not configured. Check SUPABASE_URL and SUPABASE_SERVICE_KEY env vars.")
        sys.exit(1)

    print("Fetching messages from Supabase...")

    # Fetch all messages (we'll filter in Python since PostgREST filtering is tricky)
    messages, status = store.select_rows(
        table="messages",
        params={},
        select="*",
        order="created_at.asc",
        limit=limit
    )

    if status != 200:
        print(f"ERROR: Failed to fetch messages (status {status})")
        sys.exit(1)

    print(f"Fetched {len(messages)} messages")

    # Filter out simulated conversations (session_id starts with "sim_")
    real_messages = [
        msg for msg in messages
        if not msg.get('session_id', '').startswith('sim_')
    ]

    print(f"Filtered to {len(real_messages)} real user messages")

    if not real_messages:
        print("WARNING: No real user messages found!")
        print("Make sure you have real users (not starting with 'sim_') in your database.")
        sys.exit(0)

    # Write to CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'session_id',
            'participant_id',
            'participant_group',
            'role',
            'content',
            'created_at'
        ])

        writer.writeheader()

        for msg in real_messages:
            writer.writerow({
                'session_id': msg.get('session_id', ''),
                'participant_id': msg.get('participant_id', ''),
                'participant_group': msg.get('participant_group', ''),
                'role': msg.get('role', ''),
                'content': msg.get('content', ''),
                'created_at': msg.get('created_at', '')
            })

    print(f"\n✓ Exported {len(real_messages)} messages to {output_path}")

    # Show session breakdown
    sessions = set(msg.get('session_id') for msg in real_messages)
    print(f"✓ {len(sessions)} unique sessions")

    # Show variant breakdown
    variants = {}
    for msg in real_messages:
        variant = msg.get('participant_group', 'unknown')
        variants[variant] = variants.get(variant, 0) + 1

    print("\nVariant breakdown:")
    for variant, count in sorted(variants.items()):
        print(f"  {variant}: {count} messages")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Export real user conversations from Supabase to CSV"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="data/real_conversations.csv",
        help="Output CSV file path"
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of messages to fetch (for testing)"
    )

    args = parser.parse_args()

    export_real_conversations(Path(args.output), args.limit)


if __name__ == "__main__":
    main()
