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

export function Rail({
  memory,
  handoff,
  fresh,
}: {
  memory: MemorySnapshot | null
  handoff: Handoff | null
  fresh: boolean
}) {
  const episodes = memory?.episodes ?? []
  const activated = handoff?.activated ?? []

  return (
    <aside className="rail" aria-label="Fluctlight memory">
      <p className="rail-name">
        <EpisodeSpark />
        Fluctlight
      </p>
      <section className="rail-block">
        <div className="rail-head">
          <h2 className="kicker">Episodes</h2>
          <span>{episodes.length}</span>
        </div>
        {episodes.length === 0 ? (
          <div className="empty-rail">Searches land here as Fluctlight episodes, with the agent and source attached.</div>
        ) : (
          episodes.slice(0, 8).map((episode) => <EpisodeCard key={`${episode.engramId}-${episode.createdAt}`} episode={episode} />)
        )}
      </section>

      <section className="rail-block">
        <div className="rail-head">
          <h2 className="kicker">Activated</h2>
          <span>{handoff ? `${handoff.hops} hop` : "handoff"}</span>
        </div>
        {!handoff ? (
          <div className="empty-rail">Switch agents to activate the previous brain and hand those episodes across.</div>
        ) : activated.length === 0 ? (
          <div className="empty-rail">Nothing to activate yet. Search once as the current agent, then switch.</div>
        ) : (
          activated.slice(0, 6).map((card, index) => (
            <ActivatedCard key={card.engramId || index} card={card} fresh={fresh} delay={index * 70} />
          ))
        )}
      </section>

      <p className="paths">
        FluctlightDB
        <br />
        {memory?.agents["agent-a"]?.path ?? "data/brains/agent-a"} · {countLabel(memory?.agents["agent-a"]?.engrams ?? 0)}
        <br />
        {memory?.agents["agent-b"]?.path ?? "data/brains/agent-b"} · {countLabel(memory?.agents["agent-b"]?.engrams ?? 0)}
      </p>
    </aside>
  )
}

function EpisodeCard({ episode }: { episode: Episode }) {
  const agent = AGENTS[episode.agentId as AgentId]
  return (
    <article className="episode">
      <div className="ep-top">
        <span className="avatar">{agent?.initial ?? "?"}</span>
        <strong>{agent?.name ?? episode.agentId}</strong>
        <time dateTime={episode.createdAt}>{relativeTime(episode.createdAt)}</time>
      </div>
      <p>{episode.content}</p>
      <div className="prov">
        {episode.provenance.kind} · engram {shortId(episode.engramId)}
        <br />
        {episode.provenance.sourceUri}
      </div>
    </article>
  )
}

function ActivatedCard({ card, fresh, delay }: { card: Activated; fresh: boolean; delay: number }) {
  const origin = AGENTS[card.originAgent as AgentId]
  const receiver = AGENTS[card.receivedBy as AgentId]
  const reduce = useReducedMotion()
  return (
    <motion.article
      className={`episode ${fresh ? "fresh" : ""}`}
      initial={fresh && !reduce ? { opacity: 0, y: 8 } : false}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay: reduce ? 0 : delay / 1000, ease: [0.22, 1, 0.36, 1] }}
    >
      <div className="ep-top">
        {fresh ? <EpisodeSpark /> : null}
        <span className="avatar">{receiver?.initial ?? "B"}</span>
        <strong>{receiver?.name ?? "Agent"}</strong>
        <time>handoff</time>
      </div>
      <p>{card.content}</p>
      <div className="prov">
        from {origin?.name ?? card.originAgent} · {card.provenance.kind}
        <br />
        {card.provenance.sourceUri || `engram ${shortId(card.engramId)}`}
      </div>
    </motion.article>
  )
}
