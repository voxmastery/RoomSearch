import type { AgentId, HandoffResponse, NoteResponse, SearchResponse, StatusResponse } from "./types"

export class ApiError extends Error {
  code: string

  constructor(code: string, message: string) {
    super(message)
    this.code = code
  }
}

async function read<T>(response: Response): Promise<T> {
  const text = await response.text()
  const body = text ? (JSON.parse(text) as T & { error?: string; message?: string }) : ({} as T)
  if (!response.ok) {
    const err = body as { error?: string; message?: string }
    throw new ApiError(err.error ?? "request_failed", err.message ?? `Request failed (${response.status})`)
  }
  return body
}

export function fetchStatus(): Promise<StatusResponse> {
  return fetch("/api/status").then((response) => read<StatusResponse>(response))
}

export function searchRoom(query: string, agentId: AgentId): Promise<SearchResponse> {
  return fetch("/api/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, agentId }),
  }).then((response) => read<SearchResponse>(response))
}

export function chatRoom(message: string, agentId: AgentId): Promise<SearchResponse> {
  return fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, agentId }),
  }).then((response) => read<SearchResponse>(response))
}

export function addNote(note: { title: string; text: string; topic: string }): Promise<NoteResponse> {
  return fetch("/api/notes", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(note),
  }).then((response) => read<NoteResponse>(response))
}

export function handoff(from: AgentId, to: AgentId): Promise<HandoffResponse> {
  return fetch("/api/handoff", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ from, to }),
  }).then((response) => read<HandoffResponse>(response))
}
