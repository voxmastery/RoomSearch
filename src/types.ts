export type AgentId = "agent-a" | "agent-b"

export type MossMode = "live" | "mock" | "unconfigured"

export type Hit = {
  id: string
  title: string
  snippet: string
  score: number
  topic: string
  mark: string
}

export type MossPayload = {
  mode: MossMode
  query: string
  index: string
  latencyMs: number
  engineMs: number | null
  topK: number
  alpha: number
  docCount: number
  call: string
}

export type Provenance = {
  kind: string
  sourceUri: string
  verified: boolean
}

export type Episode = {
  engramId: string
  agentId: string
  originAgent: string
  content: string
  context: string
  createdAt: string
  gateRejected: boolean
  provenance: Provenance
}

export type Activated = {
  engramId: string
  activation: number
  verified: boolean
  agentId: string
  originAgent: string
  receivedBy: string
  content: string
  context: string
  provenance: Provenance
}

export type Handoff = {
  from: AgentId
  to: AgentId
  at: string
  cue: string
  written: number
  activated: Activated[]
  sourceRecalls: number
  hops: number
  empty: boolean
}

export type AgentBrain = {
  id: AgentId
  name: string
  role: string
  initial: string
  path: string
  engrams: number
  synapses: number
}

export type MemorySnapshot = {
  agents: Record<AgentId, AgentBrain>
  episodes: Episode[]
  lastHandoff: Handoff | null
}

export type MossStatus = {
  mode: MossMode
  ready: boolean
  error: string | null
  index: string
  docCount: number
  topK: number
  alpha: number
}

export type StatusResponse = {
  moss: MossStatus
  memory: MemorySnapshot
}

export type SearchResponse = {
  query: string
  agentId: AgentId
  moss: MossPayload
  hits: Hit[]
  observation: string
  episode: Episode
  memory: MemorySnapshot
}

export type HandoffResponse = {
  handoff: Handoff
  memory: MemorySnapshot
}

export const AGENTS: Record<AgentId, { id: AgentId; name: string; role: string; initial: string }> = {
  "agent-a": { id: "agent-a", name: "Agent A", role: "Cartographer", initial: "A" },
  "agent-b": { id: "agent-b", name: "Agent B", role: "Planner", initial: "B" },
}

export const SUGGESTIONS = [
  "Where should we eat in Lisbon?",
  "Do we need a JR Pass for Kyoto?",
  "How does the tile cache work?",
  "What is the coastal hike wind cutoff?",
]
