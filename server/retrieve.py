"""Hot-path retrieval.

Moss `client.query` when project keys are set.
Keyword overlap only when `DEMO_MOCK_MOSS=1` and keys are missing.
The mock path never reports itself as Moss.
"""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass, field
from typing import Any

from server.seed import INDEX_NAME, SEED_DOCS

TOP_K = 5
ALPHA = 0.75
_TOKEN = re.compile(r"[a-z0-9]+")


class RetrieveError(Exception):
    def __init__(self, code: str, message: str, status: int) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


@dataclass
class Hit:
    id: str
    title: str
    snippet: str
    score: float
    topic: str
    mark: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "snippet": self.snippet,
            "score": round(self.score, 4),
            "topic": self.topic,
            "mark": self.mark,
        }


@dataclass
class RetrieveResult:
    mode: str
    query: str
    index: str
    latency_ms: float
    engine_ms: int | None
    top_k: int
    alpha: float
    hits: list[Hit]
    doc_count: int
    call: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "query": self.query,
            "index": self.index,
            "latencyMs": round(self.latency_ms, 2),
            "engineMs": self.engine_ms,
            "topK": self.top_k,
            "alpha": self.alpha,
            "docCount": self.doc_count,
            "call": self.call,
            "hits": [hit.as_dict() for hit in self.hits],
        }


def _snippet(title: str, text: str) -> str:
    body = text
    prefix = f"{title}. "
    if body.startswith(prefix):
        body = body[len(prefix) :]
    body = " ".join(body.split())
    if len(body) <= 220:
        return body
    cut = body[:217].rsplit(" ", 1)[0]
    return cut + "\u2026"


