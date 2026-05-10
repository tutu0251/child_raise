"""Headless week advancement and auto-play stepping (shared with GUI)."""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from game.persistence import SCHEMA_VERSION, dump_save, utc_now_iso
from game.settings import GameSettings
from game.template_data import DEFAULT_TRAIT_KEYS, merge_child_stat_defaults, profile_to_game_child, sample_weekly_events
from game.trait_updates import REACTION_KINDS, apply_trait_deltas, format_delta_line, trait_deltas


def trait_delta_between(traits_before: dict[str, int], traits_after: dict[str, int]) -> dict[str, int]:
    """Integer trait changes from a baseline snapshot to a later snapshot (clamped traits)."""
    out: dict[str, int] = {}
    for k in DEFAULT_TRAIT_KEYS:
        b = int(traits_before.get(k, 50))
        a = int(traits_after.get(k, 50))
        d = a - b
        if d != 0:
            out[k] = d
    return out


def format_batch_trait_summary(deltas: dict[str, int]) -> str:
    if not deltas:
        return "traits ~flat"
    parts = [f"{k} {v:+d}" for k, v in sorted(deltas.items())]
    return ", ".join(parts)


def format_autoplay_highlight_line(h: dict) -> str:
    kinds = h.get("kinds") or []
    kind_lbl = "/".join(str(x) for x in kinds) if kinds else "event"
    sy = float(h.get("simulated_years", 0.0))
    cw = h.get("calendar_week", "?")
    head = f"[{kind_lbl}] ~{sy:.2f}y (week {cw})"
    txt = str(h.get("event_text", "")).replace("\n", " ").strip()
    if len(txt) > 90:
        txt = txt[:87] + "…"
    rx = h.get("reaction", "")
    detail = f"{rx}" if rx else ""
    if txt:
        detail = f"{detail} — {txt}".strip(" —") if detail else txt
    peak = h.get("trait_delta_peak")
    if peak is not None and "major_trait" in kinds:
        detail = f"{detail} (max |Δ|={peak})".strip()
    return f"{head}: {detail}" if detail else head


def simulated_years(child: dict[str, str | int], calendar_week: int) -> float:
    ay = float(child.get("age_years", 0))
    cw = max(1, int(calendar_week))
    return ay + (cw - 1) / 52.0


def normalize_age_calendar_week(child: dict[str, str | int], calendar_week: int) -> int:
    """
    Fold a week counter into 1..52 and add completed years to ``age_years``.

    Fixes inconsistent saves where ``calendar_week`` grew without rolling (e.g. Age 3 · Week 833).
    """
    ay = int(child.get("age_years", 0))
    cw = max(1, int(calendar_week))
    extra, rem = divmod(cw - 1, 52)
    child["age_years"] = ay + int(extra)
    return rem + 1


def advance_calendar_week(child: dict[str, str | int], calendar_week: int) -> int:
    """After completing ``calendar_week``, return the next week (1..52) and bump ``age_years`` on year rollover."""
    new_cw = int(calendar_week) + 1
    ay = int(child.get("age_years", 0))
    while new_cw > 52:
        ay += 1
        new_cw -= 52
    child["age_years"] = ay
    return new_cw


def pick_auto_reaction_and_intensity(settings: GameSettings, rng: random.Random) -> tuple[str, int]:
    mode = settings.auto_play_reaction_mode
    if mode == "guide":
        reaction = "Guide"
    elif mode == "encourage":
        reaction = "Encourage"
    else:
        kinds = list(REACTION_KINDS)
        wmap = settings.auto_play_random_reaction_weights
        if isinstance(wmap, dict) and wmap:
            weights = [max(0.0, float(wmap.get(k, 0.0))) for k in kinds]
            if sum(weights) > 0:
                reaction = rng.choices(kinds, weights=weights, k=1)[0]
            else:
                reaction = rng.choice(kinds)
        else:
            reaction = rng.choice(kinds)

    lo = max(0, min(10, int(settings.auto_play_intensity_min)))
    hi = max(0, min(10, int(settings.auto_play_intensity_max)))
    if hi < lo:
        lo, hi = hi, lo
    intensity = lo if lo == hi else rng.randint(lo, hi)
    return reaction, intensity


def finalize_week_snapshot(
    calendar_week: int,
    event_descriptions: list[str],
    current_week_reactions: list[dict],
    traits: dict[str, int],
    week_reaction_lines: list[str],
    week_history: list[dict],
) -> None:
    week_history.append(
        {
            "calendar_week": calendar_week,
            "event_texts": list(event_descriptions),
            "reactions": list(current_week_reactions),
            "traits_end": dict(traits),
            "narrative": "\n".join(week_reaction_lines),
        }
    )
    week_reaction_lines.clear()
    current_week_reactions.clear()


