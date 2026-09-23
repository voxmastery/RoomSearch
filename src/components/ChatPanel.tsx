import { X } from "lucide-react"
import { useEffect, useRef } from "react"
import type { AgentId, MossMode } from "../types"

export type ChatTurn = {
  id: number
  agentId: AgentId
  agentName: string
  agentRole: string
  message: string
  reply: string
  latencyMs: number
  mode: MossMode
  sources: string[]
}

function pillLabel(turn: ChatTurn): string {
  const ms = `${turn.latencyMs.toFixed(1)} ms`
  return turn.mode === "live" ? `Moss · ${ms}` : `Mock · ${ms}`
}

export function ChatPanel({
  agentName,
  agentRole,
  turns,
  draft,
  busy,
  blocked,
  blockedReason,
  error,
  onDraft,
  onSend,
  onClose,
}: {
  agentName: string
  agentRole: string
  turns: ChatTurn[]
  draft: string
  busy: boolean
  blocked: boolean
  blockedReason: string | null
  error: string | null
  onDraft: (value: string) => void
  onSend: (message: string) => void
  onClose: () => void
}) {
  const inputRef = useRef<HTMLInputElement>(null)
  const threadRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  useEffect(() => {
    const node = threadRef.current
    if (node) node.scrollTop = node.scrollHeight
  }, [turns, busy])

  return (
    <section className="chat-panel" id="ask-agent" aria-label={`Chat with ${agentName}`}>
      <header className="chat-head">
        <div>
          <h3>
            {agentName} · {agentRole}
          </h3>
          <p>Moss retrieves the room, then {agentName} answers from those notes.</p>
        </div>
        <button type="button" className="icon-btn" onClick={onClose} aria-label="Close chat">
          <X size={16} strokeWidth={1.75} aria-hidden="true" />
        </button>
      </header>

      <div className="thread" ref={threadRef}>
        {turns.length === 0 && !busy ? (
          <p className="thread-empty">Ask about a dinner, a train, or a note you just added.</p>
        ) : null}
        {turns.map((turn) => (
          <article className="turn" key={turn.id}>
            <p className="you">{turn.message}</p>
            <p className="agent-line">
              <strong>
                {turn.agentName} · {turn.agentRole}
              </strong>
              {turn.reply}
            </p>
            <div className="turn-meta">
              <span className={`pill ${turn.mode === "live" ? "moss" : "mock"}`}>{pillLabel(turn)}</span>
              {turn.sources.length > 0 ? <span className="cites">{turn.sources.slice(0, 3).join(" · ")}</span> : null}
            </div>
          </article>
        ))}
        {busy ? <p className="thread-empty">Retrieving from the room…</p> : null}
      </div>

      {error ? (
        <p className="composer-error" role="alert">
          {error}
        </p>
      ) : null}
      {blocked && blockedReason ? <p className="composer-hint">{blockedReason}</p> : null}

      <form
        className="chat"
        onSubmit={(event) => {
          event.preventDefault()
          onSend(draft)
        }}
      >
        <input
          ref={inputRef}
          value={draft}
          onChange={(event) => onDraft(event.target.value)}
          placeholder={`Message ${agentName}`}
          aria-label={`Message ${agentName}`}
          disabled={blocked || busy}
          autoComplete="off"
        />
        <button type="submit" disabled={blocked || busy || draft.trim().length === 0}>
          {busy ? "Sending…" : "Send"}
        </button>
      </form>
    </section>
  )
}
