"""Load parametric child/event templates and sample age-appropriate weekly events by category."""

from __future__ import annotations

import json
import random
from pathlib import Path


DEFAULT_INTELLIGENCE: int = 50
DEFAULT_SOCIAL_TENDENCY: int = 50
DEFAULT_HEALTH: int = 100
DEFAULT_ENERGY: int = 100

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

EVENT_CATEGORIES: tuple[str, ...] = (
    "Emotional",
    "Social",
    "Learning",
    "Behavior",
    "Milestone",
    "Health",
)

_EVENT_CATEGORY_SET: frozenset[str] = frozenset(EVENT_CATEGORIES)

_STAGE_DEFAULT_WEIGHTS: dict[str, dict[str, float]] = {
    "infant": {k: 0.055 for k in DEFAULT_TRAIT_KEYS},
    "toddler": {k: 0.06 for k in DEFAULT_TRAIT_KEYS},
    "preschool": {k: 0.065 for k in DEFAULT_TRAIT_KEYS},
    "early_school": {k: 0.07 for k in DEFAULT_TRAIT_KEYS},
    "middle_childhood": {k: 0.075 for k in DEFAULT_TRAIT_KEYS},
    "adolescence": {k: 0.08 for k in DEFAULT_TRAIT_KEYS},
}


def _clamp_optional_int(value: object, default: int, lo: int, hi: int) -> int:
    if value is None:
        return default
    try:
        return max(lo, min(hi, int(value)))
    except (TypeError, ValueError):
        return default


def merge_child_stat_defaults(child: dict[str, str | int]) -> dict[str, str | int]:
    """Ensure newer UI/stat keys exist when loading saves created before those fields."""
    out = dict(child)
    out.setdefault("intelligence", DEFAULT_INTELLIGENCE)
    out.setdefault("social_tendency", DEFAULT_SOCIAL_TENDENCY)
    out.setdefault("health", DEFAULT_HEALTH)
    out.setdefault("energy", DEFAULT_ENERGY)
    return out


def _clamp_calendar_week(value: object) -> int:
    try:
        return max(1, min(52, int(value)))
    except (TypeError, ValueError):
        return 1


def effective_new_game_age_and_week(
    template: dict,
    *,
    start_age_years: int,
    calendar_week_fallback: int = 1,
) -> tuple[int, int, bool]:
    """
    Resolve starting ``age_years`` and ``calendar_week``.

    If ``template['age_years']`` is strictly greater than the player's start-age option
    (0 = birth, 3 = skip infancy), the template age wins and the template's calendar week
    is used when present.

    Returns ``(age_years, calendar_week, template_overrode_age)``.
    """
    tpl = dict(template)
    try:
        tpl_age = int(tpl.get("age_years", 0))
    except (TypeError, ValueError):
        tpl_age = 0
    try:
        chosen = int(start_age_years)
    except (TypeError, ValueError):
        chosen = 0
    if chosen not in (0, 3):
        chosen = 0 if chosen < 2 else 3

    template_overrode = tpl_age > chosen
    effective_age = tpl_age if template_overrode else chosen

    if template_overrode:
        cw = _clamp_calendar_week(tpl.get("calendar_week", 1))
    elif chosen == 3:
        cw = 1
    else:
        if "calendar_week" in tpl:
            cw = _clamp_calendar_week(tpl.get("calendar_week"))
        else:
            cw = _clamp_calendar_week(calendar_week_fallback)

    return effective_age, cw, template_overrode


def apply_new_game_choices(
    template: dict,
    *,
    start_age_years: int,
    gender: str,
    temperament: str,
    calendar_week: int = 1,
    intelligence: int | None = None,
    social_tendency: int | None = None,
    health: int | None = None,
    energy: int | None = None,
) -> dict:
    """Merge new-game dialog choices into a profile dict (mutates a shallow copy only)."""
    profile = dict(template)
    eff_age, eff_cw, _ = effective_new_game_age_and_week(
        template, start_age_years=start_age_years, calendar_week_fallback=calendar_week
    )
    profile["age_years"] = eff_age
    profile["calendar_week"] = eff_cw

    g = str(gender).strip()
    if g:
        profile["gender"] = g

    t = str(temperament).strip()
    if t:
        profile["temperament"] = t

    if intelligence is not None:
        profile["intelligence"] = _clamp_optional_int(intelligence, DEFAULT_INTELLIGENCE, 0, 100)
    if social_tendency is not None:
        profile["social_tendency"] = _clamp_optional_int(
            social_tendency, DEFAULT_SOCIAL_TENDENCY, 0, 100
        )
    if health is not None:
        profile["health"] = _clamp_optional_int(health, DEFAULT_HEALTH, 0, 100)
    if energy is not None:
        profile["energy"] = _clamp_optional_int(energy, DEFAULT_ENERGY, 0, 100)

    return profile


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


