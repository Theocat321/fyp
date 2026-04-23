import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app, store


client = TestClient(app)


# --- health ---

def test_health_ok():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["provider"] == "VodaCare"
    assert "storage_configured" in data


def test_health_storage_false_without_config():
    resp = client.get("/api/health")
    assert resp.json()["storage_configured"] is False


# --- chat ---

def test_chat_returns_required_fields():
    resp = client.post("/api/chat", json={"message": "How do I check my data?"})
    assert resp.status_code == 200
    data = resp.json()
    assert "reply" in data
    assert "topic" in data
    assert "session_id" in data
    assert "escalate" in data
    assert "suggestions" in data


def test_chat_reuses_session_id():
    resp = client.post("/api/chat", json={"message": "hello", "session_id": "test-sess"})
    assert resp.json()["session_id"] == "test-sess"


def test_chat_error_reply_without_llm():
    resp = client.post("/api/chat", json={"message": "tell me about plans"})
    assert "problem" in resp.json()["reply"].lower() or "working" in resp.json()["reply"].lower()


def test_chat_escalate_on_human_request():
    resp = client.post("/api/chat", json={"message": "I want to talk to a human"})
    assert resp.json()["escalate"] is True


def test_chat_topic_detection():
    resp = client.post("/api/chat", json={"message": "What are my roaming options?"})
    assert resp.json()["topic"] == "roaming"


# --- interaction ---

def test_interaction_single_event():
    payload = {
        "session_id": "s1",
        "event": "page_view",
        "component": "chat",
    }
    resp = client.post("/api/interaction", json=payload)
    assert resp.status_code in (200, 202)
    assert resp.json()["ok"] is True


def test_interaction_array_of_events():
    payload = [
        {"session_id": "s1", "event": "click"},
        {"session_id": "s1", "event": "submit"},
    ]
    resp = client.post("/api/interaction", json=payload)
    assert resp.status_code in (200, 202)


def test_interaction_events_wrapper():
    payload = {"events": [{"session_id": "s1", "event": "focus"}]}
    resp = client.post("/api/interaction", json=payload)
    assert resp.status_code in (200, 202)


def test_interaction_invalid_json():
    resp = client.post(
        "/api/interaction",
        content=b"not json",
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 400


def test_interaction_compact_shape_skipped():
    payload = {"group": "A", "input": "hello", "output": "hi"}
    resp = client.post("/api/interaction", json=payload)
    assert resp.status_code == 202
    assert resp.json()["stored"] == 0


def test_interaction_missing_session_id_skipped():
    payload = {"event": "click"}  # no session_id
    resp = client.post("/api/interaction", json=payload)
    assert resp.status_code == 202


# --- participants ---

def test_participants_upsert():
    with patch.object(store, "insert_rows", return_value=(1, 200)):
        resp = client.post("/api/participants", json={
            "participant_id": "p1",
            "name": "Alice",
            "group": "A",
            "session_id": "s1",
        })
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_participants_session_only_update():
    with patch.object(store, "update_by_pk", return_value=(1, 200)):
        resp = client.post("/api/participants", json={
            "participant_id": "p1",
            "session_id": "s-new",
        })
    assert resp.status_code == 200
    assert resp.json()["updated"] == 1


# --- messages ---

def test_messages_post():
    with patch.object(store, "insert_rows", return_value=(1, 200)):
        resp = client.post("/api/messages", json={
            "session_id": "s1",
            "role": "user",
            "content": "Hello",
        })
    assert resp.status_code == 200


def test_messages_get_returns_list():
    with patch.object(store, "select_rows", return_value=([
        {"role": "user", "content": "hi", "session_id": "s1"}
    ], 200)):
        resp = client.get("/api/messages?session_id=s1")
    assert resp.status_code == 200
    assert isinstance(resp.json()["messages"], list)


def test_messages_get_empty_without_storage():
    resp = client.get("/api/messages?session_id=nonexistent")
    assert "messages" in resp.json()


# --- scenarios ---

def test_scenarios_returns_list():
    resp = client.get("/api/scenarios")
    assert resp.status_code == 200
    scenarios = resp.json()["scenarios"]
    assert isinstance(scenarios, list)
    assert len(scenarios) > 0


def test_scenarios_have_required_fields():
    resp = client.get("/api/scenarios")
    for s in resp.json()["scenarios"]:
        assert "id" in s
        assert "name" in s
        assert "topic" in s


# --- feedback ---

def test_feedback_fails_without_storage():
    resp = client.post("/api/feedback", json={
        "session_id": "s1",
        "rating_overall": 4,
        "rating_task_success": 5,
        "rating_clarity": 4,
        "rating_empathy": 3,
        "rating_accuracy": 4,
    })
    assert resp.status_code == 500
    assert resp.json()["ok"] is False


def test_feedback_ok_with_storage():
    with patch.object(store, "insert_rows", return_value=(1, 200)), \
         patch.object(store, "is_configured", return_value=True):
        resp = client.post("/api/feedback", json={
            "session_id": "s1",
            "rating_overall": 5,
            "rating_task_success": 5,
            "rating_clarity": 5,
            "rating_empathy": 5,
            "rating_accuracy": 5,
        })
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
