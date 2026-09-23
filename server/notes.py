"""Shape a user note into a room document.

Ids are minted here so an added note cannot replace one of the twelve
seeded documents. The Moss project key is never read in this module.
"""

from __future__ import annotations

import re
import secrets

from server.seed import SEED_DOCS

MAX_TITLE = 140
MAX_TEXT = 8_000
MAX_TOPIC = 80

_SEED_IDS = {doc["id"] for doc in SEED_DOCS}
_SLUG = re.compile(r"[^a-z0-9]+")
_WORD = re.compile(r"[A-Za-z0-9]+")


class NoteError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def prepare_note(title: str, text: str, topic: str) -> dict[str, str]:
    """Return id, title, text, topic, and mark for one room note."""
    body = _clean(text)
    label = " ".join(_clean(title).split())
    category = " ".join(_clean(topic).split())

    if not body and not label:
        raise NoteError("empty_note", "Write a note, or paste text, before adding it to the room.")
    if not body:
        raise NoteError("empty_note", "Add the note text.")

    if not label:
        lines = [line.strip() for line in body.splitlines() if line.strip()]
        if not lines:
            raise NoteError("empty_note", "Add the note text.")
        label = " ".join(lines[0].split())[:MAX_TITLE].strip()
        rest = "\n".join(lines[1:]).strip()
        body = rest or lines[0].strip()

    if len(label) > MAX_TITLE:
        raise NoteError("note_too_long", "Keep the title under 140 characters.")
    if len(body) > MAX_TEXT:
        raise NoteError("note_too_long", "Keep the note under 8,000 characters.")
    if not label:
        raise NoteError("empty_note", "Add a title, or start the paste with one.")

    if not category:
        category = "Note"
    if len(category) > MAX_TOPIC:
        raise NoteError("note_too_long", "Keep the category under 80 characters.")

    note_id = _note_id(label)
    if note_id in _SEED_IDS or not note_id.startswith("user-"):
        raise NoteError("reserved_id", "Seeded notes stay as they are. New notes get their own ids.")

    return {
        "id": note_id,
        "title": label,
        "text": body,
        "topic": category,
        "mark": _mark(label),
    }


def indexed_text(title: str, text: str) -> str:
    """Match the seed path: the indexed string leads with the title."""
    if text.lower().startswith(title.lower()):
        return text
    return f"{title}. {text}"


def _clean(value: str) -> str:
    return value.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n").strip()


def _note_id(title: str) -> str:
    slug = _SLUG.sub("-", title.lower()).strip("-")[:40].strip("-") or "note"
    return f"user-{slug}-{secrets.token_hex(4)}"


def _mark(title: str) -> str:
    words = _WORD.findall(title)
    if len(words) >= 2:
        return (words[0][0] + words[1][0]).upper()
    if words and len(words[0]) >= 2:
        return words[0][:2].upper()
    if words:
        return (words[0][0] + "N").upper()
    return "NT"
