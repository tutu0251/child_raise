"""Static mock data only — no logic."""

from __future__ import annotations


MOCK_CHILD = {
    "name": "Lin Mei",
    "age_week": 47,
    "gender": "Girl",
    "branch": "Scholar | Logic track",
    "temperament": "Curious, cautious",
}

MOCK_TRAITS_ORDER: list[tuple[str, int]] = [
    ("Curiosity", 72),
    ("Patience", 45),
    ("Empathy", 61),
    ("Discipline", 38),
    ("Creativity", 84),
    ("Confidence", 52),
    ("Social ease", 33),
    ("Resilience", 67),
]

MOCK_EVENTS = [
    "School fair: volunteered at the science booth (+confidence chatter).",
    "Rainy weekend: finished a puzzle book with a caretaker.",
    "Minor scrape at recess - cried briefly, accepted a band-aid.",
]

MOCK_SUMMARY_BASE = (
    'Mei asked more "why" questions than usual and stayed calmer when plans '
    "changed. She still hesitates before group games but joined once invited. "
    "Next week might lean into small social wins without pushing too hard."
)

MOCK_CONTROLS = [
    ("Save", "Persist mock session"),
    ("Resume", "Load last mock checkpoint"),
    ("Next Week", "Advance mock timeline"),
    ("Options", "Placeholder settings"),
]

MOCK_DELTAS: dict[tuple[int, str], dict[str, int]] = {
    (1, "A"): {"Confidence": 4, "Social ease": 3, "Curiosity": 2},
    (1, "B"): {"Patience": 3, "Resilience": 3, "Empathy": 1},
    (1, "C"): {"Discipline": 4, "Confidence": 2},
    (2, "A"): {"Creativity": 4, "Empathy": 3, "Curiosity": 2},
    (2, "B"): {"Patience": 4, "Resilience": 3},
    (2, "C"): {"Discipline": 3, "Creativity": 2},
    (3, "A"): {"Empathy": 4, "Resilience": 3},
    (3, "B"): {"Patience": 4, "Resilience": 2},
    (3, "C"): {"Resilience": 4, "Discipline": 3},
}

REACTION_BLURBS = {
    "A": "you praised effort and reflected together",
    "B": "you gave space and checked in later",
    "C": "you offered one concrete next step",
}

EVENT_SHORT = {
    1: "the school fair booth",
    2: "the quiet puzzle weekend",
    3: "the recess scrape",
}
