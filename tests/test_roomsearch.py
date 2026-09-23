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


def test_prepare_note_keeps_seed_ids():
    from server.notes import prepare_note
    from server.seed import SEED_DOCS

    doc = prepare_note("Northline room charter", "A private addendum about the ferry queue.", "Room")
    assert doc["id"].startswith("user-")
    assert doc["id"] not in {item["id"] for item in SEED_DOCS}
    assert len(SEED_DOCS) == 12


def test_public_failure_strips_credentials(monkeypatch):
    monkeypatch.setenv("MOSS_PROJECT_KEY", "super-secret-key")
    monkeypatch.setenv("MOSS_PROJECT_ID", "proj-123")
    from server.retrieve import _public_failure

    message = _public_failure(
        RuntimeError("rejected proj-123 with super-secret-key"),
        fallback="Moss could not add that note to the room index.",
    )
    assert "super-secret-key" not in message
    assert "proj-123" not in message
    assert "[redacted]" in message


def test_added_note_is_searchable_and_seed_stays(mock_client):
    before = mock_client.get("/api/status")
    assert before.status_code == 200
    assert before.json()["moss"]["docCount"] == 12

    added = mock_client.post(
        "/api/notes",
        json={
            "title": "Porto bakery stop",
            "text": "The room voted for pastel de nata at Manteigaria on the way to the river.",
            "topic": "Food",
        },
    )
    assert added.status_code == 200
    body = added.json()
    assert body["id"].startswith("user-porto-bakery-stop-")
    assert body["title"] == "Porto bakery stop"
    assert body["topic"] == "Food"
    assert body["docCount"] == 13
    assert body["index"] == "roomsearch-notes"
    assert body["mode"] == "mock"

    status = mock_client.get("/api/status")
    assert status.json()["moss"]["docCount"] == 13

    found = mock_client.post(
        "/api/search",
        json={"query": "pastel de nata at Manteigaria", "agentId": "agent-a"},
    )
    assert found.status_code == 200
    payload = found.json()
    assert payload["hits"][0]["id"] == body["id"]
    assert payload["hits"][0]["topic"] == "Food"
    assert payload["moss"]["docCount"] == 13
    assert payload["moss"]["mode"] == "mock"
    assert payload["episode"]["agentId"] == "agent-a"
    assert payload["episode"]["engramId"]

    seeded = mock_client.post(
        "/api/search",
        json={"query": "Where should we eat in Lisbon?", "agentId": "agent-b"},
    )
    assert seeded.status_code == 200
    assert seeded.json()["hits"][0]["id"] == "lisbon-dinner"

    pasted = mock_client.post(
        "/api/notes",
        json={
            "text": "Sintra tram tip\nBuy tickets before the hill or the queue eats the afternoon.",
            "tags": "Transit",
        },
    )
    assert pasted.status_code == 200
    paste_body = pasted.json()
    assert paste_body["title"] == "Sintra tram tip"
    assert paste_body["topic"] == "Transit"
    assert paste_body["docCount"] == 14

    again = mock_client.post(
        "/api/search",
        json={"query": "Sintra tram tip", "agentId": "agent-b"},
    )
    assert again.json()["hits"][0]["id"] == paste_body["id"]

    handed = mock_client.post("/api/handoff", json={"from": "agent-a", "to": "agent-b"})
    assert handed.status_code == 200
    assert handed.json()["handoff"]["empty"] is False


def test_chat_retrieves_replies_and_handoff_activates(mock_client):
    spoken = mock_client.post(
        "/api/chat",
        json={"message": "Where should we eat in Lisbon?", "agentId": "agent-a"},
    )
    assert spoken.status_code == 200
    body = spoken.json()
    assert body["reply"].startswith("Agent A (Cartographer):")
    assert "Lisbon dinner shortlist" in body["reply"]
    assert body["hits"][0]["id"] == "lisbon-dinner"
    assert body["moss"]["mode"] == "mock"
    assert body["moss"]["latencyMs"] >= 0
    assert "MossClient" not in body["moss"]["call"] or "not MossClient" in body["moss"]["call"]
    assert body["episode"]["agentId"] == "agent-a"
    assert body["episode"]["context"] == "moss-chat"
    assert body["episode"]["provenance"]["sourceUri"] == "roomsearch://agent-a/chat"
    assert "not Moss" in body["episode"]["content"]
    assert body["memory"]["agents"]["agent-a"]["engrams"] >= 1

    handed = mock_client.post("/api/handoff", json={"from": "agent-a", "to": "agent-b"})
    assert handed.status_code == 200
    activated = handed.json()["handoff"]
    assert activated["empty"] is False
    assert activated["written"] >= 1
    assert activated["activated"][0]["receivedBy"] == "agent-b"
    assert activated["activated"][0]["originAgent"] == "agent-a"
    assert activated["activated"][0]["provenance"]["sourceUri"].startswith("fluctlight://agent-a/engram/")

    follow = mock_client.post(
        "/api/search",
        json={"query": "Sunday river ferry", "agentId": "agent-b"},
    )
    assert follow.status_code == 200
    assert follow.json()["moss"]["mode"] == "mock"
    assert follow.json()["hits"][0]["id"] == "sunday-ferry"


