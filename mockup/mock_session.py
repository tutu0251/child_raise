"""Mock session state and placeholder rules (not real game logic)."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from mockup.mock_constants import (
    EVENT_SHORT,
    MOCK_CHILD,
    MOCK_DELTAS,
    MOCK_SUMMARY_BASE,
    MOCK_TRAITS_ORDER,
    REACTION_BLURBS,
)


@dataclass
class MockSession:
    traits: dict[str, int]
    summary: str = ""
    debate_unlocked: bool = False
    maker_highlight: bool = False
    athletics_tease: bool = False
    last_event: int | None = None
    last_reaction: str | None = None
    last_deltas: dict[str, int] = field(default_factory=dict)
    trait_previous: dict[str, int] | None = None
    cumulative_gains: dict[str, int] = field(default_factory=dict)
    auto_simulated_weeks: int = 0

    def __post_init__(self) -> None:
        if not self.summary:
            self.summary = MOCK_SUMMARY_BASE
        if not self.cumulative_gains:
            self.cumulative_gains = {name: 0 for name, _ in MOCK_TRAITS_ORDER}


def _clamp(v: int) -> int:
    return max(0, min(100, v))


def initial_traits() -> dict[str, int]:
    return {name: v for name, v in MOCK_TRAITS_ORDER}


def display_week(session: MockSession) -> int:
    return int(MOCK_CHILD["age_week"]) + session.auto_simulated_weeks


def apply_trait_deltas(session: MockSession, deltas: dict[str, int]) -> None:
    session.trait_previous = dict(session.traits)
    session.last_deltas = dict(deltas)
    for trait, d in deltas.items():
        if trait not in session.traits:
            continue
        session.traits[trait] = _clamp(session.traits[trait] + d)
        if d > 0:
            session.cumulative_gains[trait] = session.cumulative_gains.get(trait, 0) + d


def apply_mock_choice(session: MockSession, event: int, reaction: str) -> None:
    r = reaction.upper()
    session.last_event = event
    session.last_reaction = r
    deltas = dict(MOCK_DELTAS.get((event, r), {"Curiosity": 1}))
    apply_trait_deltas(session, deltas)

    if event == 1 and r == "A":
        session.debate_unlocked = True
    if event == 2 and r == "B":
        session.maker_highlight = True
    if event == 3 and r == "C":
        session.athletics_tease = True


def auto_simulate_weeks(session: MockSession, n: int, *, rng: random.Random | None = None) -> None:
    if n <= 0:
        return
    rgen = rng or random.Random()
    trait_names = [name for name, _ in MOCK_TRAITS_ORDER]
    session.trait_previous = dict(session.traits)
    batch_totals: dict[str, int] = {t: 0 for t in trait_names}

    for _ in range(n):
        session.auto_simulated_weeks += 1
        week_deltas: dict[str, int] = {}
        for __ in range(rgen.randint(2, 4)):
            t = rgen.choice(trait_names)
            week_deltas[t] = week_deltas.get(t, 0) + rgen.randint(1, 2)
        for t, d in week_deltas.items():
            session.traits[t] = _clamp(session.traits[t] + d)
            batch_totals[t] = batch_totals.get(t, 0) + d
            session.cumulative_gains[t] = session.cumulative_gains.get(t, 0) + max(0, d)

        w = session.auto_simulated_weeks
        if w >= 4:
            session.maker_highlight = True
        if w >= 7:
            session.debate_unlocked = True
        if w >= 10:
            session.athletics_tease = True

    session.last_deltas = {k: v for k, v in batch_totals.items() if v}
    session.last_event = None
    session.last_reaction = None
    session.summary = (
        f"(Mock) Auto-simulated {n} week(s): random small bumps only, no real model. "
        "Branch lines below grow as pure demo thresholds (weeks 4 / 7 / 10)."
    )


def build_summary(session: MockSession) -> str:
    ev = session.last_event
    r = session.last_reaction
    if ev is None or r is None:
        return session.summary if session.summary else MOCK_SUMMARY_BASE

    ev_bit = EVENT_SHORT.get(ev, "this week's moment")
    react = REACTION_BLURBS.get(r, "you responded in your own way")
    focus = (
        "Caregiver note: the path mock shifts slightly in the tree - "
        "still placeholder branches, not real progression."
    )
    return (
        f"Following {ev_bit}, {react}. "
        f"Mei's week reads a bit different on paper: traits nudged as a demo only. "
        f"{focus}"
    )
