"""Measure RoomSearch's Moss hot path.

Wall-clock is taken around ``client.query`` only, the same interval the API
reports as ``latencyMs``. The index is loaded and one warmup query is discarded
before the sample.

Requires ``MOSS_PROJECT_ID`` and ``MOSS_PROJECT_KEY`` (``.env`` or the shell).
Prints percentiles only. Never prints credentials.
"""

from __future__ import annotations

import asyncio
import json
import os
import platform
import statistics
import sys
import time
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env")

from server.retrieve import ALPHA, TOP_K, _query_options  # noqa: E402
from server.seed import INDEX_NAME, SEED_DOCS  # noqa: E402

N_DEFAULT = 150
WARMUP_QUERY = "lisbon dinner"

QUERIES = [
    "Northline room charter",
    "What is this shared research room for?",
    "Lisbon dinner shortlist",
    "Where should we eat in Lisbon?",
    "Sunday river ferry",
    "When is the last useful Lisbon ferry?",
    "Kyoto rail pass decision",
    "Do we need a JR Pass for the Kyoto loop?",
    "Shared field-week budget",
    "What is the lodging cap per night?",
    "Field week packing list",
    "What should we pack before the flight?",
    "Coastal hike weather window",
    "What if the headland wind is above the cutoff?",
    "Atlas contributor guide",
    "How do we open a pull request for a place?",
    "Tile cache architecture decision",
    "Where are map tiles stored offline?",
    "Map UI design review",
    "How should shared pins look on the map?",
    "Sprint goals meeting notes",
    "What is in scope for this sprint?",
    "How shared pins work",
    "Who owns a shared pin in the room?",
]


def percentile(sorted_samples: list[float], pct: float) -> float:
    if not sorted_samples:
        raise ValueError("empty sample")
    if len(sorted_samples) == 1:
        return sorted_samples[0]
    rank = (len(sorted_samples) - 1) * (pct / 100.0)
    lo = int(rank)
    hi = min(lo + 1, len(sorted_samples) - 1)
    frac = rank - lo
    return sorted_samples[lo] * (1.0 - frac) + sorted_samples[hi] * frac


def _cpu_model() -> str:
    try:
        text = Path("/proc/cpuinfo").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return platform.processor() or "unknown"
    for line in text.splitlines():
        if line.lower().startswith("model name"):
            return line.split(":", 1)[1].strip()
    return platform.processor() or "unknown"


def _mem_gb() -> float | None:
    try:
        text = Path("/proc/meminfo").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    for line in text.splitlines():
        if line.startswith("MemTotal:"):
            kb = int(line.split()[1])
            return round(kb / 1024 / 1024, 1)
    return None


def _summarize(samples: list[float]) -> dict[str, float]:
    ordered = sorted(samples)
    under = sum(1 for value in samples if value < 10.0)
    return {
        "p50": round(percentile(ordered, 50), 2),
        "p95": round(percentile(ordered, 95), 2),
        "p99": round(percentile(ordered, 99), 2),
        "mean": round(statistics.fmean(samples), 2),
        "min": round(min(samples), 2),
        "max": round(max(samples), 2),
        "under10msPct": round(100.0 * under / len(samples), 1),
    }


async def _ensure_loaded(client) -> int:
    from moss import DocumentInfo, MutationOptions

    documents = [
        DocumentInfo(
            id=doc["id"],
            text=f"{doc['title']}. {doc['text']}",
            metadata={"title": doc["title"], "topic": doc["topic"], "mark": doc["mark"]},
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
    await client.query(INDEX_NAME, WARMUP_QUERY, _query_options())
    info = await client.get_index(INDEX_NAME)
    count = getattr(info, "doc_count", None)
    if isinstance(count, int) and count > 0:
        return count
    return len(SEED_DOCS)


async def main() -> int:
    project_id = os.getenv("MOSS_PROJECT_ID", "").strip()
    project_key = os.getenv("MOSS_PROJECT_KEY", "").strip()
    if not project_id or not project_key:
        print("Moss credentials are not set. Refusing to run a mock benchmark.", file=sys.stderr)
        return 2

    n = int(os.getenv("BENCH_N", str(N_DEFAULT)))
    if n < 50:
        print("BENCH_N must be at least 50.", file=sys.stderr)
        return 2

    from moss import MossClient

    client = MossClient(project_id, project_key)
    try:
        doc_count = await _ensure_loaded(client)
        wall: list[float] = []
        engine: list[float] = []
        for i in range(n):
            query = QUERIES[i % len(QUERIES)]
            started = time.perf_counter()
            result = await client.query(INDEX_NAME, query, _query_options())
            wall.append((time.perf_counter() - started) * 1000)
            taken = getattr(result, "time_taken_ms", None)
            if isinstance(taken, (int, float)):
                engine.append(float(taken))
    finally:
        close = getattr(client, "close", None)
        if close is not None:
            result = close()
            if hasattr(result, "__await__"):
                await result

    wall_summary = _summarize(wall)
    payload = {
        "measuredOn": date.today().isoformat(),
        "index": INDEX_NAME,
        "model": "moss-minilm",
        "docCount": doc_count,
        "seedDocCount": len(SEED_DOCS),
        "topK": TOP_K,
        "alpha": ALPHA,
        "n": n,
        "querySet": len(QUERIES),
        "warmupDiscarded": 1,
        "warmupQuery": WARMUP_QUERY,
        "call": f'client.query("{INDEX_NAME}", query, QueryOptions(top_k={TOP_K}, alpha={ALPHA}))',
        "clock": "time.perf_counter around client.query only",
        "hardware": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "cpu": _cpu_model(),
            "cpus": os.cpu_count(),
            "memGb": _mem_gb(),
        },
        "wallClockMs": wall_summary,
    }
    if engine:
        payload["engineMs"] = _summarize(engine)

    out = ROOT / "docs" / "benchmarks" / "roomsearch-moss.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(f"index={INDEX_NAME} docs={doc_count} n={n} top_k={TOP_K} alpha={ALPHA}")
    print(
        "wall-clock ms  "
        f"p50={wall_summary['p50']}  p95={wall_summary['p95']}  p99={wall_summary['p99']}  "
        f"mean={wall_summary['mean']}  min={wall_summary['min']}  max={wall_summary['max']}  "
        f"under10ms={wall_summary['under10msPct']}%"
    )
    if engine:
        engine_summary = payload["engineMs"]
        print(
            "engine ms      "
            f"p50={engine_summary['p50']}  p95={engine_summary['p95']}  p99={engine_summary['p99']}"
        )
    print(f"wrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
