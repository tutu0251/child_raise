"""Lightweight weekly narrative copy driven by UI state (placeholder prose)."""

from __future__ import annotations

from collections import Counter

from game.template_data import DEFAULT_TRAIT_KEYS


def _snippet(text: str, limit: int = 120) -> str:
    s = text.replace("\n", " ").strip()
    if len(s) <= limit:
        return s
    return s[: limit - 1] + "…"


def _reaction_digest(reactions: list[dict] | None) -> str:
    if not reactions:
        return ""
    kinds: Counter[str] = Counter()
    for r in reactions:
        if isinstance(r, dict) and r.get("reaction"):
            kinds[str(r["reaction"])] += 1
    if not kinds:
        return ""
    parts = [f"{k}×{n}" for k, n in kinds.most_common(6)]
    return "Caregiver responses this week: " + ", ".join(parts) + "."


def _dominant_trait_shift(
    traits_now: dict[str, int],
    traits_week_start: dict[str, int] | None,
) -> tuple[str, int] | None:
    if not traits_week_start:
        return None
    best_k = ""
    best_abs = 0
    best_signed = 0
    for k in DEFAULT_TRAIT_KEYS:
        if k not in traits_now or k not in traits_week_start:
            continue
        delta = int(traits_now[k]) - int(traits_week_start[k])
        a = abs(delta)
        if a > best_abs:
            best_abs = a
            best_signed = delta
            best_k = k
    if best_abs == 0 or not best_k:
        return None
    return best_k, best_signed


def build_weekly_narrative_feedback(
    *,
    calendar_week: int,
    child_name: str,
    event_count: int,
    reaction_lines_count: int,
    traits_now: dict[str, int],
    traits_week_start: dict[str, int] | None,
    simulation_target_years: int,
    simulated_years_approx: float,
    auto_uneventful_note: bool = False,
    event_summaries: list[str] | None = None,
    last_reaction_summary: str | None = None,
    week_reactions: list[dict] | None = None,
) -> str:
    """Weekly summary: pacing, events, caregiver reactions, and dominant trait movement."""
    parts: list[str] = [
        f"{child_name}, calendar week {calendar_week}: "
        f"about {simulated_years_approx:.1f}y along a {simulation_target_years}-year run."
    ]
    if auto_uneventful_note:
        parts.append("An uneventful week advanced automatically (options).")

    if event_count == 0:
        parts.append("Fewer situations surfaced; routines dominated.")
    elif event_count == 1:
        parts.append("One situation anchored the week.")
    else:
        parts.append(f"{event_count} situations threaded through the week.")

    if event_summaries:
        for i, raw in enumerate(event_summaries, start=1):
            snip = _snippet(str(raw), 140)
            if snip:
                parts.append(f"Event {i}: {snip}")

    rx_line = _reaction_digest(week_reactions)
    if rx_line:
        parts.append(rx_line)
    elif reaction_lines_count == 0 and event_count > 0:
        parts.append("Reactions are still open; choices will reshape how the week reads.")
    elif reaction_lines_count > 0:
        parts.append(
            f"{reaction_lines_count} caregiver response(s) logged; compare trait arrows to Monday baseline."
        )

    dom = _dominant_trait_shift(traits_now, traits_week_start)
    if dom:
        k, signed = dom
        direction = "rose" if signed > 0 else "fell" if signed < 0 else "held"
        parts.append(f"Largest personality move: {k} {direction} by {abs(signed)} (vs week start).")

    if traits_week_start and traits_now:
        deltas = [
            int(traits_now[k]) - int(traits_week_start[k])
            for k in DEFAULT_TRAIT_KEYS
            if k in traits_now and k in traits_week_start
        ]
        if deltas:
            net = sum(deltas)
            if net >= 4:
                parts.append("Net Big-Five-style shift this week reads slightly upward overall.")
            elif net <= -4:
                parts.append("Net shift this week reads slightly tighter or more guarded overall.")
            else:
                parts.append("Net personality change stayed within a narrow band.")

    tail = (last_reaction_summary or "").strip()
    if tail:
        parts.append(f"Latest log line: {tail}")

    return " ".join(parts)
