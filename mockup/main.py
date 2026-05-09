"""Entry point for the UI mockup. Kept separate from game logic."""

from __future__ import annotations

from mockup.mock_console import render_full
from mockup.mock_session import (
    MockSession,
    apply_mock_choice,
    auto_simulate_weeks,
    build_summary,
    initial_traits,
)
from mockup.ui.console_views import render_star_separator


def prompt_event() -> int:
    while True:
        raw = input("Choose event (1-3): ").strip()
        if raw in ("1", "2", "3"):
            return int(raw)
        print("  Please enter 1, 2, or 3.")


def prompt_reaction() -> str:
    print()
    print("  Reactions (mock):")
    print("    A - Lean in: praise effort and reflect together")
    print("    B - Step back: space now, check in later")
    print("    C - Coach: one concrete next step")
    while True:
        raw = input("Choose reaction (A-C): ").strip().upper()
        if raw in ("A", "B", "C"):
            return raw
        print("  Please enter A, B, or C.")


def prompt_auto_simulate_weeks() -> int:
    print()
    print("  Mock auto-simulate: advances calendar weeks and bumps traits at random.")
    print("  Branch tree grows at demo thresholds (weeks 4, 7, 10 in sim counter).")
    while True:
        raw = input("  Auto-simulate how many weeks first? [0]: ").strip() or "0"
        if raw.isdigit():
            return min(int(raw), 520)
        print("  Enter a non-negative integer (e.g. 0 to skip).")


def main() -> None:
    session = MockSession(traits=initial_traits())

    print()
    print(" Interactive mock: optional auto weeks, then pick event + reaction.")
    n_sim = prompt_auto_simulate_weeks()
    if n_sim:
        auto_simulate_weeks(session, n_sim)

    render_full(session)

    ev = prompt_event()
    reaction = prompt_reaction()
    apply_mock_choice(session, ev, reaction)
    session.summary = build_summary(session)

    print()
    render_star_separator("AFTER YOUR CHOICE (placeholder updates)")
    render_full(session)


if __name__ == "__main__":
    main()
