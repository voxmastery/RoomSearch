import { useEffect, useRef, useState } from "react"
import { ApiError, chatRoom, fetchStatus, handoff, searchRoom } from "./api"
import { ArrowLeftRight, ArrowRight, Compass, Route, Search } from "lucide-react"
import { AddNote } from "./components/AddNote"
import { ChatPanel, type ChatTurn } from "./components/ChatPanel"
import { Rail } from "./components/Rail"
import { MossPulse, RoomIllustration } from "./components/RoomArt"
import { Sources } from "./components/Sources"
import { Trace } from "./components/Trace"
import { AGENTS, SUGGESTIONS, type AgentId, type Handoff, type MemorySnapshot, type MossMode, type NoteResponse, type SearchResponse, type StatusResponse } from "./types"

const other = (id: AgentId): AgentId => (id === "agent-a" ? "agent-b" : "agent-a")

export default function App() {
  const [status, setStatus] = useState<StatusResponse | null>(null)
  const [offline, setOffline] = useState(false)
  const [agentId, setAgentId] = useState<AgentId>("agent-a")
  const [draft, setDraft] = useState("")
  const [chatDraft, setChatDraft] = useState("")
  const [asked, setAsked] = useState("")
  const [phase, setPhase] = useState<"idle" | "running" | "done" | "error">("idle")
  const [result, setResult] = useState<SearchResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [memory, setMemory] = useState<MemorySnapshot | null>(null)
  const [lastHandoff, setLastHandoff] = useState<Handoff | null>(null)
  const [handoffBusy, setHandoffBusy] = useState(false)
  const [fresh, setFresh] = useState(false)
  const [runKey, setRunKey] = useState(0)
  const [composerOpen, setComposerOpen] = useState(false)
  const [chatOpen, setChatOpen] = useState(false)
  const [chatBusy, setChatBusy] = useState(false)
  const [chatError, setChatError] = useState<string | null>(null)
  const [turns, setTurns] = useState<ChatTurn[]>([])
  const [toast, setToast] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const toastTimer = useRef(0)
  const turnSeq = useRef(0)

  useEffect(() => {
    let stop = false
    let timer = 0
    async function pull() {
      try {
        const next = await fetchStatus()
        if (stop) return
        setOffline(false)
        setStatus(next)
        setMemory((current) => current ?? next.memory)
        setLastHandoff((current) => current ?? next.memory.lastHandoff)
        if (next.moss.mode === "live" && !next.moss.ready) {
          timer = window.setTimeout(() => void pull(), 1500)
        }
      } catch {
        if (stop) return
        setOffline(true)
        timer = window.setTimeout(() => void pull(), 1500)
      }
    }
    void pull()
    return () => {
      stop = true
      window.clearTimeout(timer)
    }
  }, [])

  useEffect(() => () => window.clearTimeout(toastTimer.current), [])

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const tag = document.activeElement?.tagName
      if (event.key === "/" && tag !== "INPUT" && tag !== "TEXTAREA") {
        event.preventDefault()
        inputRef.current?.focus()
      }
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [])

  const mode: MossMode = status?.moss.mode ?? "unconfigured"
  const searchable = mode === "mock" || (mode === "live" && Boolean(status?.moss.ready))
  const agent = AGENTS[agentId]
  const next = AGENTS[other(agentId)]
  const idle = phase === "idle"
  const noteCount = status?.moss.docCount
  const lede =
    typeof noteCount === "number"
      ? `${noteCount} ${noteCount === 1 ? "note" : "notes"} in the room. One Moss index. Two Fluctlight brains.`
      : "Shared notes. One Moss index. Two Fluctlight brains."
  const composerBlocked = !searchable || phase === "running" || handoffBusy || offline || chatBusy
  const composerReason = composerBlocked ? composerBlockReason(mode, Boolean(status?.moss.ready), offline, phase === "running" || handoffBusy || chatBusy) : null

  function showToast(message: string) {
    setToast(message)
    window.clearTimeout(toastTimer.current)
    toastTimer.current = window.setTimeout(() => setToast(null), 4200)
  }

  function openComposer() {
    setComposerOpen(true)
    window.requestAnimationFrame(() => {
      document.getElementById("add-note")?.scrollIntoView({ behavior: "smooth", block: "nearest" })
    })
  }

  function openChat() {
    setChatOpen(true)
    window.requestAnimationFrame(() => {
      document.getElementById("ask-agent")?.scrollIntoView({ behavior: "smooth", block: "nearest" })
    })
  }

  async function onNoteAdded(note: NoteResponse) {
    setComposerOpen(false)
    showToast(`Added “${note.title}” · ${note.docCount} notes in the room`)
    try {
      const nextStatus = await fetchStatus()
      setOffline(false)
      setStatus(nextStatus)
      setMemory((current) => current ?? nextStatus.memory)
      setLastHandoff((current) => current ?? nextStatus.memory.lastHandoff)
    } catch {
      setStatus((current) =>
        current ? { ...current, moss: { ...current.moss, docCount: note.docCount } } : current,
      )
    }
    await runSearch(note.title)
  }

  async function runSearch(raw: string) {
    const query = raw.trim()
    if (!query || phase === "running" || !searchable) return
    setDraft(query)
    setAsked(query)
    setPhase("running")
    setError(null)
    setResult(null)
    setRunKey((value) => value + 1)
    try {
      const found = await searchRoom(query, agentId)
      setResult(found)
      setMemory(found.memory)
      setPhase("done")
    } catch (err) {
      setPhase("error")
      setError(err instanceof ApiError ? err.message : "The search did not finish.")
    }
  }

  async function runChat(raw: string) {
    const message = raw.trim()
    if (!message || chatBusy || phase === "running" || !searchable) return
    const speaker = agent
    setChatBusy(true)
    setChatError(null)
    setChatDraft("")
    try {
      const found = await chatRoom(message, speaker.id)
      turnSeq.current += 1
      setTurns((current) => [
        ...current,
        {
          id: turnSeq.current,
          agentId: speaker.id,
          agentName: speaker.name,
          agentRole: speaker.role,
          message,
          reply: found.reply ?? found.observation,
          latencyMs: found.moss.latencyMs,
          mode: found.moss.mode,
          sources: found.hits.map((hit) => hit.title),
        },
      ])
      setMemory(found.memory)
    } catch (err) {
      setChatDraft(message)
      setChatError(err instanceof ApiError ? err.message : "The reply did not finish.")
    } finally {
      setChatBusy(false)
    }
  }

  async function switchAgent(target: AgentId) {
    if (target === agentId || handoffBusy || phase === "running" || chatBusy) return
    setHandoffBusy(true)
    setError(null)
    try {
      const response = await handoff(agentId, target)
      setLastHandoff(response.handoff)
      setMemory(response.memory)
      setAgentId(target)
      setFresh(true)
      window.setTimeout(() => setFresh(false), 900)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "The handoff did not finish.")
    } finally {
      setHandoffBusy(false)
    }
  }

  const searchForm = (variant: "hero" | "compact") => (
    <form
      className={variant === "compact" ? "search compact" : "search"}
      onSubmit={(event) => {
        event.preventDefault()
        void runSearch(draft)
      }}
    >
      <Search className="lead-icon" size={18} strokeWidth={1.75} aria-hidden="true" />
      <input
        ref={variant === "hero" || !idle ? inputRef : undefined}
        value={draft}
        onChange={(event) => setDraft(event.target.value)}
        placeholder="Search the shared room"
        aria-label="Search the shared room"
        disabled={!searchable || phase === "running"}
        autoComplete="off"
      />
      <button className="go" type="submit" aria-label="Search" disabled={!searchable || phase === "running" || draft.trim().length === 0}>
        <ArrowRight size={18} strokeWidth={1.75} aria-hidden="true" />
      </button>
    </form>
  )

  const roomActions = (
    <div className="hero-cta">
      <button type="button" className="cta" aria-expanded={composerOpen} onClick={openComposer}>
        Add a note
      </button>
      <button type="button" className="cta ask" aria-expanded={chatOpen} onClick={openChat}>
        Ask the agent
      </button>
    </div>
  )

  const chatPanel = chatOpen ? (
    <ChatPanel
      agentName={agent.name}
      agentRole={agent.role}
      turns={turns}
      draft={chatDraft}
      busy={chatBusy}
      blocked={composerBlocked}
      blockedReason={composerReason}
      error={chatError}
      onDraft={setChatDraft}
      onSend={(message) => void runChat(message)}
      onClose={() => setChatOpen(false)}
    />
  ) : null

  return (
    <div className={`shell ${idle ? "is-idle" : "is-results"}`}>
      <header className="top">
        <div className="top-row">
          <div className="brand">
            <span className="mark" aria-hidden="true">R</span>
            <div>
              <h1>RoomSearch</h1>
              <p>Shared research room</p>
            </div>
          </div>
          <div className="agents">
            <div className="segment" role="group" aria-label="Active agent">
              {Object.values(AGENTS).map((item) => (
                <button
                  key={item.id}
                  type="button"
                  className={item.id === agentId ? "on" : ""}
                  onClick={() => void switchAgent(item.id)}
                  aria-pressed={item.id === agentId}
                >
                  <span className="initial" aria-hidden="true">
                    {item.id === "agent-a" ? (
                      <Compass size={14} strokeWidth={1.75} />
                    ) : (
                      <Route size={14} strokeWidth={1.75} />
                    )}
                  </span>
                  <span className="who">
                    <strong>{item.name}</strong>
                    <em>{item.role}</em>
                  </span>
                </button>
              ))}
            </div>
            <button className="switch" type="button" onClick={() => void switchAgent(other(agentId))} disabled={handoffBusy || phase === "running" || chatBusy}>
              <ArrowLeftRight size={14} strokeWidth={1.75} aria-hidden="true" />
              {handoffBusy ? "Activating…" : `Switch to ${next.name}`}
            </button>
            <ModeBadge mode={mode} ready={Boolean(status?.moss.ready)} offline={offline} />
          </div>
        </div>
        {idle ? null : <div className="top-search">{searchForm("compact")}</div>}
      </header>

      {idle ? (
        <section className="hero">
          <Banner mode={mode} ready={Boolean(status?.moss.ready)} error={status?.moss.error ?? null} offline={offline} />
          <RoomIllustration />
          <p className="eyebrow">Two agents, one room</p>
          <h2>Ask the shared room</h2>
          <p className="lede">{lede}</p>
          {searchForm("hero")}
          <div className="suggest">
            {SUGGESTIONS.map((prompt) => (
              <button key={prompt} type="button" disabled={!searchable} onClick={() => void runSearch(prompt)}>
                {prompt}
              </button>
            ))}
          </div>
          {roomActions}
          {composerOpen ? (
            <AddNote blocked={composerBlocked} blockedReason={composerReason} onAdded={onNoteAdded} onClose={() => setComposerOpen(false)} />
          ) : null}
          {chatPanel}
        </section>
      ) : (
        <main className="workspace">
          <div className="answer">
            <Banner mode={mode} ready={Boolean(status?.moss.ready)} error={status?.moss.error ?? null} offline={offline} />
            <h2 className="query">{asked}</h2>
            <p className="asking">
              {agent.name} · {agent.role}
            </p>
            {phase === "error" && error ? <div className="banner bad">{error}</div> : null}
            {phase === "running" || phase === "done" ? (
              <Trace key={runKey} phase={phase} mode={mode === "live" ? "live" : "mock"} agentName={agent.name} agentRole={agent.role} result={result} />
            ) : null}
            {roomActions}
            {composerOpen ? (
              <AddNote blocked={composerBlocked} blockedReason={composerReason} onAdded={onNoteAdded} onClose={() => setComposerOpen(false)} />
            ) : null}
            {chatPanel}
            {phase === "done" && result ? (
              <Sources hits={result.hits} index={result.moss.index} composerOpen={composerOpen} onAdd={openComposer} onAsk={openChat} />
            ) : null}
            {phase !== "error" && error ? <div className="banner bad">{error}</div> : null}
          </div>
          <Rail memory={memory} handoff={lastHandoff} fresh={fresh} />
        </main>
      )}
      {toast ? (
        <div className="toast" role="status">
          {toast}
        </div>
      ) : null}
    </div>
  )
}

