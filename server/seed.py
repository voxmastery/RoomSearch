"""Shared-room notes seeded into the Moss index.

A field week for an open-source trip atlas: dinners, rail, maps, and the hike.
"""

from __future__ import annotations

SEED_DOCS: list[dict[str, str]] = [
    {
        "id": "charter",
        "title": "Northline room charter",
        "topic": "Room",
        "mark": "NL",
        "text": (
            "Northline is a shared research room for a four-person field week. "
            "The group is planning an open-source trip atlas, not a product launch. "
            "Agent notes stay in this room: lodging caps, map decisions, and who "
            "owns the next question. Decisions are written down so the next person "
            "can continue without replaying the conversation."
        ),
    },
    {
        "id": "lisbon-dinner",
        "title": "Lisbon dinner shortlist",
        "topic": "Food",
        "mark": "LD",
        "text": (
            "Lisbon dinner shortlist for Saturday night. First choice is Time Out "
            "Market for a shared table and many small plates. Second is Cervejaria "
            "Ramiro if the group wants seafood and can queue. After dinner, walk to "
            "the river and take the late ferry to Cacilhas for the view back at the "
            "city. Book nothing; both places are walk-in."
        ),
    },
    {
        "id": "sunday-ferry",
        "title": "Sunday river ferry",
        "topic": "Transit",
        "mark": "FY",
        "text": (
            "The Lisbon river ferry runs from Cais do Sodré toward Cacilhas through "
            "the evening. Sunday plan: late morning in Alfama, then the ferry as the "
            "bridge between lunch and the south-bank walk. Tickets are tap-on. The "
            "last useful boat for the group is 22:30 so nobody misses the Monday train."
        ),
    },
    {
        "id": "kyoto-rail",
        "title": "Kyoto rail pass decision",
        "topic": "Transit",
        "mark": "KR",
        "text": (
            "Kyoto and Nara loop is four days. A full JR Pass does not pay off for "
            "this itinerary. Use an IC card for city buses, the subway, and the "
            "Nara line. Buy one reserved seat on the return shinkansen only. "
            "The Fushimi Inari visit is a walk, not a rail day."
        ),
    },
    {
        "id": "budget",
        "title": "Shared field-week budget",
        "topic": "Budget",
        "mark": "BD",
        "text": (
            "Shared trip budget is 2400 total, split four ways. Lodging cap is 140 "
            "per night for the whole room, not per person. Museum tickets come from "
            "the shared pool. Meals are individual unless the room voted a group "
            "dinner. Keep the running tally in the budget note, not in chat."
        ),
    },
    {
        "id": "packing",
        "title": "Field week packing list",
        "topic": "Field",
        "mark": "PK",
        "text": (
            "Packing list for the field week: rain shell, light sweater, one pair "
            "of shoes that can walk cobbles, and a power bank. Download offline map "
            "packs before the flight. Leave the drone at home; the atlas uses phone "
            "photos and GPX tracks only."
        ),
    },
    {
        "id": "hike-weather",
        "title": "Coastal hike weather window",
        "topic": "Field",
        "mark": "HW",
        "text": (
            "Coastal hike is scheduled for Saturday morning. Wind cutoff is 25 knots "
            "at the headland. If the marine forecast is above that at 07:00, swap to "
            "the inland ridge path. Fog is acceptable. Heavy rain cancels the exposed "
            "cliff section and the group uses the bus back to town."
        ),
    },
    {
        "id": "atlas-contrib",
        "title": "Atlas contributor guide",
        "topic": "Repo",
        "mark": "AC",
        "text": (
            "The northline atlas repo accepts notes as Markdown plus a GPX file. "
            "Open a pull request per place, not one giant branch. Name images by "
            "place and date. Do not commit API tokens. Reviewers check that every "
            "pin has a source sentence and a coordinate."
        ),
    },
    {
        "id": "tile-cache",
        "title": "Tile cache architecture decision",
        "topic": "Map",
        "mark": "TC",
        "text": (
            "Architecture decision: cache map tiles in IndexedDB with a 14-day TTL. "
            "The atlas must pan while offline after a place has been opened once. "
            "Evict least-recently used tiles when the cache passes 400 megabytes. "
            "Vector labels stay in a separate store so a style change does not "
            "throw away imagery."
        ),
    },
    {
        "id": "map-ui",
        "title": "Map UI design review",
        "topic": "Map",
        "mark": "MU",
        "text": (
            "Design review for the atlas map. Place labels need more contrast on "
            "satellite imagery. Shared pins are colored by author, with a small "
            "initial, not a long name. The selected pin opens a side card with the "
            "source sentence. Avoid a floating toolbar; keep zoom and the layer "
            "toggle in the top right."
        ),
    },
    {
        "id": "sprint",
        "title": "Sprint goals meeting notes",
        "topic": "Sprint",
        "mark": "SG",
        "text": (
            "Sprint goals from Tuesday's room meeting: ship offline map packs, "
            "let two people drop shared pins on the same place, and write a handoff "
            "note before anyone leaves the room. Out of scope: accounts, payments, "
            "and native apps. Next review is Friday at 16:00."
        ),
    },
    {
        "id": "shared-pins",
        "title": "How shared pins work",
        "topic": "Room",
        "mark": "SP",
        "text": (
            "A shared pin belongs to the room, not to one person. The author initial "
            "is provenance. Anyone may append a sentence. Conflicting coordinates "
            "stay visible until the room picks one. Pins sync when a teammate opens "
            "the atlas; there is no live cursor."
        ),
    },
]

INDEX_NAME = "roomsearch-notes"
