import { motion, useReducedMotion } from "framer-motion"
import { FileText } from "lucide-react"
import type { Hit } from "../types"

const TOPIC_INK: Record<string, string> = {
  Room: "#3D4F66",
  Food: "#8A5A2B",
  Transit: "#1F6F62",
  Budget: "#7A4560",
  Field: "#4E6232",
  Repo: "#53447A",
  Map: "#2A5278",
  Sprint: "#7A4632",
}

export function Sources({ hits, index }: { hits: Hit[]; index: string }) {
  const reduce = useReducedMotion()
  if (hits.length === 0) {
    return (
      <section className="sources">
        <div className="kicker-row">
          <FileText size={14} strokeWidth={1.75} aria-hidden="true" />
          <h2 className="kicker">Sources</h2>
        </div>
        <div className="empty-rail">No note in the room index scored against that question.</div>
      </section>
    )
  }

  return (
    <section className="sources">
      <div className="kicker-row">
        <FileText size={14} strokeWidth={1.75} aria-hidden="true" />
        <h2 className="kicker">Sources</h2>
      </div>
      <div className="grid">
        {hits.map((hit, indexInList) => {
          const color = TOPIC_INK[hit.topic] ?? "#3A3936"
          return (
            <motion.article
              className="source"
              key={hit.id}
              initial={reduce ? false : { opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.38, delay: reduce ? 0 : indexInList * 0.06, ease: [0.22, 1, 0.36, 1] }}
            >
              <header>
                <span className="badge" style={{ color, background: `${color}14` }}>
                  {hit.mark}
                </span>
                <span className="topic">{hit.topic}</span>
                <span className="score">{hit.score.toFixed(2)}</span>
              </header>
              <h3>{hit.title}</h3>
              <p className="snippet">{hit.snippet}</p>
              <footer>
                {hit.id} · {index}
              </footer>
            </motion.article>
          )
        })}
      </div>
    </section>
  )
}
