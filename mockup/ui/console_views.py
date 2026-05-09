"""Composed console panels — pass plain data from mock or from `game/` later."""

from __future__ import annotations

from mockup.ui.layout import (
    WIDTH,
    footer,
    hr,
    section,
    trait_bar,
    trend_arrow,
    trend_legend,
    wrap_paragraph,
)


def render_status_bar(
    *,
    banner_title: str,
    name: str,
    week: int,
    gender: str,
    branch: str,
    temperament: str,
    extra_lines: list[str] | None = None,
) -> None:
    hr("=")
    print(f" {banner_title} ".center(WIDTH))
    hr("=")
    print(f"  Name: {name}")
    print(f"  Age: Week {week}   Gender: {gender}")
    print(f"  Branch: {branch}")
    print(f"  Temperament: {temperament}")
    if extra_lines:
        for ln in extra_lines:
            print(f"  {ln}")


def render_trait_panel(
    traits: dict[str, int],
    trait_order: list[str],
    trait_previous: dict[str, int] | None,
    *,
    heading: str | None = None,
) -> None:
    title = heading or f"PERSONALITY - traits (trend vs last snapshot: {trend_legend()})"
    section(title)
    for name in trait_order:
        tr = trend_arrow(trait_previous, name, traits[name])
        trait_bar(name, traits[name], tr)


def render_early_years_panel(
    cumulative_gains: dict[str, int],
    trait_order: list[str],
    auto_sim_weeks: int,
    *,
    panel_title: str = "EARLY YEARS - mock cumulative gains (optional demo)",
    blurb: str = "Sum of positive mock increments since session start (not a real stat model).",
) -> None:
    total = sum(cumulative_gains.values())
    if total == 0 and auto_sim_weeks == 0:
        return
    section(panel_title)
    print(f"  {blurb}")
    for name in trait_order:
        g = cumulative_gains.get(name, 0)
        bar_c = min(20, g)
        mini = "#" * bar_c + "-" * (20 - bar_c)
        print(f"  {name:<14} +{g:>4} total   [{mini}]")
    print(f"  Auto-sim weeks logged: {auto_sim_weeks}")


def render_events_panel(events: list[str], *, subtitle: str = "pick one below") -> None:
    section(f"WEEKLY EVENTS ({subtitle})")
    for i, ev in enumerate(events, start=1):
        print(f"  {i}. {ev}")


def render_summary_panel(text: str) -> None:
    section("WEEKLY SUMMARY")
    wrap_paragraph(text)


def render_branch_panel(lines: list[str], *, section_title: str) -> None:
    section(section_title)
    print("\n".join(lines))


def render_controls_panel(controls: list[tuple[str, str]]) -> None:
    section("CONTROLS (labels only - no bindings)")
    for label, hint in controls:
        print(f"  [{label:^11}]  - {hint}")
    print()
    print("  " + " | ".join(f"[{lbl}]" for lbl, _ in controls))


def render_change_banner(
    *,
    banner_title: str,
    event_index: int | None,
    reaction: str | None,
    deltas: dict[str, int],
) -> None:
    if event_index is None and not deltas:
        return
    section(banner_title)
    if event_index is not None:
        print(f"  Event: {event_index}   Reaction: {reaction}")
    if deltas:
        parts = [f"{k} {v:+d}" for k, v in sorted(deltas.items())]
        print(f"  Trait deltas (demo): {', '.join(parts)}")


def render_star_separator(title: str) -> None:
    hr("*")
    print(f" {title} ".center(WIDTH))
    hr("*")
