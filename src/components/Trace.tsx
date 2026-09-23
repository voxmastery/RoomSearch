import { AnimatePresence, motion, useReducedMotion } from "framer-motion"
import { ChevronDown } from "lucide-react"
import { useEffect, useState, type ReactNode } from "react"
import type { MossMode, SearchResponse } from "../types"

type TraceProps = {
  phase: "running" | "done"
  mode: MossMode
  agentName: string
  agentRole: string
  result: SearchResponse | null
}

function ms(value: number): string {
  return `${value.toFixed(1)} ms`
}

export function Trace({ phase, mode, agentName, agentRole, result }: TraceProps) {
  const live = (result?.moss.mode ?? mode) === "live"
  const [open, setOpen] = useState<Record<string, boolean>>({ search: true })
  const toggle = (id: string) => setOpen((current) => ({ ...current, [id]: !current[id] }))

  useEffect(() => {
    if (phase === "done") setOpen((current) => ({ ...current, observe: true }))
  }, [phase])

  const searchTitle = live ? "Moss query" : "Mock retrieval"
  const pill =
    phase === "running"
      ? live
        ? "Moss"
        : "Mock"
      : phase === "done" && result
        ? live
          ? `Moss · ${ms(result.moss.latencyMs)}`
          : `Mock · ${ms(result.moss.latencyMs)}`
        : null

  return (
    <section className="trace" aria-label="Thinking">
      <Step
        n={1}
        id="frame"
        title="Framing the question"
        open={Boolean(open.frame)}
        onToggle={() => toggle("frame")}
        done
      >
        {agentName} is asking the shared room as {agentRole}. The notes stay in one Moss index.
        Memory of this turn is written to that agent&apos;s Fluctlight brain, not into the index.
      </Step>
      <Step
        n={2}
        id="search"
        title={searchTitle}
        className={live ? "tone-moss" : "tone-mock"}
        open={Boolean(open.search)}
        onToggle={() => toggle("search")}
        done={phase === "done"}
        waiting={phase === "running"}
        pill={pill}
        pillTone={live ? "moss" : "mock"}
        pending={phase === "running"}
      >
        {phase === "running" || !result ? (
          live
            ? "Calling Moss client.query and measuring wall-clock around that call."
            : "Running keyword overlap on the room notes. This is not a Moss query."
        ) : (
          <dl className="metrics">
            <dt>call</dt>
            <dd>{result.moss.call}</dd>
            <dt>index</dt>
            <dd>
              {result.moss.index} · {result.moss.docCount} notes
            </dd>
            <dt>wall</dt>
            <dd>{ms(result.moss.latencyMs)} around query()</dd>
            <dt>engine</dt>
            <dd>{result.moss.engineMs == null ? "not called" : `${result.moss.engineMs} ms time_taken_ms`}</dd>
            <dt>mix</dt>
            <dd>
              hybrid α {result.moss.alpha} · top {result.moss.topK}
            </dd>
          </dl>
        )}
      </Step>
      <Step
        n={3}
        id="observe"
        title="Observation"
        open={Boolean(open.observe)}
        onToggle={() => toggle("observe")}
        done={phase === "done"}
        waiting={phase === "running"}
      >
        {phase === "done" && result ? result.observation : "Waiting on the retrieval step."}
      </Step>
    </section>
  )
}

function Step({
  n,
  id,
  title,
  className,
  open,
  onToggle,
  done,
  waiting,
  pill,
  pillTone,
  pending,
  children,
}: {
  n: number
  id: string
  title: string
  className?: string
  open: boolean
  onToggle: () => void
  done?: boolean
  waiting?: boolean
  pill?: string | null
  pillTone?: "moss" | "mock"
  pending?: boolean
  children: ReactNode
}) {
  const reduce = useReducedMotion()
  return (
    <article className={`step ${className ?? ""} ${done && !waiting ? "done" : ""}`.trim()}>
      <span className="num" aria-hidden="true">{n}</span>
      <div className="step-main">
        <button className="step-h" type="button" aria-expanded={open} aria-controls={`${id}-body`} onClick={onToggle}>
          <span className="step-title">{title}</span>
          <span className="step-aside">
            {pill ? (
              <motion.span
                className={`pill ${pillTone ?? "moss"} ${pending ? "pending" : ""}`}
                animate={pending && !reduce ? { opacity: [1, 0.45, 1] } : { opacity: 1 }}
                transition={pending && !reduce ? { duration: 1.15, repeat: Infinity, ease: "easeInOut" } : { duration: 0.2 }}
              >
                {pill}
              </motion.span>
            ) : null}
            <motion.span
              className="chev-wrap"
              aria-hidden="true"
              animate={{ rotate: open ? 180 : 0 }}
              transition={{ duration: reduce ? 0 : 0.18 }}
            >
              <ChevronDown size={16} strokeWidth={1.75} />
            </motion.span>
          </span>
        </button>
        <AnimatePresence initial={false}>
          {open ? (
            <motion.div
              className="step-body"
              id={`${id}-body`}
              initial={reduce ? false : { height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={reduce ? undefined : { height: 0, opacity: 0 }}
              transition={{ duration: reduce ? 0 : 0.22, ease: [0.22, 1, 0.36, 1] }}
            >
              <div className="step-body-inner">{children}</div>
            </motion.div>
          ) : null}
        </AnimatePresence>
      </div>
    </article>
  )
}
