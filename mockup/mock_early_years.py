"""Placeholder batch summary of cumulative mock trait gains (early-years style)."""

from __future__ import annotations

from mockup.mock_constants import MOCK_TRAITS_ORDER
from mockup.mock_session import MockSession, display_week


def format_early_years_batch(session: MockSession) -> str:
    """Human-readable summary of personality changes since session start (mock only)."""
    names = [n for n, _ in MOCK_TRAITS_ORDER]
    gains = session.cumulative_gains
    total = sum(max(0, gains.get(n, 0)) for n in names)
    week = display_week(session)
    lines = [
        f"Mock snapshot — calendar week ~{week}, auto-advanced weeks: {session.auto_simulated_weeks}.",
        f"Total positive mock increments recorded: {total} (not a real growth model).",
        "",
    ]
    positive = [(n, gains.get(n, 0)) for n in names if gains.get(n, 0) > 0]
    positive.sort(key=lambda x: -x[1])
    if not positive:
        lines.append("No cumulative gains yet — react to an event or advance weeks.")
        return "\n".join(lines)

    lines.append("Largest cumulative lifts (demo):")
    for name, g in positive[:5]:
        lines.append(f"  • {name}: +{g} total")
    if len(positive) > 5:
        rest = sum(g for _, g in positive[5:])
        lines.append(f"  • Other traits combined: +{rest}")
    return "\n".join(lines)
