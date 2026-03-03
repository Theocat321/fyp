#!/usr/bin/env python3
"""
Script to extract all written responses (rationales) from the JSON file
and bucket them into separate text files for Group A and Group B.
"""

import json

def extract_and_bucket_responses():
    # Load the JSON data
    with open('/Users/stagcto/fyp/llm-testing/human_laj_combined_analysis.json', 'r') as f:
        data = json.load(f)

    # Extract responses for Group A
    group_a_responses = []
    for session in data['by_group']['A']['sessions']:
        if 'laj_evaluation' in session and 'rationale' in session['laj_evaluation']:
            rationale = session['laj_evaluation']['rationale']
            if rationale:
                group_a_responses.append({
                    'session_id': session['session_id'],
                    'rationale': rationale
                })

    # Extract responses for Group B
    group_b_responses = []
    for session in data['by_group']['B']['sessions']:
        if 'laj_evaluation' in session and 'rationale' in session['laj_evaluation']:
            rationale = session['laj_evaluation']['rationale']
            if rationale:
                group_b_responses.append({
                    'session_id': session['session_id'],
                    'rationale': rationale
                })

    # Write Group A responses to file
    with open('/Users/stagcto/fyp/group_a_responses.txt', 'w') as f:
        f.write(f"=== GROUP A RESPONSES ===\n")
        f.write(f"Total responses: {len(group_a_responses)}\n\n")
        for i, response in enumerate(group_a_responses, 1):
            f.write(f"--- Session {i} ({response['session_id']}) ---\n")
            f.write(response['rationale'])
            f.write("\n\n")

    # Write Group B responses to file
    with open('/Users/stagcto/fyp/group_b_responses.txt', 'w') as f:
        f.write(f"=== GROUP B RESPONSES ===\n")
        f.write(f"Total responses: {len(group_b_responses)}\n\n")
        for i, response in enumerate(group_b_responses, 1):
            f.write(f"--- Session {i} ({response['session_id']}) ---\n")
            f.write(response['rationale'])
            f.write("\n\n")

    print(f"✓ Extracted {len(group_a_responses)} responses from Group A → group_a_responses.txt")
    print(f"✓ Extracted {len(group_b_responses)} responses from Group B → group_b_responses.txt")

if __name__ == "__main__":
    extract_and_bucket_responses()
