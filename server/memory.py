"""Durable agent memory.

FluctlightDB owns episodes. Moss is not used here.
Each agent has its own embedded brain. A handoff activates the source
brain, writes those episodes into the destination brain, then activates
the destination so the UI shows what that agent can recall.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AGENTS: dict[str, dict[str, str]] = {
    "agent-a": {"id": "agent-a", "name": "Agent A", "role": "Cartographer", "initial": "A"},
    "agent-b": {"id": "agent-b", "name": "Agent B", "role": "Planner", "initial": "B"},
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


class MemoryStore:
    def __init__(self, data_dir: Path) -> None:
        from fluctlightdb import connect_embedded

        self.data_dir = data_dir
        self.brains_dir = data_dir / "brains"
        self.brains_dir.mkdir(parents=True, exist_ok=True)
        self.journal_path = data_dir / "journal.json"
        self._lock = threading.Lock()
        self.brains = {
            agent_id: connect_embedded(str(self.brains_dir / agent_id))
            for agent_id in AGENTS
        }
        self.episodes: list[dict[str, Any]] = []
        self.last_handoff: dict[str, Any] | None = None
        self._load_journal()

    def _load_journal(self) -> None:
        if not self.journal_path.exists():
            return
        try:
            payload = json.loads(self.journal_path.read_text())
        except (OSError, json.JSONDecodeError):
            return
        self.episodes = list(payload.get("episodes") or [])
        self.last_handoff = payload.get("lastHandoff")

    def _save_journal(self) -> None:
        payload = {"episodes": self.episodes[-80:], "lastHandoff": self.last_handoff}
        self.journal_path.write_text(json.dumps(payload, indent=2))

    def record_search(
        self,
        agent_id: str,
        query: str,
        lead_title: str,
        mode: str,
    ) -> dict[str, Any]:
        agent = AGENTS[agent_id]
        engine = "Moss" if mode == "live" else "dev mock retrieval, not Moss"
        content = (
            f"{agent['name']} searched \u201c{query}\u201d with {engine}. "
            f"Closest note: {lead_title or 'none'}."
        )
        with self._lock:
            brain = self.brains[agent_id]
            brain.turn_begin()
            brain.wm_push(content, context="moss-search", salience=0.8)
            written = brain.experience(
                content,
                context="moss-search",
                salience=0.82,
                agent_id=agent_id,
                provenance_kind="tool_grounded",
                source_uri=f"roomsearch://{agent_id}/search",
                verified=True,
                confidence=0.9,
            )
            brain.turn_end(flush=True)
            brain.checkpoint()
            episode = _episode_from_write(
                written,
                agent_id=agent_id,
                content=content,
                context="moss-search",
                source_uri=f"roomsearch://{agent_id}/search",
                origin_agent=agent_id,
            )
            self.episodes.append(episode)
            self._save_journal()
            return episode

    def handoff(self, source_id: str, dest_id: str) -> dict[str, Any]:
        if source_id == dest_id:
            raise ValueError("Pick the other agent to hand off.")
        with self._lock:
            source_episodes = [ep for ep in self.episodes if ep["agentId"] == source_id]
            cue_parts = [ep["content"] for ep in source_episodes[-4:]]
            if not cue_parts:
                payload = {
                    "from": source_id,
                    "to": dest_id,
                    "at": _now(),
                    "cue": "",
                    "written": 0,
                    "activated": [],
                    "sourceRecalls": 0,
                    "hops": 0,
                    "empty": True,
                }
                self.last_handoff = payload
                self._save_journal()
                return payload

            seen: set[str] = set()
            source_recalls: list[dict[str, Any]] = []
            source_brain = self.brains[source_id]
            for cue in cue_parts:
                activated = source_brain.activate(cue[:500], agent_id=source_id, limit=4)
                for recall in activated.get("recalls") or []:
                    engram_id = str(recall.get("engram_id") or "")
                    if not engram_id or engram_id in seen:
                        continue
                    seen.add(engram_id)
                    source_recalls.append(recall)

            dest = self.brains[dest_id]
            dest.turn_begin()
            written = 0
            for recall in source_recalls:
                episode = recall.get("episode") or {}
                content = str(episode.get("content") or "").strip()
                if not content:
                    continue
                engram_id = str(recall.get("engram_id"))
                source_uri = f"fluctlight://{source_id}/engram/{engram_id}"
                activation = float(recall.get("activation") or 0.5)
                result = dest.experience(
                    content,
                    context=f"handoff-from-{source_id}",
                    salience=0.9,
                    agent_id=dest_id,
                    provenance_kind="tool_grounded",
                    source_uri=source_uri,
                    verified=bool(recall.get("verified")),
                    confidence=_clamp(activation / 5.0),
                )
                card = _episode_from_write(
                    result,
                    agent_id=dest_id,
                    content=content,
                    context=f"handoff-from-{source_id}",
                    source_uri=source_uri,
                    origin_agent=str((episode.get("agent_id") or source_id)),
                )
                self.episodes.append(card)
                written += 1
            if written:
                summary = f"Handoff from {AGENTS[source_id]['name']} to {AGENTS[dest_id]['name']}."
                dest.wm_push(summary, context="handoff", salience=0.7)
            dest.turn_end(flush=True)
            dest.checkpoint()
            source_brain.checkpoint()

            dest_seen: set[str] = set()
            dest_recalls: list[dict[str, Any]] = []
            hops = 0
            for cue in cue_parts:
                activated = dest.activate(cue[:500], agent_id=dest_id, limit=4)
                hops = max(hops, int(activated.get("hops") or 0))
                for recall in activated.get("recalls") or []:
                    engram_id = str(recall.get("engram_id") or "")
                    if not engram_id or engram_id in dest_seen:
                        continue
                    dest_seen.add(engram_id)
                    dest_recalls.append(_activated_card(recall, received_by=dest_id))

            payload = {
                "from": source_id,
                "to": dest_id,
                "at": _now(),
                "cue": cue_parts[-1][:180],
                "written": written,
                "activated": dest_recalls,
                "sourceRecalls": len(source_recalls),
                "hops": hops,
                "empty": written == 0,
            }
            self.last_handoff = payload
            self._save_journal()
            return payload

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            brains = {}
            for agent_id, brain in self.brains.items():
                status = brain.status()
                brains[agent_id] = {
                    **AGENTS[agent_id],
                    "path": f"data/brains/{agent_id}",
                    "engrams": int(status.get("engrams") or 0),
                    "synapses": int(status.get("synapses") or 0),
                }
            return {
                "agents": brains,
                "episodes": list(reversed(self.episodes[-40:])),
                "lastHandoff": self.last_handoff,
            }


def _episode_from_write(
    written: dict[str, Any],
    *,
    agent_id: str,
    content: str,
    context: str,
    source_uri: str,
    origin_agent: str,
) -> dict[str, Any]:
    return {
        "engramId": str(written.get("engram_id") or ""),
        "agentId": agent_id,
        "originAgent": origin_agent,
        "content": content,
        "context": context,
        "createdAt": _now(),
        "gateRejected": bool(written.get("gate_rejected")),
        "provenance": {
            "kind": "tool_grounded",
            "sourceUri": source_uri,
            "verified": True,
        },
    }


def _origin_agent(source_uri: str, fallback: str) -> str:
    marker = "fluctlight://"
    if source_uri.startswith(marker):
        agent = source_uri[len(marker) :].split("/", 1)[0]
        if agent in AGENTS:
            return agent
    return fallback


def _activated_card(recall: dict[str, Any], *, received_by: str) -> dict[str, Any]:
    episode = recall.get("episode") or {}
    provenance = episode.get("provenance") or {}
    source_uri = str(provenance.get("source_uri") or "")
    holder = str(episode.get("agent_id") or received_by)
    return {
        "engramId": str(recall.get("engram_id") or ""),
        "activation": float(recall.get("activation") or 0),
        "verified": bool(recall.get("verified")),
        "agentId": holder,
        "originAgent": _origin_agent(source_uri, holder),
        "receivedBy": received_by,
        "content": str(episode.get("content") or ""),
        "context": str(episode.get("context") or ""),
        "hops": None,
        "provenance": {
            "kind": str(provenance.get("kind") or "tool_grounded"),
            "sourceUri": str(provenance.get("source_uri") or ""),
            "verified": bool(provenance.get("verified")),
        },
    }
