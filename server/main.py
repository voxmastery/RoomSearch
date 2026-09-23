"""RoomSearch API.

POST /api/search     — Moss query (or labeled mock) + Fluctlight experience
POST /api/chat       — Moss retrieve, agent reply, Fluctlight experience
POST /api/notes      — append a note to the same Moss index
POST /api/handoff    — Fluctlight activate on the source, write, activate on the destination
GET  /api/status     — Moss mode and both brains
"""

from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from server.memory import AGENTS, MemoryStore
from server.notes import NoteError, prepare_note
from server.retrieve import RetrieveError, Retriever
from server.seed import INDEX_NAME

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent


def _data_dir() -> Path:
    raw = os.getenv("ROOMSEARCH_DATA", "").strip()
    path = Path(raw) if raw else ROOT / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path


class SearchBody(BaseModel):
    query: str = Field(min_length=1, max_length=400)
    agentId: str


class ChatBody(BaseModel):
    message: str = Field(min_length=1, max_length=400)
    agentId: str


class HandoffBody(BaseModel):
    from_agent: str = Field(alias="from")
    to: str

    model_config = {"populate_by_name": True}


class NoteBody(BaseModel):
    title: str = Field(default="", max_length=200)
    text: str = Field(default="", max_length=12_000)
    topic: str = Field(default="", max_length=100)
    tags: str = Field(default="", max_length=100)


def _reply(agent_id: str, hits: list[dict]) -> str:
    agent = AGENTS[agent_id]
    who = f"{agent['name']} ({agent['role']})"
    if not hits:
        return f"{who}: Nothing in the room index matched that."
    lead = hits[0]
    text = f"{who}: {lead['title']}. {lead['snippet']}"
    also = [hit["title"] for hit in hits[1:3]]
    if also:
        text += f" Also in range: {', '.join(also)}."
    return text


def _observation(hits: list[dict]) -> str:
    if not hits:
        return "Nothing in the room index matched that question."
    lead = hits[0]["title"]
    also = [hit["title"] for hit in hits[1:3]]
    if also:
        return f"{lead} is the closest note. Also in range: {', '.join(also)}."
    return f"{lead} is the closest note in the room."


def _moss_keys_present() -> bool:
    return bool(os.getenv("MOSS_PROJECT_ID", "").strip() and os.getenv("MOSS_PROJECT_KEY", "").strip())


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.retriever = Retriever()
    app.state.memory = MemoryStore(_data_dir())
    # Live Moss boots (index upsert + model) can take a while. Listen first so a
    # host health check can pass, and let /api/status report ready when the index is loaded.
    boot = asyncio.create_task(app.state.retriever.start())
    if not _moss_keys_present():
        await boot
    app.state.moss_boot = boot
    try:
        yield
    finally:
        if not boot.done():
            boot.cancel()
            try:
                await boot
            except asyncio.CancelledError:
                pass
        await app.state.retriever.close()


app = FastAPI(title="RoomSearch", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RetrieveError)
async def retrieve_error(_request: Request, exc: RetrieveError) -> JSONResponse:
    return JSONResponse(status_code=exc.status, content={"error": exc.code, "message": exc.message})


def _check_agent(agent_id: str) -> None:
    if agent_id not in AGENTS:
        raise RetrieveError("unknown_agent", "Agent must be agent-a or agent-b.", 400)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"ok": "true", "service": "roomsearch"}


@app.get("/api/status")
def status(request: Request) -> dict:
    retriever: Retriever = request.app.state.retriever
    memory: MemoryStore = request.app.state.memory
    return {"moss": retriever.status(), "memory": memory.snapshot()}


@app.post("/api/search")
async def search(body: SearchBody, request: Request) -> dict:
    _check_agent(body.agentId)
    retriever: Retriever = request.app.state.retriever
    memory: MemoryStore = request.app.state.memory
    found = await retriever.search(body.query)
    lead = found.hits[0].title if found.hits else ""
    episode = memory.record_search(body.agentId, found.query, lead, found.mode)
    return _found_payload(found, body.agentId, memory, reply=None, episode=episode)


def _found_payload(found, agent_id: str, memory: MemoryStore, *, reply: str | None, episode: dict) -> dict:
    payload = found.as_dict()
    body = {
        "query": found.query,
        "agentId": agent_id,
        "moss": {key: payload[key] for key in payload if key != "hits"},
        "hits": payload["hits"],
        "observation": reply if reply is not None else _observation(payload["hits"]),
        "episode": episode,
        "memory": memory.snapshot(),
    }
    if reply is not None:
        body["reply"] = reply
        body["message"] = found.query
    return body


@app.post("/api/chat")
async def chat(body: ChatBody, request: Request) -> dict:
    _check_agent(body.agentId)
    retriever: Retriever = request.app.state.retriever
    memory: MemoryStore = request.app.state.memory
    found = await retriever.search(body.message)
    reply = _reply(body.agentId, found.as_dict()["hits"])
    episode = memory.record_chat(body.agentId, found.query, reply, found.mode)
    return _found_payload(found, body.agentId, memory, reply=reply, episode=episode)


@app.post("/api/notes")
async def create_note(body: NoteBody, request: Request) -> dict:
    topic = body.topic.strip() or body.tags.strip()
    try:
        doc = prepare_note(body.title, body.text, topic)
    except NoteError as exc:
        raise RetrieveError(exc.code, exc.message, 400) from exc
    retriever: Retriever = request.app.state.retriever
    count = await retriever.add_note(doc)
    return {
        "id": doc["id"],
        "title": doc["title"],
        "topic": doc["topic"],
        "docCount": count,
        "index": INDEX_NAME,
        "mode": retriever.mode,
    }


@app.post("/api/handoff")
def handoff(body: HandoffBody, request: Request) -> dict:
    _check_agent(body.from_agent)
    _check_agent(body.to)
    memory: MemoryStore = request.app.state.memory
    try:
        result = memory.handoff(body.from_agent, body.to)
    except ValueError as exc:
        raise RetrieveError("bad_handoff", str(exc), 400) from exc
    return {"handoff": result, "memory": memory.snapshot()}


DIST = ROOT / "dist"


@app.get("/")
def index() -> FileResponse:
    page = DIST / "index.html"
    if not page.is_file():
        raise HTTPException(status_code=404, detail="UI build is missing. Run npm run build.")
    return FileResponse(page)


@app.get("/{asset_path:path}")
def frontend(asset_path: str) -> FileResponse:
    if asset_path.startswith("api/") or asset_path == "api":
        raise HTTPException(status_code=404)
    root = DIST.resolve()
    candidate = (DIST / asset_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        raise HTTPException(status_code=404) from None
    if not candidate.is_file():
        page = DIST / "index.html"
        if page.is_file():
            return FileResponse(page)
        raise HTTPException(status_code=404)
    return FileResponse(candidate)
