"""Real game v1.0 entry — loads JSON templates, opens Tk shell."""

from __future__ import annotations

import random
import sys
from pathlib import Path

# Allow `python main.py` from inside `game/` as well as `python -m game.main` from repo root.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_rp = str(_PROJECT_ROOT)
if _rp not in sys.path:
    sys.path.insert(0, _rp)

from game.template_data import (
    load_child_templates,
    load_events_templates,
    profile_to_game_child,
    sample_weekly_events,
)
from game.ui.layout import GameMainWindow

DATA_DIR = Path(__file__).resolve().parent / "data"


def _opening_summary(child_name: str, profile_id: str | None) -> str:
    pid = f" (profile `{profile_id}`)" if profile_id else ""
    return (
        f"{child_name} starts here{pid}. Weekly events are sampled from templates "
        "matched to age and calendar week, with random fills from each event's pools."
    )


def _opening_stats_blurb(
    catalog: list[dict],
    *,
    age_years: int,
    calendar_week: int,
    child_name: str,
    rng: random.Random,
) -> str:
    """Prove age/week filtering + parametric rendering at startup."""
    samples = sample_weekly_events(
        catalog,
        age_years=age_years,
        calendar_week=calendar_week,
        child_name=child_name,
        rng=rng,
        max_events=1,
    )
    teaser = samples[0]["text"] if samples else "(no events drawn for this age/week snapshot)"
    age_exact = age_years + max(0, calendar_week - 1) / 52.0
    return (
        f"Age≈{age_exact:.2f}y — pool filtered for this week. Example draw: {teaser}"
    )


def main() -> None:
    rng = random.Random()

    profiles = load_child_templates(DATA_DIR / "child_templates.json")
    catalog = load_events_templates(DATA_DIR / "events_templates.json")

    profile = rng.choice(profiles)
    child, traits = profile_to_game_child(profile)

    age_years = int(child["age_years"])
    calendar_week = int(child["calendar_week"])
    name = str(child["name"])
    profile_id = profile.get("id") if isinstance(profile.get("id"), str) else None

    summary = _opening_summary(name, profile_id)
    stats_blurb = _opening_stats_blurb(
        catalog,
        age_years=age_years,
        calendar_week=calendar_week,
        child_name=name,
        rng=rng,
    )

    GameMainWindow(
        child=child,
        traits=traits,
        events_catalog=catalog,
        rng=rng,
        summary_narrative=summary,
        stats_blurb=stats_blurb,
    ).run()


if __name__ == "__main__":
    main()
