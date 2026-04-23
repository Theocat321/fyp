import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from unittest.mock import patch, MagicMock
from app.storage import SupabaseStore


@pytest.fixture
def unconfigured():
    return SupabaseStore()


@pytest.fixture
def configured():
    store = SupabaseStore()
    store.url = "https://example.supabase.co"
    store.key = "service-key-abc"
    return store


# --- is_configured ---

def test_not_configured_without_url_and_key(unconfigured):
    assert unconfigured.is_configured() is False


def test_configured_with_both(configured):
    assert configured.is_configured() is True


def test_not_configured_missing_key(configured):
    configured.key = None
    assert configured.is_configured() is False


# --- insert_rows ---

def test_insert_rows_skips_when_not_configured(unconfigured):
    stored, code = unconfigured.insert_rows("messages", [{"content": "hi"}])
    assert stored == 0
    assert code == 202


def test_insert_rows_success(configured):
    mock_resp = MagicMock()
    mock_resp.status_code = 201
    with patch("app.storage.requests.post", return_value=mock_resp):
        stored, code = configured.insert_rows("messages", [{"content": "a"}, {"content": "b"}])
    assert stored == 2
    assert code == 201


def test_insert_rows_409_treated_as_no_op(configured):
    mock_resp = MagicMock()
    mock_resp.status_code = 409
    with patch("app.storage.requests.post", return_value=mock_resp):
        stored, code = configured.insert_rows("participants", [{"participant_id": "p1"}])
    assert stored == 0
    assert code == 200


def test_insert_rows_server_error_returns_zero(configured):
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "internal error"
    with patch("app.storage.requests.post", return_value=mock_resp):
        stored, code = configured.insert_rows("messages", [{"content": "hi"}])
    assert stored == 0
    assert code == 500


def test_insert_rows_upsert_appends_on_conflict_param(configured):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    with patch("app.storage.requests.post", return_value=mock_resp) as mock_post:
        configured.insert_rows("participants", [{}], upsert=True, on_conflict="participant_id")
    url_called = mock_post.call_args[0][0]
    assert "on_conflict=participant_id" in url_called


# --- update_by_pk ---

def test_update_skips_when_not_configured(unconfigured):
    updated, code = unconfigured.update_by_pk("participants", "participant_id", "p1", {"session_id": "s1"})
    assert updated == 0
    assert code == 202


def test_update_success(configured):
    mock_resp = MagicMock()
    mock_resp.status_code = 204
    with patch("app.storage.requests.patch", return_value=mock_resp):
        updated, code = configured.update_by_pk("participants", "participant_id", "p1", {"session_id": "s2"})
    assert updated == 1
    assert code == 204


def test_update_uses_eq_filter(configured):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    with patch("app.storage.requests.patch", return_value=mock_resp) as mock_patch:
        configured.update_by_pk("participants", "participant_id", "p99", {"session_id": "s"})
    url_called = mock_patch.call_args[0][0]
    assert "participant_id=eq.p99" in url_called


# --- select_rows ---

def test_select_skips_when_not_configured(unconfigured):
    rows, code = unconfigured.select_rows("messages", {"session_id": "s1"})
    assert rows == []
    assert code == 202


def test_select_returns_rows(configured):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [{"role": "user", "content": "hi"}]
    with patch("app.storage.requests.get", return_value=mock_resp):
        rows, code = configured.select_rows("messages", {"session_id": "s1"})
    assert len(rows) == 1
    assert rows[0]["role"] == "user"


def test_select_builds_eq_filter(configured):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = []
    with patch("app.storage.requests.get", return_value=mock_resp) as mock_get:
        configured.select_rows("messages", {"session_id": "abc"}, limit=10)
    params = mock_get.call_args[1]["params"]
    assert params["session_id"] == "eq.abc"
    assert params["limit"] == "10"


def test_select_none_filter_values_skipped(configured):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = []
    with patch("app.storage.requests.get", return_value=mock_resp) as mock_get:
        configured.select_rows("messages", {"session_id": "s1", "participant_id": None})
    params = mock_get.call_args[1]["params"]
    assert "participant_id" not in params
