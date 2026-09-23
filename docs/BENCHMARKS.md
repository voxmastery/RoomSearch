# Benchmarks

RoomSearch claims the **warmed in-process** Moss path: `load_index`, then wall-clock around `client.query`. That is the number on the latency pill and in `moss.latencyMs`.

The remote or unloaded path is not this claim. [Moss benchmarks](https://www.moss.dev/benchmarks) attribute cloud-database time to network (about 40–150 ms in-region, 150–400 ms cross-region) plus load balancing, auth, and serialization, and list traditional query latency as 50–300 ms+.

Figures below were read from the live benchmarks page on 2026-09-23 (`dateModified` 2026-09-23). The page does not publish a 100,000-document cell. The published Moss workload is a 1,000-query FAQ-style set.

## Moss published

Source: [moss.dev/benchmarks](https://www.moss.dev/benchmarks). Same 1,000-query FAQ-style workload, same embedding model, `top_k=5`, indexes warmed so cold start is excluded from p50. Moss ran locally in-process against a fully loaded index. Latency is end-to-end from query invocation to ranked results, including embedding inside the runtime.

| Engine | p50 | p95 | p99 |
| --- | ---: | ---: | ---: |
| Moss | 3.1 ms | 4.3 ms | 5.4 ms |
| ChromaDB | 351.8 ms | 423.5 ms | 538.5 ms |
| Pinecone | 432.6 ms | 732.1 ms | 934.2 ms |
| Qdrant | 597.6 ms | 682 ms | 771.4 ms |

Moss's own headline is 3.1 ms at p50, staying under 5.4 ms at p99, and under 10 ms for in-process semantic search after the index is loaded. Qdrant on that page is about 193× Moss at p50.

## RoomSearch measured

Measured 2026-09-23 with `python scripts/bench_moss.py`.

| | |
| --- | --- |
| Index | `roomsearch-notes` (`moss-minilm`) |
| Documents | 12 seed notes |
| Queries | 150, cycling 24 seed titles and paraphrases |
| Options | `QueryOptions(top_k=5, alpha=0.75)` |
| Clock | `time.perf_counter` around `client.query` only |
| Warmup | one discarded query, `lisbon dinner`, after `load_index` |
| Machine | Linux 6.12.94+ x86_64, Intel Xeon, 4 vCPU, 15.6 GB RAM |

| | p50 | p95 | p99 | mean | min | max | under 10 ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Wall-clock `client.query` | 4.01 ms | 5.63 ms | 5.86 ms | 3.88 ms | 2.32 ms | 5.88 ms | 100% |

Raw sample summary: [`docs/benchmarks/roomsearch-moss.json`](benchmarks/roomsearch-moss.json). No credentials are in that file.

A 12-document index is a smaller corpus than Moss's FAQ workload, so it should sit in the same sub-10 ms band. It does. Every sample was under 10 ms (max 5.88 ms). These percentiles are a little above the published FAQ table (3.1 / 4.3 / 5.4). They are the same hot path, not a claim that this index beat that workload.

The SDK also returns `time_taken_ms` as an integer millisecond (`engineMs` on the API). On this run that field was 0 or 1. The pill and this table use the wall-clock around `query()`, which matches what the UI films.

## How to verify

1. With keys set, the header reads **Moss live**. Search once. The pill reads `Moss · X.X ms`. That number is the same wall-clock.
2. `POST /api/search` returns `moss.latencyMs` for that call. `moss.mode` is `live` only when the project keys are set. `DEMO_MOCK_MOSS=1` without keys labels the pill **Mock** and must not be cited as this table.
3. Rerun the sample:

```bash
python scripts/bench_moss.py
```

`BENCH_N` defaults to 150 and must be at least 50. The script loads `.env` and refuses to run if `MOSS_PROJECT_ID` or `MOSS_PROJECT_KEY` is missing.
