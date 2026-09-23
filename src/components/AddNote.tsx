import { FileUp, X } from "lucide-react"
import { useEffect, useId, useRef, useState, type FormEvent } from "react"
import { addNote, ApiError } from "../api"
import type { NoteResponse } from "../types"

type Mode = "fields" | "paste"

const TEXT_LIMIT = 8_000

export function AddNote({
  blocked,
  blockedReason,
  onAdded,
  onClose,
}: {
  blocked: boolean
  blockedReason: string | null
  onAdded: (note: NoteResponse) => void | Promise<void>
  onClose: () => void
}) {
  const titleId = useId()
  const textId = useId()
  const topicId = useId()
  const [mode, setMode] = useState<Mode>("fields")
  const [title, setTitle] = useState("")
  const [text, setText] = useState("")
  const [topic, setTopic] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const titleRef = useRef<HTMLInputElement>(null)
  const pasteRef = useRef<HTMLTextAreaElement>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (mode === "fields") titleRef.current?.focus()
    else pasteRef.current?.focus()
  }, [mode])

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose()
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [onClose])

  async function onFile(file: File | undefined) {
    if (!file) return
    const name = file.name.toLowerCase()
    if (name.endsWith(".pdf") || file.type === "application/pdf") {
      setError("PDF files are not accepted. Upload a .txt or .md file.")
      return
    }
    const allowed = name.endsWith(".txt") || name.endsWith(".md") || name.endsWith(".markdown")
    if (!allowed) {
      setError("Upload a .txt or .md file.")
      return
    }
    if (file.size > 200_000) {
      setError("That file is too large. Keep the note under 8,000 characters.")
      return
    }
    const raw = (await file.text()).replace(/^\uFEFF/, "")
    if (raw.includes("\u0000")) {
      setError("Upload a .txt or .md file.")
      return
    }
    if (raw.trim().length > TEXT_LIMIT) {
      setError("Keep the note under 8,000 characters.")
      return
    }
    setText(raw)
    if (mode === "fields" && title.trim().length === 0) {
      const base = file.name.replace(/\.(txt|md|markdown)$/i, "").replace(/[-_]+/g, " ").trim()
      if (base) setTitle(base)
    }
    setError(null)
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    if (busy || blocked) return
    const body = text.trim()
    const label = title.trim()
    if (mode === "fields" && label.length === 0) {
      setError("Add a title, or switch to paste.")
      return
    }
    if (body.length === 0) {
      setError(mode === "paste" ? "Paste the note text." : "Add the note text.")
      return
    }
    if (body.length > TEXT_LIMIT) {
      setError("Keep the note under 8,000 characters.")
      return
    }
    setBusy(true)
    setError(null)
    try {
      const added = await addNote({
        title: mode === "paste" ? "" : label,
        text: body,
        topic: topic.trim(),
      })
      await onAdded(added)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "The note could not be added.")
      setBusy(false)
    }
  }

  return (
    <section className="composer" id="add-note" aria-label="Add a note">
      <form className="composer-card" onSubmit={(event) => void onSubmit(event)}>
        <div className="composer-head">
          <div>
            <h3>Add a note to the room</h3>
            <p>Joins the same Moss index as the field notes.</p>
          </div>
          <button type="button" className="icon-btn" onClick={onClose} aria-label="Close add note">
            <X size={16} strokeWidth={1.75} aria-hidden="true" />
          </button>
        </div>

        <div className="mode-pills" role="group" aria-label="Note format">
          <button type="button" className={mode === "fields" ? "on" : ""} aria-pressed={mode === "fields"} onClick={() => setMode("fields")}>
            Title and body
          </button>
          <button type="button" className={mode === "paste" ? "on" : ""} aria-pressed={mode === "paste"} onClick={() => setMode("paste")}>
            Paste plain text
          </button>
        </div>

        {mode === "fields" ? (
          <label className="field" htmlFor={titleId}>
            <span>Title</span>
            <input
              ref={titleRef}
              id={titleId}
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Saturday ferry change"
              maxLength={140}
              autoComplete="off"
            />
          </label>
        ) : null}

        <label className="field" htmlFor={textId}>
          <span>{mode === "paste" ? "Note" : "Body"}</span>
          <textarea
            ref={mode === "paste" ? pasteRef : undefined}
            id={textId}
            value={text}
            onChange={(event) => setText(event.target.value)}
            placeholder={
              mode === "paste"
                ? "Paste a note. The first line is the title."
                : "What should the next person in the room know?"
            }
            rows={5}
            maxLength={TEXT_LIMIT}
          />
        </label>

        <label className="field" htmlFor={topicId}>
          <span>Category</span>
          <input
            id={topicId}
            value={topic}
            onChange={(event) => setTopic(event.target.value)}
            placeholder="Optional tag, such as Transit"
            maxLength={80}
            autoComplete="off"
          />
        </label>

        {error ? (
          <p className="composer-error" role="alert">
            {error}
          </p>
        ) : null}
        {blocked && blockedReason ? <p className="composer-hint">{blockedReason}</p> : null}

        <div className="composer-actions">
          <button type="button" className="upload" onClick={() => fileRef.current?.click()} disabled={busy}>
            <FileUp size={15} strokeWidth={1.75} aria-hidden="true" />
            Upload .txt or .md
          </button>
          <input
            ref={fileRef}
            className="file-input"
            type="file"
            accept=".txt,.md,.markdown,text/plain,text/markdown"
            aria-label="Upload a text or markdown note"
            onChange={(event) => {
              const file = event.target.files?.[0]
              event.target.value = ""
              void onFile(file)
            }}
          />
          <button className="add-submit" type="submit" disabled={busy || blocked || text.trim().length === 0}>
            {busy ? "Adding…" : "Add to room"}
          </button>
        </div>
      </form>
    </section>
  )
}
