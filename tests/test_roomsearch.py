import os

import pytest
from fastapi.testclient import TestClient

from server.retrieve import rank_seed
from server.seed import SEED_DOCS


@pytest.fixture()
def mock_client(monkeypatch, tmp_path):
    monkeypatch.setenv("MOSS_PROJECT_ID", "")
    monkeypatch.setenv("MOSS_PROJECT_KEY", "")
    monkeypatch.setenv("DEMO_MOCK_MOSS", "1")
    monkeypatch.setenv("ROOMSEARCH_DATA", str(tmp_path))
    from server.main import app

    with TestClient(app) as client:
        yield client


def test_lisbon_query_ranks_the_dinner_note():
    hits = rank_seed("Where should we eat in Lisbon?", SEED_DOCS)
    assert hits
    assert hits[0].id == "lisbon-dinner"


def test_mock_search_is_labeled_and_writes_an_episode(mock_client):
    status = mock_client.get("/api/status")
    assert status.status_code == 200
    body = status.json()
    assert body["moss"]["mode"] == "mock"
    assert body["moss"]["ready"] is True

    found = mock_client.post(
        "/api/search",
        json={"query": "Where should we eat in Lisbon?", "agentId": "agent-a"},
    )
    assert found.status_code == 200
    payload = found.json()
    assert payload["moss"]["mode"] == "mock"
    assert payload["moss"]["call"].startswith("keyword overlap")
    assert "MossClient" not in payload["moss"]["call"] or "not MossClient" in payload["moss"]["call"]
    assert payload["moss"]["latencyMs"] >= 0
    assert payload["hits"][0]["id"] == "lisbon-dinner"
    assert payload["episode"]["agentId"] == "agent-a"
    assert payload["episode"]["engramId"]
    assert payload["memory"]["agents"]["agent-a"]["engrams"] >= 1
    assert "not Moss" in payload["episode"]["content"]


def test_handoff_activates_destination_brain(mock_client):
    mock_client.post(
        "/api/search",
        json={"query": "Lisbon dinner at Time Out Market", "agentId": "agent-a"},
    )
    handed = mock_client.post("/api/handoff", json={"from": "agent-a", "to": "agent-b"})
    assert handed.status_code == 200
    body = handed.json()
    assert body["handoff"]["empty"] is False
    assert body["handoff"]["written"] >= 1
    assert body["handoff"]["activated"]
    activated = body["handoff"]["activated"][0]
    assert activated["receivedBy"] == "agent-b"
    assert activated["originAgent"] == "agent-a"
    assert activated["provenance"]["sourceUri"].startswith("fluctlight://agent-a/engram/")
    assert body["memory"]["agents"]["agent-b"]["engrams"] >= 1

    again = mock_client.post(
        "/api/search",
        json={"query": "Sunday river ferry", "agentId": "agent-b"},
    )
    assert again.status_code == 200
    assert again.json()["moss"]["mode"] == "mock"
    assert again.json()["episode"]["agentId"] == "agent-b"


def test_same_agent_handoff_is_rejected(mock_client):
    response = mock_client.post("/api/handoff", json={"from": "agent-a", "to": "agent-a"})
    assert response.status_code == 400


def test_missing_keys_do_not_fake_moss(monkeypatch, tmp_path):
    monkeypatch.setenv("MOSS_PROJECT_ID", "")
    monkeypatch.setenv("MOSS_PROJECT_KEY", "")
    monkeypatch.delenv("DEMO_MOCK_MOSS", raising=False)
    monkeypatch.setenv("ROOMSEARCH_DATA", str(tmp_path))
    from server.main import app

    with TestClient(app) as client:
        status = client.get("/api/status")
        assert status.json()["moss"]["mode"] == "unconfigured"
        denied = client.post("/api/search", json={"query": "Lisbon", "agentId": "agent-a"})
        assert denied.status_code == 503
        assert denied.json()["error"] == "moss_unconfigured"
        assert os.getenv("DEMO_MOCK_MOSS") in (None, "")