def _tokens(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def rank_seed(query: str, docs: list[dict[str, str]] | None = None, top_k: int = TOP_K) -> list[Hit]:
    """Lexical overlap over the seed notes. Used only by the labeled mock path."""
    corpus = docs if docs is not None else SEED_DOCS
    query_tokens = _tokens(query)
    if not query_tokens:
        return []
    query_set = set(query_tokens)
    phrase = query.strip().lower()
    scored: list[tuple[float, dict[str, str]]] = []
    for doc in corpus:
        hay = f"{doc['title']} {doc['text']}"
        tokens = set(_tokens(hay))
        overlap = sum(1 for token in query_set if token in tokens)
        if overlap == 0:
            continue
        coverage = overlap / len(query_set)
        phrase_bonus = 0.12 if phrase and phrase in hay.lower() else 0.0
        title_bonus = 0.08 if any(token in doc["title"].lower() for token in query_set) else 0.0
        score = min(0.99, coverage * 0.8 + phrase_bonus + title_bonus)
        scored.append((score, doc))
    scored.sort(key=lambda item: item[0], reverse=True)
    hits: list[Hit] = []
    for score, doc in scored[:top_k]:
        hits.append(
            Hit(
                id=doc["id"],
                title=doc["title"],
                snippet=_snippet(doc["title"], doc["text"]),
                score=score,
                topic=doc["topic"],
                mark=doc["mark"],
            )
        )
    return hits


def _seed_by_id() -> dict[str, dict[str, str]]:
    return {doc["id"]: doc for doc in SEED_DOCS}


@dataclass
class Retriever:
    mode: str = "unconfigured"
    ready: bool = False
    error: str | None = None
    doc_count: int = len(SEED_DOCS)
    _client: Any = field(default=None, repr=False)

    async def start(self) -> None:
        project_id = os.getenv("MOSS_PROJECT_ID", "").strip()
        project_key = os.getenv("MOSS_PROJECT_KEY", "").strip()
        if project_id and project_key:
            self.mode = "live"
            try:
                await self._boot_live(project_id, project_key)
                self.ready = True
                self.error = None
            except Exception as exc:  # noqa: BLE001 — surface the SDK error to the UI
                self.ready = False
                self.error = str(exc)
            return
        if os.getenv("DEMO_MOCK_MOSS", "").strip() == "1":
            self.mode = "mock"
            self.ready = True
            self.error = None
            return
        self.mode = "unconfigured"
        self.ready = False
        self.error = None

    async def close(self) -> None:
        client = self._client
        self._client = None
        if client is None:
            return
        close = getattr(client, "close", None)
        if close is None:
            return
        result = close()
        if hasattr(result, "__await__"):
            await result

    async def _boot_live(self, project_id: str, project_key: str) -> None:
        from moss import DocumentInfo, MossClient, MutationOptions

        client = MossClient(project_id, project_key)
        self._client = client
        documents = [
            DocumentInfo(
                id=doc["id"],
                text=f"{doc['title']}. {doc['text']}",
                metadata={
                    "title": doc["title"],
                    "topic": doc["topic"],
                    "mark": doc["mark"],
                },
            )
            for doc in SEED_DOCS
        ]
        names = {info.name for info in await client.list_indexes()}
        if INDEX_NAME in names:
            await client.add_docs(INDEX_NAME, documents, MutationOptions(upsert=True))
        else:
            await client.create_index(INDEX_NAME, documents, "moss-minilm")
        cache = os.getenv("MOSS_CACHE_PATH", "").strip() or None
        await client.load_index(INDEX_NAME, cache_path=cache)
        # Warm the in-process query path so the filmed search is not the cold embed.
        await client.query(INDEX_NAME, "lisbon dinner", _query_options())
        info = await client.get_index(INDEX_NAME)
        count = getattr(info, "doc_count", None)
        if isinstance(count, int) and count > 0:
            self.doc_count = count

    async def search(self, query: str) -> RetrieveResult:
        text = query.strip()
        if not text:
            raise RetrieveError("empty_query", "Enter a question for the room.", 400)
        if self.mode == "live":
            if not self.ready or self._client is None:
                detail = self.error or "The Moss index is still warming."
                raise RetrieveError("moss_not_ready", detail, 503)
            return await self._live_query(text)
        if self.mode == "mock":
            return self._mock_query(text)
        raise RetrieveError(
            "moss_unconfigured",
            "Set MOSS_PROJECT_ID and MOSS_PROJECT_KEY. Searches stay off until Moss is configured.",
            503,
        )

    def _mock_query(self, query: str) -> RetrieveResult:
        started = time.perf_counter()
        hits = rank_seed(query)
        latency_ms = (time.perf_counter() - started) * 1000
        return RetrieveResult(
            mode="mock",
            query=query,
            index=INDEX_NAME,
            latency_ms=latency_ms,
            engine_ms=None,
            top_k=TOP_K,
            alpha=ALPHA,
            hits=hits,
            doc_count=len(SEED_DOCS),
            call="keyword overlap over seed notes \u2014 not MossClient.query",
        )

    async def _live_query(self, query: str) -> RetrieveResult:
        started = time.perf_counter()
        result = await self._client.query(INDEX_NAME, query, _query_options())
        latency_ms = (time.perf_counter() - started) * 1000
        engine = getattr(result, "time_taken_ms", None)
        engine_ms = int(engine) if isinstance(engine, (int, float)) else None
        catalog = _seed_by_id()
        hits: list[Hit] = []
        for doc in result.docs:
            meta = dict(getattr(doc, "metadata", None) or {})
            known = catalog.get(doc.id)
            title = str(meta.get("title") or (known["title"] if known else doc.id))
            topic = str(meta.get("topic") or (known["topic"] if known else "Note"))
            mark = str(meta.get("mark") or (known["mark"] if known else title[:2].upper()))
            text = str(getattr(doc, "text", "") or "")
            hits.append(
                Hit(
                    id=str(doc.id),
                    title=title,
                    snippet=_snippet(title, text),
                    score=float(doc.score),
                    topic=topic,
                    mark=mark[:2].upper(),
                )
            )
        return RetrieveResult(
            mode="live",
            query=query,
            index=INDEX_NAME,
            latency_ms=latency_ms,
            engine_ms=engine_ms,
            top_k=TOP_K,
            alpha=ALPHA,
            hits=hits,
            doc_count=self.doc_count,
            call=f'client.query("{INDEX_NAME}", query, QueryOptions(top_k={TOP_K}, alpha={ALPHA}))',
        )

    def status(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "ready": self.ready,
            "error": self.error,
            "index": INDEX_NAME,
            "docCount": self.doc_count,
            "topK": TOP_K,
            "alpha": ALPHA,
        }


def _query_options() -> Any:
    from moss import QueryOptions

    return QueryOptions(top_k=TOP_K, alpha=ALPHA)
