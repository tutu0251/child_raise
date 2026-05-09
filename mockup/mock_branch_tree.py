"""Mock-specific ASCII branch tree (reference for real branching UI later)."""

from __future__ import annotations

from mockup.mock_session import MockSession, display_week


def build_branch_lines(session: MockSession) -> list[str]:
    wk = display_week(session)
    lines: list[str] = []
    if session.last_event is not None and session.last_reaction:
        lines.extend(
            [
                "  [Mock UI] Last interaction: "
                f"event {session.last_event}, reaction {session.last_reaction} "
                "(tree nodes below unlock from placeholder flags only).",
                "",
            ]
        )
    if session.branch_history:
        lines.extend(
            [
                "  --- Recent branch activity (mock log) ---",
            ]
        )
        for note in session.branch_history[-8:]:
            lines.append(f"    • {note}")
        lines.append("")
    lines.extend(
        [
            f"  Root: Childhood path  [calendar week ~{wk}]",
            "  |",
        ]
    )
    lines.extend(
        [
            "  +-- Early focus: Observation",
            "  |     |",
            "  |     +-- Scholar | Logic  <-- current",
            "  |     |     |",
        ]
    )

    if session.debate_unlocked:
        lines.extend(
            [
                "  |     |     +-- Debate club  (open) ---+",
                "  |     |     |                          |",
                "  |     |     |                          +-- Rhetoric circle (mock)",
                "  |     |     |                          +-- Peer panel prep (mock)",
            ]
        )
    else:
        lines.append("  |     |     +-- Debate club  (locked)")

    if session.maker_highlight:
        lines.extend(
            [
                "  |     |     |",
                "  |     |     +-- Maker lab (focus) -----+",
                "  |     |     |                          |",
                "  |     |     |                          +-- Workshop tier 2 (mock)",
                "  |     |     |                          +-- Tool literacy drill (mock)",
            ]
        )
    else:
        lines.append("  |     |     +-- Maker lab  (open)")

    lines.extend(
        [
            "  |     |",
            "  |     +-- Scholar | Arts (not taken)",
            "  |",
        ]
    )

    if session.athletics_tease:
        lines.extend(
            [
                "  +-- Alternate: Athletics ---+",
                "  |                          |",
                "  |                          +-- Playground reps (mock)",
                "  |                          +-- Coordination games (mock)",
            ]
        )
    else:
        lines.append("  +-- Alternate: Athletics (not taken)")

    return lines