def advance_game_week(
    *,
    child: dict[str, str | int],
    traits: dict[str, int],
    calendar_week: int,
    weekly_slots: list[dict],
    handled_events: set[int],
    week_reaction_lines: list[str],
    current_week_reactions: list[dict],
    event_descriptions: list[str],
    week_history: list[dict],
    events_catalog: list[dict],
    rng: random.Random,
) -> tuple[int, dict[str, int]]:
    finalize_week_snapshot(
        calendar_week,
        event_descriptions,
        current_week_reactions,
        traits,
        week_reaction_lines,
        week_history,
    )
    new_cw = advance_calendar_week(child, calendar_week)
    child["calendar_week"] = new_cw
    weekly_slots[:] = sample_weekly_events(
        events_catalog,
        age_years=int(child.get("age_years", 8)),
        calendar_week=int(new_cw),
        child_name=str(child.get("name", "Child")),
        rng=rng,
        max_events=3,
    )
    handled_events.clear()
    event_descriptions[:] = [str(s.get("text", "")) for s in weekly_slots]
    traits_at_week_start = dict(traits)
    return new_cw, traits_at_week_start


def apply_auto_reactions_current_week(
    *,
    traits: dict[str, int],
    weekly_slots: list[dict],
    handled_events: set[int],
    week_reaction_lines: list[str],
    current_week_reactions: list[dict],
    settings: GameSettings,
    rng: random.Random,
    prefix: str = "[Auto] ",
    highlight_sink: list[dict] | None = None,
    calendar_week: int = 0,
    simulated_years_approx: float = 0.0,
) -> int:
    applied = 0
    collect = highlight_sink is not None and getattr(settings, "auto_play_collect_highlights", True)
    threshold = int(getattr(settings, "auto_play_major_trait_delta", 8))
    for i in range(len(weekly_slots)):
        if i in handled_events:
            continue
        reaction, intensity = pick_auto_reaction_and_intensity(settings, rng)
        slot = weekly_slots[i]
        weights = slot.get("trait_weights") or {}
        deltas = trait_deltas(weights, reaction, intensity)
        merged = apply_trait_deltas(dict(traits), deltas)
        traits.clear()
        traits.update(merged)
        handled_events.add(i)
        line = (
            f"{prefix}Event {i + 1}: {reaction} at intensity {intensity}. "
            f"{format_delta_line(deltas)}"
        )
        week_reaction_lines.append(line)
        current_week_reactions.append(
            {
                "event_index": i,
                "event_id": slot.get("id"),
                "event_text": slot.get("text"),
                "reaction": reaction,
                "intensity": intensity,
                "deltas": deltas,
                "line": line,
            }
        )
        if collect and highlight_sink is not None:
            cat = str(slot.get("category", ""))
            rarity = str(slot.get("rarity") or "").strip().lower()
            peak = max((abs(v) for v in deltas.values()), default=0)
            kinds: list[str] = []
            if cat == "Milestone":
                kinds.append("milestone")
            if rarity == "rare":
                kinds.append("rare")
            if peak >= threshold:
                kinds.append("major_trait")
            if kinds:
                highlight_sink.append(
                    {
                        "kinds": kinds,
                        "calendar_week": int(calendar_week),
                        "simulated_years": float(simulated_years_approx),
                        "event_id": slot.get("id"),
                        "event_text": str(slot.get("text", ""))[:400],
                        "category": cat,
                        "reaction": reaction,
                        "intensity": int(intensity),
                        "trait_delta_peak": int(peak),
                        "deltas": dict(deltas),
                    }
                )
        applied += 1
    return applied


@dataclass
class AutoplayContext:
    child: dict[str, str | int]
    traits: dict[str, int]
    calendar_week: int
    weekly_slots: list[dict]
    handled_events: set[int]
    week_reaction_lines: list[str]
    current_week_reactions: list[dict]
    event_descriptions: list[str]
    week_history: list[dict]
    traits_at_week_start: dict[str, int]
    autoplay_highlights: list[dict] = field(default_factory=list)

    def simulated_years(self) -> float:
        return simulated_years(self.child, self.calendar_week)

    def step(self, events_catalog: list[dict], settings: GameSettings, rng: random.Random) -> None:
        sink = self.autoplay_highlights if settings.auto_play_collect_highlights else None
        apply_auto_reactions_current_week(
            traits=self.traits,
            weekly_slots=self.weekly_slots,
            handled_events=self.handled_events,
            week_reaction_lines=self.week_reaction_lines,
            current_week_reactions=self.current_week_reactions,
            settings=settings,
            rng=rng,
            highlight_sink=sink,
            calendar_week=self.calendar_week,
            simulated_years_approx=self.simulated_years(),
        )
        self.calendar_week, self.traits_at_week_start = advance_game_week(
            child=self.child,
            traits=self.traits,
            calendar_week=self.calendar_week,
            weekly_slots=self.weekly_slots,
            handled_events=self.handled_events,
            week_reaction_lines=self.week_reaction_lines,
            current_week_reactions=self.current_week_reactions,
            event_descriptions=self.event_descriptions,
            week_history=self.week_history,
            events_catalog=events_catalog,
            rng=rng,
        )


