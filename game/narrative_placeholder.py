"""Lightweight weekly narrative copy driven by UI state (placeholder prose)."""

from __future__ import annotations


def _snippet(text: str, limit: int = 120) -> str:
    s = text.replace("\n", " ").strip()
    if len(s) <= limit:
        return s
    return s[: limit - 1] + "…"


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
) -> str:
    """Short neutral placeholder tied to events / trait drift / run progress."""
    parts: list[str] = [
        f"{child_name}, calendar week {calendar_week}: "
        f"about {simulated_years_approx:.1f}y along a {simulation_target_years}-year run (placeholder pacing)."
    ]
    if auto_uneventful_note:
        parts.append("An uneventful week advanced automatically (options).")

    if event_count == 0:
        parts.append("Fewer situations surfaced — routines dominated (placeholder).")
    elif event_count == 1:
        parts.append("One situation anchored the week emotionally (placeholder).")
    else:
        parts.append(f"{event_count} parallel threads kept the week lively (placeholder).")

    if reaction_lines_count == 0 and event_count > 0:
        parts.append("Reactions are still open — choices will reshape next week's blurb (placeholder).")
    elif reaction_lines_count > 0:
        parts.append(
            f"{reaction_lines_count} caregiver response(s) logged; see trait arrows vs Monday baseline (placeholder)."
        )

    if traits_week_start and traits_now:
        deltas = [
            int(traits_now[k]) - int(traits_week_start[k])
            for k in traits_week_start
            if k in traits_now
        ]
        if deltas:
            net = sum(deltas)
            if net >= 4:
                parts.append("Net temperament shift this week reads slightly upward (placeholder).")
            elif net <= -4:
                parts.append("Net temperament shift this week reads slightly tighter (placeholder).")
            else:
                parts.append("Net temperament stayed within a narrow band (placeholder).")

    if event_summaries:
        for i, raw in enumerate(event_summaries, start=1):
            snip = _snippet(str(raw), 120)
            if snip:
                parts.append(f"Event {i} snapshot: {snip} (placeholder).")

    tail = (last_reaction_summary or "").strip()
    if tail:
        parts.append(f"Latest log line: {tail} (placeholder).")

    return " ".join(parts)
