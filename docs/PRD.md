# RoomSearch — PRD

## Problem

Two people sharing a research room ask overlapping questions. Each question needs a fast semantic lookup over the same notes, and the next person needs to inherit what the previous person already found. A vector search alone forgets who asked. A memory store alone is the wrong index for the notes.

## Product

RoomSearch is one screen. The active agent searches a shared room. Moss answers from the notes and shows the query latency. FluctlightDB stores that turn on the agent's own brain. Switching agents activates the previous episodes and writes them onto the next brain, with provenance.

The room in this demo is a field week for an open-source trip atlas: Lisbon dinners, a Kyoto rail decision, a tile-cache note, a coastal hike cutoff. Twelve shared documents. No accounts, no second page.

## Agents

| Agent | Role | Brain |
| --- | --- | --- |
| Agent A | Cartographer | `data/brains/agent-a` |
| Agent B | Planner | `data/brains/agent-b` |

The active agent owns the turn. Both read the same Moss index. Neither brain is the search index.

## Retrieval vs memory

| | Moss | FluctlightDB |
| --- | --- | --- |
| Question | Which note matches this wording? | What did this agent already learn? |
| Call | `client.query` | `experience`, `activate`, `checkpoint` |
| When | Every search | After a search, and on A→B handoff |
| Shown as | Source cards + `Moss X.X ms` | Episodes and Activated rail |

Moss latency is wall-clock around `query()` after the index is loaded. The SDK's `time_taken_ms` is shown beside it when Moss returns it. A dev mock exists only when keys are missing and `DEMO_MOCK_MOSS=1`. The mock is labeled and does not say Moss.

## Success

A viewer can search, read the latency on the Moss step, see source cards, switch agents, and see the activated episodes carry the first agent's engram id.
