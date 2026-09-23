import type { Hit } from "../types"

const TOPIC_COLOR: Record<string, string> = {
  Room: "#9ecbff",
  Food: "#f0c27a",
  Transit: "#8ed9c8",
  Budget: "#f0a8c8",
  Field: "#c5d4a4",
  Repo: "#cbb8ff",
  Map: "#9ad0ff",
  Sprint: "#f0b59a",
}

export function Sources({ hits, index }: { hits: Hit[]; index: string }) {
  if (hits.length === 0) {
    return (
      <section className="sources">
        <h2 className="kicker">Sources</h2>
        <div className="empty-rail">No note in the room index scored against that question.</div>
      </section>
    )
  }

  return (
    <section className="sources">
      <h2 className="kicker">Sources</h2>
      <div className="grid">
        {hits.map((hit) => {
          const color = TOPIC_COLOR[hit.topic] ?? "#d5d6dc"
          return (
            <article className="source" key={hit.id}>
              <header>
                <span className="badge" style={{ color, background: `${color}22` }}>
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
            </article>
          )
        })}
      </div>
    </section>
  )
}
