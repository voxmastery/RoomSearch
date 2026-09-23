# RoomSearch demo script

Film the browser at 1440×900 or wider, light UI, one take if you can. The shot that matters is the latency pill on the Moss step. Do that shot with real keys. `DEMO_MOCK_MOSS=1` is for rehearsal only — the pill will say `Mock`, and that must not be the Moss shot.

## Before you roll

```bash
export MOSS_PROJECT_ID="…"    # portal.usemoss.dev
export MOSS_PROJECT_KEY="…"
npm run dev
```

Open the app. The header badge must read **Moss live**, not Mock and not Moss off. If it says Warming, wait until the badge flips. The first boot builds `roomsearch-notes` and downloads the embedding model.

Have the Episodes rail in frame the whole time. Start on Agent A.

## Shots

1. **Cold open (4s).** Empty search, both chips, Agent A ringed. Say: "Shared room. Moss for the notes. Fluctlight for the handoff."
2. **Search (8s).** Type `Where should we eat in Lisbon?` and press Enter. The trace appears immediately. Leave the **Moss query** row expanded.
3. **Latency (5s).** Hold until the pill is readable: `Moss · 3.4 ms` (the number will differ). Say: "That is wall-clock around `client.query`, after the index is loaded. The row under it is the SDK `time_taken_ms`."
4. **Sources (4s).** Hover one card so the lift reads on camera. The dinner note should lead.
5. **Episode (4s).** Pan to the rail. The new card is Agent A, `tool_grounded`, `roomsearch://agent-a/search`, and a short engram id. Say: "The search hit Moss. The turn was written to A's brain."
6. **Handoff (6s).** Click **Switch to Agent B**. The chip ring moves. Activated cards animate in. Read the provenance line: `fluctlight://agent-a/engram/…`. Say: "B did not re-index the notes. Fluctlight activated A's episodes and committed them on B's brain."
7. **B still uses Moss (6s).** Search `Sunday river ferry`. A second `Moss · … ms` pill appears. Say: "The next question still hits Moss. Memory did not replace retrieval."
8. **End (3s).** Both brain paths and engram counts are at the bottom of the rail.

## If a key is missing

The banner says **Set Moss keys** and search is disabled. Do not flip on the mock for the recording you submit as Moss usage. Rehearse with:

```bash
DEMO_MOCK_MOSS=1 npm run dev
```

The banner and the pill both say mock.

## What not to claim

- The pill is not a hardcoded 3 ms.
- Fluctlight is not the search engine.
- The twelve notes are a trip-atlas research room, not a medical dataset.