def run_autoplay_until_complete(
    ctx: AutoplayContext,
    events_catalog: list[dict],
    settings: GameSettings,
    rng: random.Random,
) -> None:
    target = float(settings.simulation_length_years)
    while ctx.simulated_years() + 1e-9 < target:
        ctx.step(events_catalog, settings, rng)


def build_autoplay_context_from_profile(profile: dict, *, rng: random.Random, events_catalog: list[dict]) -> AutoplayContext:
    """Fresh context from a child profile dict (e.g. JSON template row)."""
    child, traits = profile_to_game_child(profile)
    child = merge_child_stat_defaults(dict(child))
    cw = int(child.get("calendar_week", 1))
    cw = normalize_age_calendar_week(child, cw)
    child["calendar_week"] = cw
    weekly_slots = sample_weekly_events(
        events_catalog,
        age_years=int(child.get("age_years", 8)),
        calendar_week=cw,
        child_name=str(child.get("name", "Child")),
        rng=rng,
        max_events=3,
    )
    handled_events: set[int] = set()
    event_descriptions = [str(s.get("text", "")) for s in weekly_slots]
    return AutoplayContext(
        child=child,
        traits=dict(traits),
        calendar_week=cw,
        weekly_slots=weekly_slots,
        handled_events=handled_events,
        week_reaction_lines=[],
        current_week_reactions=[],
        event_descriptions=event_descriptions,
        week_history=[],
        traits_at_week_start=dict(traits),
        autoplay_highlights=[],
    )


def run_batch_autoplay_save_all(
    *,
    templates: list[dict],
    events_catalog: list[dict],
    settings: GameSettings,
    save_dir: Path,
    branch_label_suffix: str = "auto",
) -> list[Path]:
    """Run headless auto-play for each template profile; write JSON saves. Returns paths."""
    save_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for tmpl in templates:
        rng = random.Random(hash(str(tmpl.get("id", ""))) & 0xFFFFFFFF)
        ctx = build_autoplay_context_from_profile(dict(tmpl), rng=rng, events_catalog=events_catalog)
        run_autoplay_until_complete(ctx, events_catalog, settings, rng)
        label = str(tmpl.get("branch", tmpl.get("name", "branch")))[:48]
        slug = "".join(c if c.isalnum() or c in "-_" else "_" for c in label)[:40] or "branch"
        path = save_dir / f"{slug}_{branch_label_suffix}_{uuid.uuid4().hex[:8]}.json"
        payload = {
            "schema_version": SCHEMA_VERSION,
            "saved_at": utc_now_iso(),
            "branch_id": str(uuid.uuid4()),
            "branch_label": f"{label}-{branch_label_suffix}",
            "parent_branch_id": None,
            "parent_save_file": None,
            "forked_at_week": None,
            "child": dict(ctx.child),
            "traits": dict(ctx.traits),
            "calendar_week": ctx.calendar_week,
            "week_history": list(ctx.week_history),
            "game_settings": settings.to_dict(),
            "current_week_pending": {
                "weekly_slots": list(ctx.weekly_slots),
                "handled_events": sorted(ctx.handled_events),
                "week_reaction_lines": list(ctx.week_reaction_lines),
                "current_week_reactions": list(ctx.current_week_reactions),
                "event_descriptions": list(ctx.event_descriptions),
            },
        }
        dump_save(payload, path)
        paths.append(path)
    return paths


__all__ = [
    "AutoplayContext",
    "advance_calendar_week",
    "advance_game_week",
    "apply_auto_reactions_current_week",
    "build_autoplay_context_from_profile",
    "finalize_week_snapshot",
    "format_autoplay_highlight_line",
    "format_batch_trait_summary",
    "normalize_age_calendar_week",
    "pick_auto_reaction_and_intensity",
    "run_autoplay_until_complete",
    "run_batch_autoplay_save_all",
    "simulated_years",
    "trait_delta_between",
]