def test_empty_note_is_rejected(mock_client):
    response = mock_client.post("/api/notes", json={"title": "   ", "text": "  "})
    assert response.status_code == 400
    assert response.json()["error"] == "empty_note"
    assert mock_client.get("/api/status").json()["moss"]["docCount"] == 12


def test_long_note_is_rejected(mock_client):
    response = mock_client.post("/api/notes", json={"title": "Too big", "text": "a" * 8001})
    assert response.status_code == 400
    assert response.json()["error"] == "note_too_long"


def test_live_add_upserts_reloads_and_query_finds_it():
    import asyncio

    from server.notes import prepare_note
    from server.retrieve import INDEX_NAME, Retriever
    from server.seed import SEED_DOCS

    class Store:
        def __init__(self) -> None:
            self.docs: list = []
            self.loads: list = []

    store = Store()

    class Client:
        async def add_docs(self, name, docs, options):
            assert name == INDEX_NAME
            assert options.upsert is True
            store.docs.extend(docs)

        async def load_index(self, name, cache_path=None):
            store.loads.append(name)

        async def get_index(self, name):
            class Info:
                doc_count = 12 + len(store.docs)

            return Info()

        async def query(self, name, query, options):
            hit = store.docs[-1]

            class Doc:
                id = hit.id
                text = hit.text
                score = 0.88
                metadata = dict(hit.metadata)

            class Result:
                time_taken_ms = 4
                docs = [Doc()]

            return Result()

    async def run():
        retriever = Retriever(mode="live", ready=True, _client=Client())
        doc = prepare_note("Harbor lantern note", "The lantern stays in the harbor shed.", "Field")
        count = await retriever.add_note(doc)
        assert count == 13
        assert store.loads == [INDEX_NAME]
        assert store.docs[0].id == doc["id"]
        assert store.docs[0].id not in {item["id"] for item in SEED_DOCS}
        found = await retriever.search("harbor lantern shed")
        assert found.mode == "live"
        assert found.hits[0].id == doc["id"]
        assert found.hits[0].title == "Harbor lantern note"
        assert found.hits[0].topic == "Field"
        assert found.doc_count == 13
        assert found.call.startswith('client.query("roomsearch-notes"')

    asyncio.run(run())


def test_live_add_failure_keeps_the_count_and_hides_the_key(monkeypatch):
    import asyncio

    from server.notes import prepare_note
    from server.retrieve import RetrieveError, Retriever

    monkeypatch.setenv("MOSS_PROJECT_KEY", "super-secret-key")

    class Client:
        async def add_docs(self, name, docs, options):
            raise RuntimeError("upload rejected for super-secret-key")

        async def load_index(self, name, cache_path=None):
            raise AssertionError("index should stay loaded when the upsert fails")

    async def run():
        retriever = Retriever(mode="live", ready=True, doc_count=12, _client=Client())
        doc = prepare_note("Side door", "The side door code is taped under the planter.", "Room")
        with pytest.raises(RetrieveError) as caught:
            await retriever.add_note(doc)
        assert caught.value.status == 502
        assert "super-secret-key" not in caught.value.message
        assert retriever.doc_count == 12

    asyncio.run(run())


def test_notes_stay_off_without_moss_keys(monkeypatch, tmp_path):
    monkeypatch.setenv("MOSS_PROJECT_ID", "")
    monkeypatch.setenv("MOSS_PROJECT_KEY", "")
    monkeypatch.delenv("DEMO_MOCK_MOSS", raising=False)
    monkeypatch.setenv("ROOMSEARCH_DATA", str(tmp_path))
    from server.main import app

    with TestClient(app) as client:
        denied = client.post(
            "/api/notes",
            json={"title": "Side note", "text": "This must not pretend to be in Moss."},
        )
        assert denied.status_code == 503
        assert denied.json()["error"] == "moss_unconfigured"


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
