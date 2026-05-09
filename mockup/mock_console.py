"""Mock-specific wiring: maps `MockSession` into reusable console panels."""

from __future__ import annotations

from mockup.mock_branch_tree import build_branch_lines
from mockup.mock_constants import MOCK_CHILD, MOCK_CONTROLS, MOCK_EVENTS, MOCK_TRAITS_ORDER
from mockup.mock_session import MockSession, display_week
from mockup.ui.console_views import (
    render_branch_panel,
    render_change_banner,
    render_controls_panel,
    render_early_years_panel,
    render_events_panel,
    render_status_bar,
    render_summary_panel,
    render_trait_panel,
)
from mockup.ui.layout import footer


def render_full(session: MockSession) -> None:
    trait_names = [n for n, _ in MOCK_TRAITS_ORDER]
    notes: list[str] = []
    if session.auto_simulated_weeks:
        notes.append(
            f"Mock note: {session.auto_simulated_weeks} week(s) auto-simulated before this view."
        )

    render_status_bar(
        banner_title="CHILD MOCKUP - status bar",
        name=str(MOCK_CHILD["name"]),
        week=display_week(session),
        gender=str(MOCK_CHILD["gender"]),
        branch=str(MOCK_CHILD["branch"]),
        temperament=str(MOCK_CHILD["temperament"]),
        extra_lines=notes or None,
    )
    render_trait_panel(session.traits, trait_names, session.trait_previous)
    render_early_years_panel(
        session.cumulative_gains,
        trait_names,
        session.auto_simulated_weeks,
    )
    render_events_panel(MOCK_EVENTS)
    render_summary_panel(session.summary)
    render_branch_panel(
        build_branch_lines(session),
        section_title="BRANCH TREE (ASCII, expands as mock flags fire)",
    )
    render_controls_panel(MOCK_CONTROLS)
    render_change_banner(
        banner_title="LAST MOCK CHANGE",
        event_index=session.last_event,
        reaction=session.last_reaction,
        deltas=session.last_deltas,
    )
    footer()
