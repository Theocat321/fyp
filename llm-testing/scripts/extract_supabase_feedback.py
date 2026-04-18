#!/usr/bin/env python3
"""
Script to extract human feedback responses from Supabase support_feedback table
and bucket them into separate text files for Group A and Group B.
"""

import os
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

def extract_feedback():
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    response = supabase.table('support_feedback').select('*').execute()
    feedback_data = response.data

    group_a_feedback = []
    group_b_feedback = []

    for feedback in feedback_data:
        if feedback.get('comments_other'):
            entry = {
                'session_id': feedback.get('session_id'),
                'participant_id': feedback.get('participant_id'),
                'comment': feedback.get('comments_other'),
                'created_at': feedback.get('created_at')
            }

            group = feedback.get('participant_group', '').upper()
            if group == 'A':
                group_a_feedback.append(entry)
            elif group == 'B':
                group_b_feedback.append(entry)

    with open(Path(__file__).parent.parent / "outputs" / "group_a_feedback.txt", 'w') as f:
        f.write(f"=== GROUP A HUMAN FEEDBACK ===\n")
        f.write(f"Total feedback entries: {len(group_a_feedback)}\n\n")
        for i, feedback in enumerate(group_a_feedback, 1):
            f.write(f"--- Feedback {i} ---\n")
            f.write(f"Session ID: {feedback['session_id']}\n")
            f.write(f"Participant ID: {feedback['participant_id']}\n")
            f.write(f"Created At: {feedback['created_at']}\n")
            f.write(f"Comment:\n{feedback['comment']}\n")
            f.write("\n" + "="*80 + "\n\n")

    with open(Path(__file__).parent.parent / "outputs" / "group_b_feedback.txt", 'w') as f:
        f.write(f"=== GROUP B HUMAN FEEDBACK ===\n")
        f.write(f"Total feedback entries: {len(group_b_feedback)}\n\n")
        for i, feedback in enumerate(group_b_feedback, 1):
            f.write(f"--- Feedback {i} ---\n")
            f.write(f"Session ID: {feedback['session_id']}\n")
            f.write(f"Participant ID: {feedback['participant_id']}\n")
            f.write(f"Created At: {feedback['created_at']}\n")
            f.write(f"Comment:\n{feedback['comment']}\n")
            f.write("\n" + "="*80 + "\n\n")

    print(f"✓ Extracted {len(group_a_feedback)} feedback entries from Group A → group_a_feedback.txt")
    print(f"✓ Extracted {len(group_b_feedback)} feedback entries from Group B → group_b_feedback.txt")

if __name__ == "__main__":
    extract_feedback()
