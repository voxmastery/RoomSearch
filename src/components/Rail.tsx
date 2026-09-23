import { motion, useReducedMotion } from "framer-motion"
import type { Activated, AgentId, Episode, Handoff, MemorySnapshot } from "../types"
import { AGENTS } from "../types"
import { EpisodeSpark } from "./RoomArt"

function relativeTime(iso: string): string {
  const then = new Date(iso).getTime()
  if (!Number.isFinite(then)) return ""
  const delta = Date.now() - then
  if (delta < 20_000) return "just now"
  const minutes = Math.round(delta / 60_000)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.round(minutes / 60)
  if (hours < 36) return `${hours}h ago`
  return new Date(iso).toLocaleDateString()
}

function countLabel(count: number): string {
  return count === 1 ? "1 engram" : `${count} engrams`
}

function shortId(id: string): string {
  return id ? id.slice(0, 8) : "—"
}