function composerBlockReason(mode: MossMode, ready: boolean, offline: boolean, turnBusy: boolean): string {
  if (offline) return "The API is offline."
  if (mode === "unconfigured") return "Set Moss keys before adding a note."
  if (mode === "live" && !ready) return "Wait for the Moss index to finish warming."
  if (turnBusy) return "Wait for the current turn to finish."
  return "Notes stay off until Moss is ready."
}

function ModeBadge({ mode, ready, offline }: { mode: MossMode; ready: boolean; offline: boolean }) {
  if (offline) return <span className="mode">API offline</span>
  if (mode === "live" && ready) return <span className="mode live"><MossPulse />Moss live</span>
  if (mode === "live") return <span className="mode wait"><i />Warming</span>
  if (mode === "mock") return <span className="mode mock"><i />Mock</span>
  return <span className="mode">Moss off</span>
}

function Banner({ mode, ready, error, offline }: { mode: MossMode; ready: boolean; error: string | null; offline: boolean }) {
  if (offline) {
    return (
      <div className="banner bad">
        <strong>API offline.</strong> Start the Python server so search and handoff have somewhere to land.
      </div>
    )
  }
  if (mode === "mock") {
    return (
      <div className="banner mock">
        <strong>Dev mock retrieval.</strong> Hits are keyword overlap over the room notes, not Moss. Unset DEMO_MOCK_MOSS and add portal keys to film a real query.
      </div>
    )
  }
  if (mode === "live" && !ready) {
    return (
      <div className="banner">
        <strong>Warming the Moss index.</strong> {error ?? "The first load builds roomsearch-notes and downloads the embedding model."}
      </div>
    )
  }
  if (mode === "unconfigured") {
    return (
      <div className="banner">
        <strong>Set Moss keys.</strong> Export MOSS_PROJECT_ID and MOSS_PROJECT_KEY, then restart the API. Searches stay off so a missing key is never shown as Moss.
      </div>
    )
  }
  if (mode === "live" && error) {
    return (
      <div className="banner bad">
        <strong>Moss failed.</strong> {error}
      </div>
    )
  }
  return null
}
