"""Static mock data only — no logic."""

from __future__ import annotations


MOCK_CHILD = {
    "name": "Lin Mei",
    "age_week": 47,
    "gender": "Girl",
    "branch": "Scholar | Logic track",
    "temperament": "Curious, cautious",
}

# Big Five + resilience, independence, risk-taking (placeholder values).
MOCK_TRAITS_ORDER: list[tuple[str, int]] = [
    ("Openness", 72),
    ("Conscientiousness", 45),
    ("Extraversion", 33),
    ("Agreeableness", 61),
    ("Neuroticism", 40),
    ("Resilience", 67),
    ("Independence", 52),
    ("Risk-taking", 38),
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
    ("Save", "Placeholder persistence"),
    ("Resume", "Placeholder load"),
    ("Branch", "Placeholder branch actions"),
    ("Next week (calm)", "Uneventful mock week"),
    ("Noisy demo week", "Random multi-bump mock week"),
    ("View Branch Tree", "ASCII tree window"),
    ("Options", "Placeholder settings"),
]

MOCK_DELTAS: dict[tuple[int, str], dict[str, int]] = {
    (1, "A"): {"Extraversion": 4, "Independence": 3, "Openness": 2},
    (1, "B"): {"Conscientiousness": 3, "Resilience": 3, "Agreeableness": 1},
    (1, "C"): {"Conscientiousness": 4, "Extraversion": 2},
    (2, "A"): {"Openness": 4, "Agreeableness": 3, "Independence": 2},
    (2, "B"): {"Conscientiousness": 4, "Resilience": 3},
    (2, "C"): {"Conscientiousness": 3, "Openness": 2},
    (3, "A"): {"Agreeableness": 4, "Resilience": 3},
    (3, "B"): {"Conscientiousness": 4, "Resilience": 2},
    (3, "C"): {"Resilience": 4, "Conscientiousness": 3},
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
