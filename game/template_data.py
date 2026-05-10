"""Load parametric child/event templates and sample age-appropriate weekly events."""

from __future__ import annotations

import json
import random
from pathlib import Path


DEFAULT_TRAIT_KEYS: tuple[str, ...] = (
    "Openness",
    "Conscientiousness",
    "Extraversion",
    "Agreeableness",
    "Neuroticism",
    "Resilience",
    "Independence",
    "Risk-taking",
)

_STAGE_DEFAULT_WEIGHTS: dict[str, dict[str, float]] = {
    "infant": {k: 0.055 for k in DEFAULT_TRAIT_KEYS},
    "toddler": {k: 0.06 for k in DEFAULT_TRAIT_KEYS},
    "preschool": {k: 0.065 for k in DEFAULT_TRAIT_KEYS},
    "early_school": {k: 0.07 for k in DEFAULT_TRAIT_KEYS},
    "middle_childhood": {k: 0.075 for k in DEFAULT_TRAIT_KEYS},
    "adolescence": {k: 0.08 for k in DEFAULT_TRAIT_KEYS},
}


def load_child_templates(path: Path | str) -> list[dict]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    templates = raw.get("templates")
    if not isinstance(templates, list):
        raise ValueError("child_templates.json must contain a 'templates' array")
    return templates


def load_events_templates(path: Path | str) -> list[dict]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    events = raw.get("events")
    if not isinstance(events, list):
        raise ValueError("events_templates.json must contain an 'events' array")
    return events


def child_age_years_exact(age_years: int, calendar_week: int) -> float:
    """Rough continuous age for filtering (week advances within the same calendar year)."""
    w = max(1, int(calendar_week))
    return float(age_years) + (w - 1) / 52.0


def events_matching_age(catalog: list[dict], age_exact: float) -> list[dict]:
    out: list[dict] = []
    for e in catalog:
        try:
            lo = float(e["age_min_years"])
            hi = float(e["age_max_years"])
        except (KeyError, TypeError):
            continue
        if lo <= age_exact <= hi:
            out.append(e)
    return out


def trait_weights_for_event(event: dict) -> dict[str, float]:
    """Merge JSON trait_weights with stage defaults when missing or partial."""
    stage = str(event.get("stage_id", "middle_childhood"))
    base = dict(_STAGE_DEFAULT_WEIGHTS.get(stage, _STAGE_DEFAULT_WEIGHTS["middle_childhood"]))
    raw = event.get("trait_weights")
    if isinstance(raw, dict):
        for k, v in raw.items():
            if k in base and v is not None:
                try:
                    base[k] = float(v)
                except (TypeError, ValueError):
                    continue
    return base


def render_event_template(
    event: dict,
    rng: random.Random,
    *,
    child_name: str,
    caretaker: str = "you",
) -> str:
    """Fill `{placeholders}` using `pools` (random picks) and fixed kwargs."""
    template = str(event.get("template", ""))
    pools = event.get("pools") or {}
    picks: dict[str, str] = {}
    for key, options in pools.items():
        if isinstance(options, list) and options:
            picks[str(key)] = str(rng.choice(options))
        else:
            picks[str(key)] = ""
    picks.setdefault("child_name", child_name)
    picks.setdefault("caretaker", caretaker)
    picks["child_name"] = child_name
    picks["caretaker"] = caretaker
    return template.format(**picks)


def sample_weekly_events(
    catalog: list[dict],
    *,
    age_years: int,
    calendar_week: int,
    child_name: str,
    caretaker: str = "you",
    rng: random.Random | None = None,
    max_events: int = 3,
) -> list[dict]:
    """Pick a random count in 0..min(3, pool) inclusive; return rendered slots with weights."""
    rng = rng or random.Random()
    age_exact = child_age_years_exact(age_years, calendar_week)
    pool = events_matching_age(catalog, age_exact)
    if not pool:
        return []

    cap = min(max_events, len(pool))
    k = rng.randint(0, cap)
    if k == 0:
        return []

    chosen = rng.sample(pool, k=k)
    slots: list[dict] = []
    for e in chosen:
        text = render_event_template(e, rng, child_name=child_name, caretaker=caretaker)
        slots.append(
            {
                "id": e.get("id"),
                "text": text,
                "trait_weights": trait_weights_for_event(e),
            }
        )
    return slots


def sample_weekly_event_strings(
    catalog: list[dict],
    *,
    age_years: int,
    calendar_week: int,
    child_name: str,
    caretaker: str = "you",
    rng: random.Random | None = None,
    max_events: int = 3,
) -> list[str]:
    """Convenience: text lines only (0–3 events)."""
    return [
        s["text"]
        for s in sample_weekly_events(
            catalog,
            age_years=age_years,
            calendar_week=calendar_week,
            child_name=child_name,
            caretaker=caretaker,
            rng=rng,
            max_events=max_events,
        )
    ]


def profile_to_game_child(profile: dict) -> tuple[dict[str, str | int], dict[str, int]]:
    """Split JSON profile into UI child dict and numeric traits."""
    traits_raw = profile.get("baseline_traits") or {}
    traits: dict[str, int] = {}
    for key in DEFAULT_TRAIT_KEYS:
        if key in traits_raw:
            traits[key] = max(0, min(100, int(traits_raw[key])))
        else:
            traits[key] = 50

    child: dict[str, str | int] = {
        "name": str(profile.get("name", "Child")),
        "age_years": int(profile.get("age_years", 8)),
        "calendar_week": int(profile.get("calendar_week", 1)),
        "gender": str(profile.get("gender", "")),
        "branch": str(profile.get("branch", "")),
        "temperament": str(profile.get("temperament", "")),
    }
    return child, traits