def canonical_event_category(raw: object) -> str | None:
    """Return a valid category string, or None if missing/invalid."""
    if not isinstance(raw, str):
        return None
    s = raw.strip()
    return s if s in _EVENT_CATEGORY_SET else None


def event_category(event: dict, *, fallback: str = "Behavior") -> str:
    c = canonical_event_category(event.get("category"))
    return c if c is not None else fallback


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


def _event_identity(ev: dict) -> str:
    eid = ev.get("id")
    if eid is not None:
        return str(eid)
    return str(id(ev))


def _pick_category_order_weighted(
    by_cat: dict[str, list[dict]],
    rng: random.Random,
    *,
    limit: int,
) -> list[str]:
    """Distinct categories, weighted toward categories with fewer templates (diversity)."""
    remaining = [c for c in EVENT_CATEGORIES if c in by_cat]
    if not remaining:
        remaining = list(by_cat.keys())
    weights = [1.0 / max(1, len(by_cat[c])) for c in remaining]
    order: list[str] = []
    while remaining and len(order) < limit:
        idx = rng.choices(range(len(remaining)), weights=weights, k=1)[0]
        order.append(remaining.pop(idx))
        weights.pop(idx)
    return order


def sample_weekly_events(
    catalog: list[dict],
    *,
    age_years: int,
    calendar_week: int,
    child_name: str,
    caretaker: str = "you",
    rng: random.Random | None = None,
    max_events: int = 3,
    categories_to_draw: tuple[str, ...] | list[str] | None = None,
) -> list[dict]:
    """Pick a random count in 0..min(max_events, pool); prefer one event per category, then fill."""
    rng = rng or random.Random()
    age_exact = child_age_years_exact(age_years, calendar_week)
    pool = events_matching_age(catalog, age_exact)
    if not pool:
        return []

    if categories_to_draw is not None:
        allowed = {
            c for raw in categories_to_draw if (c := canonical_event_category(raw)) is not None
        }
        if allowed:
            pool = [e for e in pool if event_category(e) in allowed]

    if not pool:
        return []

    cap = min(max_events, len(pool))
    k = rng.randint(0, cap)
    if k == 0:
        return []

    by_cat: dict[str, list[dict]] = {}
    for e in pool:
        by_cat.setdefault(event_category(e), []).append(e)

    category_order = _pick_category_order_weighted(by_cat, rng, limit=min(k, len(by_cat)))

    chosen_raw: list[dict] = []
    used: set[str] = set()

    for cat in category_order:
        if len(chosen_raw) >= k:
            break
        bucket = [e for e in by_cat.get(cat, ()) if _event_identity(e) not in used]
        if not bucket:
            continue
        pick = rng.choice(bucket)
        chosen_raw.append(pick)
        used.add(_event_identity(pick))

    while len(chosen_raw) < k:
        leftovers = [e for e in pool if _event_identity(e) not in used]
        if not leftovers:
            break
        pick = rng.choice(leftovers)
        chosen_raw.append(pick)
        used.add(_event_identity(pick))

    slots: list[dict] = []
    for e in chosen_raw:
        text = render_event_template(e, rng, child_name=child_name, caretaker=caretaker)
        cat = event_category(e)
        rarity_raw = e.get("rarity")
        rarity = str(rarity_raw).strip().lower() if rarity_raw else ""
        slots.append(
            {
                "id": e.get("id"),
                "text": text,
                "trait_weights": trait_weights_for_event(e),
                "category": cat,
                **({"rarity": rarity} if rarity else {}),
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
    categories_to_draw: tuple[str, ...] | list[str] | None = None,
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
            categories_to_draw=categories_to_draw,
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
        "intelligence": _clamp_optional_int(
            profile.get("intelligence"), DEFAULT_INTELLIGENCE, 0, 100
        ),
        "social_tendency": _clamp_optional_int(
            profile.get("social_tendency"), DEFAULT_SOCIAL_TENDENCY, 0, 100
        ),
        "health": _clamp_optional_int(profile.get("health"), DEFAULT_HEALTH, 0, 100),
        "energy": _clamp_optional_int(profile.get("energy"), DEFAULT_ENERGY, 0, 100),
    }
    return child, traits
