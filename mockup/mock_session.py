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
    branch_history: list[str] = field(default_factory=list)

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


def _trim_branch_history(session: MockSession, *, max_items: int = 14) -> None:
    if len(session.branch_history) > max_items:
        session.branch_history[:] = session.branch_history[-max_items:]


def _apply_demo_calendar_flags(session: MockSession) -> None:
    """Unlocks tree nodes by mock calendar week count (placeholder, not real progression)."""
    w = session.auto_simulated_weeks
    if w >= 4:
        session.maker_highlight = True
    if w >= 7:
        session.debate_unlocked = True
    if w >= 10:
        session.athletics_tease = True


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
    deltas = dict(MOCK_DELTAS.get((event, r), {"Openness": 1}))
    apply_trait_deltas(session, deltas)

    if event == 1 and r == "A":
        if not session.debate_unlocked:
            session.branch_history.append(
                "[Decision] School-fair reaction → Debate side-branch unlocks (mock)."
            )
            _trim_branch_history(session)
        session.debate_unlocked = True
    if event == 2 and r == "B":
        if not session.maker_highlight:
            session.branch_history.append(
                "[Decision] Quiet weekend stance → Maker lab marked as focus (mock)."
            )
            _trim_branch_history(session)
        session.maker_highlight = True
    if event == 3 and r == "C":
        if not session.athletics_tease:
            session.branch_history.append(
                "[Decision] Recess coaching → Athletics teaser branch opens (mock)."
            )
            _trim_branch_history(session)
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

        prev_maker = session.maker_highlight
        prev_debate = session.debate_unlocked
        prev_ath = session.athletics_tease
        _apply_demo_calendar_flags(session)
        w = session.auto_simulated_weeks
        if session.maker_highlight and not prev_maker:
            session.branch_history.append(
                f"[Calendar] Week {w} threshold → Maker spotlight path (mock demo)."
            )
            _trim_branch_history(session)
        if session.debate_unlocked and not prev_debate:
            session.branch_history.append(
                f"[Calendar] Week {w} threshold → Debate branch unlock (mock demo)."
            )
            _trim_branch_history(session)
        if session.athletics_tease and not prev_ath:
            session.branch_history.append(
                f"[Calendar] Week {w} threshold → Athletics teaser (mock demo)."
            )
            _trim_branch_history(session)

    session.last_deltas = {k: v for k, v in batch_totals.items() if v}
    session.last_event = None
    session.last_reaction = None
    session.summary = (
        f"(Mock) Auto-simulated {n} week(s): random small bumps only, no real model. "
        "Branch lines below grow as pure demo thresholds (weeks 4 / 7 / 10)."
    )


def mock_uneventful_week(session: MockSession, *, rng: random.Random | None = None) -> None:
    """Advance one mock week with light random drift — stands in for uneventful routine weeks."""
    rgen = rng or random.Random()
    trait_names = [name for name, _ in MOCK_TRAITS_ORDER]
    session.trait_previous = dict(session.traits)
    session.auto_simulated_weeks += 1
    session.last_event = None
    session.last_reaction = None

    week_deltas: dict[str, int] = {}
    if rgen.random() < 0.88:
        t = rgen.choice(trait_names)
        week_deltas[t] = week_deltas.get(t, 0) + 1
    if rgen.random() < 0.28:
        t2 = rgen.choice(trait_names)
        week_deltas[t2] = week_deltas.get(t2, 0) + 1

    for t, d in week_deltas.items():
        session.traits[t] = _clamp(session.traits[t] + d)
        session.cumulative_gains[t] = session.cumulative_gains.get(t, 0) + max(0, d)

    session.last_deltas = dict(week_deltas)

    prev_maker = session.maker_highlight
    prev_debate = session.debate_unlocked
    prev_ath = session.athletics_tease
    _apply_demo_calendar_flags(session)
    w = session.auto_simulated_weeks
    if session.maker_highlight and not prev_maker:
        session.branch_history.append(
            f"[Calendar] Week {w} threshold → Maker spotlight path (mock demo)."
        )
        _trim_branch_history(session)
    if session.debate_unlocked and not prev_debate:
        session.branch_history.append(
            f"[Calendar] Week {w} threshold → Debate branch unlock (mock demo)."
        )
        _trim_branch_history(session)
    if session.athletics_tease and not prev_ath:
        session.branch_history.append(
            f"[Calendar] Week {w} threshold → Athletics teaser (mock demo)."
        )
        _trim_branch_history(session)

    session.summary = (
        "(Mock) Uneventful week: tiny ambient trait drift only — no scripted event."
    )


def build_summary(session: MockSession) -> str:
    ev = session.last_event
    r = session.last_reaction
    if ev is None or r is None:
        return session.summary if session.summary else MOCK_SUMMARY_BASE

    ev_bit = EVENT_SHORT.get(ev, "this week's moment")
    react = REACTION_BLURBS.get(r, "you responded in your own way")
    delta_bits = ""
    if session.last_deltas:
        delta_bits = (
            "Mock trait nudges: "
            + ", ".join(f"{k} {v:+d}" for k, v in sorted(session.last_deltas.items()))
            + ". "
        )
    focus = (
        "Caregiver note: the branch panel refreshes from placeholder flags only — "
        "not real progression logic."
    )
    return (
        f"This week you addressed situation {ev}. After {ev_bit}, {react}. "
        f"{delta_bits}"
        f"The weekly narrative updates here so you can see the GUI pipeline working. "
        f"{focus}"
    )
