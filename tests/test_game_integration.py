"""Integration tests: progression mechanics, persistence, options, GUI smoke (no manual play)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from game.narrative_placeholder import build_weekly_narrative_feedback
from game.persistence import (
    SCHEMA_VERSION,
    dump_save,
    fork_payload_from_loaded,
    load_save,
    render_saved_branch_forest,
    traits_compact,
)
from game.settings import GameSettings
from game.template_data import (
    DEFAULT_ENERGY,
    DEFAULT_HEALTH,
    DEFAULT_INTELLIGENCE,
    DEFAULT_SOCIAL_TENDENCY,
    DEFAULT_TRAIT_KEYS,
    EVENT_CATEGORIES,
    apply_new_game_choices,
    load_child_templates,
    load_events_templates,
    profile_to_game_child,
    sample_weekly_events,
)
from game.trait_updates import REACTION_KINDS, apply_trait_deltas, trait_deltas
from game.personality_analysis import build_personality_analysis
from game.simulation import (
    advance_game_week,
    apply_auto_reactions_current_week,
    build_autoplay_context_from_profile,
    format_batch_trait_summary,
    normalize_age_calendar_week,
    run_autoplay_until_complete,
    trait_delta_between,
)


GAME_ROOT = Path(__file__).resolve().parents[1] / "game"
EVENTS_JSON = GAME_ROOT / "data" / "events_templates.json"
CHILD_JSON = GAME_ROOT / "data" / "child_templates.json"


class TestNewGameProfileInit(unittest.TestCase):
    def test_apply_new_game_choices_start_age_and_profile_to_child(self) -> None:
        if not CHILD_JSON.is_file():
            raise unittest.SkipTest("child_templates.json missing")
        profiles = load_child_templates(CHILD_JSON)
        self.assertTrue(profiles)
        base = dict(profiles[0])
        profile = apply_new_game_choices(
            base,
            start_age_years=3,
            gender="Girl",
            temperament="Test temperament",
            calendar_week=1,
        )
        self.assertEqual(profile["age_years"], 3)
        self.assertEqual(profile["calendar_week"], 1)
        self.assertEqual(profile["gender"], "Girl")
        self.assertEqual(profile["temperament"], "Test temperament")

        child, traits = profile_to_game_child(profile)
        self.assertEqual(int(child["age_years"]), 3)
        self.assertEqual(int(child["calendar_week"]), 1)
        self.assertEqual(str(child["gender"]), "Girl")
        self.assertEqual(str(child["temperament"]), "Test temperament")
        self.assertIn("intelligence", child)
        self.assertIn("social_tendency", child)
        self.assertIn("health", child)
        self.assertIn("energy", child)
        self.assertEqual(int(child["intelligence"]), DEFAULT_INTELLIGENCE)
        self.assertEqual(int(child["social_tendency"]), DEFAULT_SOCIAL_TENDENCY)
        self.assertEqual(int(child["health"]), DEFAULT_HEALTH)
        self.assertEqual(int(child["energy"]), DEFAULT_ENERGY)
        self.assertTrue(traits)

    def test_profile_optional_stats_from_template(self) -> None:
        profile = {
            "name": "Unit",
            "age_years": 0,
            "calendar_week": 1,
            "gender": "Boy",
            "branch": "B",
            "temperament": "T",
            "baseline_traits": {k: 50 for k in DEFAULT_TRAIT_KEYS},
            "intelligence": 62,
            "social_tendency": 48,
            "health": 88,
            "energy": 77,
        }
        child, _ = profile_to_game_child(profile)
        self.assertEqual(int(child["intelligence"]), 62)
        self.assertEqual(int(child["social_tendency"]), 48)
        self.assertEqual(int(child["health"]), 88)
        self.assertEqual(int(child["energy"]), 77)

    def test_start_age_zero(self) -> None:
        p = apply_new_game_choices(
            {"id": "x", "name": "N", "age_years": 8, "gender": "x", "temperament": "y", "branch": "b"},
            start_age_years=0,
            gender="",
            temperament="",
            calendar_week=5,
        )
        self.assertEqual(p["age_years"], 0)
        self.assertEqual(p["calendar_week"], 5)


class TestGameMainWindowTopBar(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not EVENTS_JSON.is_file():
            raise unittest.SkipTest("events_templates.json missing")

    def test_top_bar_reflects_child_age_and_stats(self) -> None:
        from game.ui.layout import GameMainWindow

        catalog = load_events_templates(EVENTS_JSON)
        profile = apply_new_game_choices(
            {
                "id": "gui_test",
                "name": "Alex",
                "age_years": 8,
                "calendar_week": 99,
                "gender": "Boy",
                "temperament": "Calm",
                "branch": "Main",
                "baseline_traits": {k: 50 for k in DEFAULT_TRAIT_KEYS},
            },
            start_age_years=3,
            gender="Non-binary",
            temperament="Calm",
            calendar_week=1,
        )
        child, traits = profile_to_game_child(profile)

        win = GameMainWindow(
            child=child,
            traits=traits,
            events_catalog=catalog,
            summary_narrative="Test",
            stats_blurb="Blurb",
            rng=None,
        )
        try:
            self.assertEqual(win._top_labels["week_lbl"].cget("text"), "Age 3 · Week 1")
            self.assertEqual(win._top_labels["gender_lbl"].cget("text"), "Non-binary")
            self.assertEqual(win._top_labels["intel_lbl"].cget("text"), str(DEFAULT_INTELLIGENCE))
        finally:
            win.root.destroy()


class TestTraitProgression(unittest.TestCase):
    def test_trait_deltas_and_clamp(self) -> None:
        weights = {k: 0.08 for k in DEFAULT_TRAIT_KEYS}
        d = trait_deltas(weights, "Praise", 8)
        self.assertTrue(d)
        traits = {k: 95 for k in DEFAULT_TRAIT_KEYS}
        out = apply_trait_deltas(traits, d)
        for k, v in out.items():
            self.assertGreaterEqual(v, 0)
            self.assertLessEqual(v, 100)

    def test_reaction_kinds_cover_ui(self) -> None:
        self.assertEqual(
            set(REACTION_KINDS),
            {"Praise", "Punish", "Guide", "Encourage", "Restrict", "Ignore"},
        )


class TestWeeklyEvents(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not EVENTS_JSON.is_file():
            raise unittest.SkipTest("events_templates.json missing")
        cls._catalog = load_events_templates(EVENTS_JSON)

    def test_sample_weekly_events_age_bounded(self) -> None:
        import random

        rng = random.Random(42)
        for _ in range(30):
            slots = sample_weekly_events(
                self._catalog,
                age_years=8,
                calendar_week=12,
                child_name="Test",
                rng=rng,
                max_events=3,
            )
            self.assertLessEqual(len(slots), 3)
            for s in slots:
                self.assertIn("text", s)
                self.assertIn("trait_weights", s)
                self.assertEqual(len(s["trait_weights"]), len(DEFAULT_TRAIT_KEYS))
                self.assertIn("category", s)
                self.assertIn(s["category"], EVENT_CATEGORIES)

    def test_sample_weekly_events_category_filter(self) -> None:
        import random

        catalog = [
            {
                "id": "t_learn",
                "stage_id": "middle_childhood",
                "category": "Learning",
                "age_min_years": 5.0,
                "age_max_years": 12.0,
                "template": "Study {child_name}",
                "pools": {},
            },
            {
                "id": "t_social",
                "stage_id": "middle_childhood",
                "category": "Social",
                "age_min_years": 5.0,
                "age_max_years": 12.0,
                "template": "Friends {child_name}",
                "pools": {},
            },
            {
                "id": "t_health",
                "stage_id": "middle_childhood",
                "category": "Health",
                "age_min_years": 5.0,
                "age_max_years": 12.0,
                "template": "Rest {child_name}",
                "pools": {},
            },
        ]
        rng = random.Random(0)
        for _ in range(50):
            slots = sample_weekly_events(
                catalog,
                age_years=8,
                calendar_week=1,
                child_name="Kid",
                rng=rng,
                max_events=3,
                categories_to_draw=("Learning", "Social"),
            )
            self.assertLessEqual(len(slots), 3)
            for s in slots:
                self.assertIn(s["category"], ("Learning", "Social"))

    def test_sample_weekly_events_prefers_distinct_categories(self) -> None:
        import random

        catalog = [
            {
                "id": f"c{i}",
                "stage_id": "middle_childhood",
                "category": cat,
                "age_min_years": 0.0,
                "age_max_years": 18.0,
                "template": f"Situation {i} for {{child_name}}",
                "pools": {},
            }
            for i, cat in enumerate(EVENT_CATEGORIES[:3])
        ]
        rng = random.Random(12345)
        slots = sample_weekly_events(
            catalog,
            age_years=10,
            calendar_week=1,
            child_name="X",
            rng=rng,
            max_events=3,
        )
        if len(slots) == 3:
            cats = [s["category"] for s in slots]
            self.assertEqual(len(cats), len(set(cats)), cats)

    def test_sample_weekly_events_passes_optional_rarity(self) -> None:
        catalog = [
            {
                "id": "rare_one",
                "stage_id": "infant",
                "category": "Milestone",
                "rarity": "rare",
                "age_min_years": 0.0,
                "age_max_years": 1.0,
                "template": "Hello {child_name}",
                "pools": {},
            }
        ]
        for seed in range(500):
            rng = __import__("random").Random(seed)
            slots = sample_weekly_events(
                catalog,
                age_years=0,
                calendar_week=1,
                child_name="B",
                rng=rng,
                max_events=3,
            )
            if slots:
                self.assertEqual(slots[0].get("rarity"), "rare")
                break
        else:
            self.fail("expected at least one non-empty weekly draw")

    def test_sample_weekly_events_templates_have_category_field(self) -> None:
        missing = [e for e in self._catalog if "category" not in e]
        self.assertEqual(missing, [])


class TestPersistence(unittest.TestCase):
    def test_roundtrip_and_fork(self) -> None:
        payload = {
            "schema_version": SCHEMA_VERSION,
            "branch_id": "orig-branch",
            "branch_label": "Main",
            "parent_branch_id": None,
            "parent_save_file": None,
            "forked_at_week": None,
            "child": {"name": "Test", "age_years": 7, "calendar_week": 5, "gender": "x", "branch": "b", "temperament": "t"},
            "traits": {k: 50 for k in DEFAULT_TRAIT_KEYS},
            "calendar_week": 5,
            "week_history": [],
            "game_settings": GameSettings().to_dict(),
            "current_week_pending": {
                "weekly_slots": [],
                "handled_events": [],
                "week_reaction_lines": [],
                "current_week_reactions": [],
                "event_descriptions": [],
            },
        }
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "save.json"
            dump_save(payload, path)
            loaded = load_save(path)
            self.assertEqual(loaded["branch_id"], "orig-branch")
            self.assertEqual(loaded["traits"]["Openness"], 50)

            forked = fork_payload_from_loaded(loaded, new_label="Alt", parent_file_name="save.json")
            self.assertNotEqual(forked["branch_id"], "orig-branch")
            self.assertEqual(forked["branch_label"], "Alt")
            self.assertEqual(forked["parent_branch_id"], "orig-branch")


class TestSettings(unittest.TestCase):
    def test_roundtrip_dict(self) -> None:
        g = GameSettings(simulation_length_years=16, batch_early_years_stats=True)
        h = GameSettings.from_dict(g.to_dict())
        self.assertEqual(h.simulation_length_years, 16)
        self.assertTrue(h.batch_early_years_stats)


class TestNarrativePlaceholder(unittest.TestCase):
    def test_feedback_non_empty(self) -> None:
        t = build_weekly_narrative_feedback(
            calendar_week=3,
            child_name="Sam",
            event_count=2,
            reaction_lines_count=1,
            traits_now={"Openness": 52},
            traits_week_start={"Openness": 50},
            simulation_target_years=18,
            simulated_years_approx=8.1,
        )
        self.assertIn("Sam", t)
        self.assertGreater(len(t), 40)


class TestBranchForestRender(unittest.TestCase):
    def test_render_lines_without_crash(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sd = Path(td)
            lines = render_saved_branch_forest(
                sd,
                current_branch_id="abc",
                current_week=4,
                current_traits={"Openness": 50},
                current_label="Play",
            )
            self.assertTrue(any("Live session" in ln or "SESSION" in ln.upper() or "live" in ln.lower() for ln in lines))


class TestStatsPanelSmoke(unittest.TestCase):
    def test_build_destroy(self) -> None:
        import tkinter as tk
        from tkinter import ttk

        from game.ui.stats_panel import StatsPanel

        root = tk.Tk()
        root.withdraw()
        try:
            f = ttk.Frame(root)
            p = StatsPanel.build(f, list(DEFAULT_TRAIT_KEYS))
            p.set_traits({k: 40 + i for i, k in enumerate(DEFAULT_TRAIT_KEYS)}, baseline={k: 40 for k in DEFAULT_TRAIT_KEYS})
            root.update_idletasks()
        finally:
            root.destroy()


class TestSummaryPanelFormatting(unittest.TestCase):
    def test_normalize_collapses_blank_lines(self) -> None:
        from game.ui.summary_panel import normalize_paragraphs

        s = "a\n\n\n\nb"
        self.assertEqual(normalize_paragraphs(s), "a\n\nb")


class TestAutoPlaySimulation(unittest.TestCase):
    def test_apply_auto_reactions_guide_updates_traits(self) -> None:
        settings = GameSettings(
            auto_play_reaction_mode="guide",
            auto_play_intensity_min=10,
            auto_play_intensity_max=10,
        )
        rng = __import__("random").Random(0)
        traits = {k: 50 for k in DEFAULT_TRAIT_KEYS}
        slots = [
            {
                "id": "e1",
                "text": "situation",
                "trait_weights": {k: 0.12 for k in DEFAULT_TRAIT_KEYS},
                "category": "Learning",
            }
        ]
        handled: set[int] = set()
        lines: list[str] = []
        reacts: list[dict] = []
        n = apply_auto_reactions_current_week(
            traits=traits,
            weekly_slots=slots,
            handled_events=handled,
            week_reaction_lines=lines,
            current_week_reactions=reacts,
            settings=settings,
            rng=rng,
        )
        self.assertEqual(n, 1)
        self.assertEqual(handled, {0})
        self.assertTrue(any(traits.get(k, 50) != 50 for k in DEFAULT_TRAIT_KEYS))

    def test_advance_game_week_rolls_age_after_week_52(self) -> None:
        import random

        rng = random.Random(0)
        child = {"name": "Kid", "age_years": 3, "calendar_week": 52}
        traits = {k: 55 for k in DEFAULT_TRAIT_KEYS}
        catalog = [
            {
                "id": "ev",
                "stage_id": "middle_childhood",
                "category": "Learning",
                "age_min_years": 5.0,
                "age_max_years": 12.0,
                "template": "Study {child_name}",
                "pools": {},
            }
        ]
        weekly_slots: list[dict] = []
        handled: set[int] = set()
        week_lines: list[str] = []
        current_rx: list[dict] = []
        event_descriptions: list[str] = []
        week_history: list[dict] = []

        new_cw, _ = advance_game_week(
            child=child,
            traits=traits,
            calendar_week=52,
            weekly_slots=weekly_slots,
            handled_events=handled,
            week_reaction_lines=week_lines,
            current_week_reactions=current_rx,
            event_descriptions=event_descriptions,
            week_history=week_history,
            events_catalog=catalog,
            rng=rng,
        )
        self.assertEqual(new_cw, 1)
        self.assertEqual(child["age_years"], 4)
        self.assertEqual(child.get("calendar_week"), 1)

    def test_normalize_age_calendar_week_repairs_flat_counter(self) -> None:
        child = {"name": "Kid", "age_years": 3}
        cw = normalize_age_calendar_week(child, 833)
        self.assertEqual(cw, 1)
        self.assertEqual(child["age_years"], 19)

    def test_advance_game_week_appends_history(self) -> None:
        import random

        rng = random.Random(0)
        child = {"name": "Kid", "age_years": 10, "calendar_week": 2}
        traits = {k: 55 for k in DEFAULT_TRAIT_KEYS}
        catalog = [
            {
                "id": "ev",
                "stage_id": "middle_childhood",
                "category": "Learning",
                "age_min_years": 5.0,
                "age_max_years": 12.0,
                "template": "Study {child_name}",
                "pools": {},
            }
        ]
        weekly_slots = [
            {
                "id": "e1",
                "text": "x",
                "trait_weights": {k: 0.05 for k in DEFAULT_TRAIT_KEYS},
                "category": "Learning",
            }
        ]
        handled: set[int] = {0}
        week_lines = ["Event 1: Guide"]
        current_rx = [{"event_index": 0, "reaction": "Guide", "intensity": 5}]
        event_descriptions = ["x"]
        week_history: list[dict] = []

        new_cw, tws = advance_game_week(
            child=child,
            traits=traits,
            calendar_week=2,
            weekly_slots=weekly_slots,
            handled_events=handled,
            week_reaction_lines=week_lines,
            current_week_reactions=current_rx,
            event_descriptions=event_descriptions,
            week_history=week_history,
            events_catalog=catalog,
            rng=rng,
        )
        self.assertEqual(new_cw, 3)
        self.assertEqual(child.get("calendar_week"), 3)
        self.assertEqual(len(week_history), 1)
        self.assertEqual(week_history[0]["calendar_week"], 2)
        self.assertFalse(week_lines)
        self.assertEqual(tws, dict(traits))

    def test_autoplay_context_runs_steps_without_input(self) -> None:
        if not EVENTS_JSON.is_file():
            raise unittest.SkipTest("events_templates.json missing")
        import random

        catalog = load_events_templates(EVENTS_JSON)
        profile = {
            "name": "AutoKid",
            "age_years": 10,
            "calendar_week": 1,
            "gender": "Girl",
            "branch": "Test branch",
            "temperament": "Calm",
            "baseline_traits": {k: 50 for k in DEFAULT_TRAIT_KEYS},
        }
        rng = random.Random(42)
        ctx = build_autoplay_context_from_profile(profile, rng=rng, events_catalog=catalog)
        settings = GameSettings()
        for _ in range(6):
            ctx.step(catalog, settings, rng)
        self.assertEqual(len(ctx.week_history), 6)

    def test_personality_analysis_includes_traits_and_reactions(self) -> None:
        traits = {k: 40 + i for i, k in enumerate(DEFAULT_TRAIT_KEYS)}
        hist = [
            {
                "calendar_week": 1,
                "reactions": [{"reaction": "Guide"}, {"reaction": "Praise"}],
                "traits_end": traits,
                "narrative": "",
                "event_texts": [],
            }
        ]
        text = build_personality_analysis(
            child={"name": "Sam", "branch": "Main"},
            traits=traits,
            week_history=hist,
            simulation_length_years=18,
            simulated_years_approx=17.9,
        )
        self.assertIn("Sam", text)
        self.assertIn("Guide", text)
        self.assertIn("Praise", text)

    def test_trait_delta_between_sums_moves(self) -> None:
        a = {k: 50 for k in DEFAULT_TRAIT_KEYS}
        b = dict(a)
        b["Openness"] = 55
        b["Neuroticism"] = 48
        d = trait_delta_between(a, b)
        self.assertEqual(d.get("Openness"), 5)
        self.assertEqual(d.get("Neuroticism"), -2)

    def test_format_batch_trait_summary(self) -> None:
        s = format_batch_trait_summary({"Openness": 3, "Neuroticism": -1})
        self.assertIn("Openness +3", s)
        self.assertIn("Neuroticism -1", s)

    def test_highlights_milestone_and_rare(self) -> None:
        settings = GameSettings(
            auto_play_reaction_mode="guide",
            auto_play_intensity_min=10,
            auto_play_intensity_max=10,
            auto_play_collect_highlights=True,
            auto_play_major_trait_delta=50,
        )
        rng = __import__("random").Random(0)
        traits = {k: 50 for k in DEFAULT_TRAIT_KEYS}
        sink: list[dict] = []
        slots = [
            {
                "id": "m1",
                "text": "First words",
                "trait_weights": {k: 0.12 for k in DEFAULT_TRAIT_KEYS},
                "category": "Milestone",
            },
            {
                "id": "r1",
                "text": "Rare moment",
                "trait_weights": {k: 0.12 for k in DEFAULT_TRAIT_KEYS},
                "category": "Learning",
                "rarity": "rare",
            },
        ]
        apply_auto_reactions_current_week(
            traits=traits,
            weekly_slots=slots,
            handled_events=set(),
            week_reaction_lines=[],
            current_week_reactions=[],
            settings=settings,
            rng=rng,
            highlight_sink=sink,
            calendar_week=3,
            simulated_years_approx=3.1,
        )
        kinds = [tuple(x.get("kinds") or ()) for x in sink]
        self.assertTrue(any("milestone" in k for k in kinds))
        self.assertTrue(any("rare" in k for k in kinds))

    def test_autoplay_context_collects_highlights_end_to_end(self) -> None:
        if not EVENTS_JSON.is_file():
            raise unittest.SkipTest("events_templates.json missing")
        import random

        catalog = load_events_templates(EVENTS_JSON)
        profile = {
            "name": "HiKid",
            "age_years": 0,
            "calendar_week": 1,
            "gender": "Girl",
            "branch": "H",
            "temperament": "Calm",
            "baseline_traits": {k: 50 for k in DEFAULT_TRAIT_KEYS},
        }
        rng = random.Random(99)
        ctx = build_autoplay_context_from_profile(profile, rng=rng, events_catalog=catalog)
        settings = GameSettings(simulation_length_years=1, auto_play_collect_highlights=True)
        run_autoplay_until_complete(ctx, catalog, settings, rng)
        self.assertTrue(len(ctx.week_history) > 0)
        self.assertIsInstance(ctx.autoplay_highlights, list)

    def test_personality_analysis_lists_autoplay_highlights(self) -> None:
        traits = {k: 50 for k in DEFAULT_TRAIT_KEYS}
        hi = [
            {
                "kinds": ["milestone"],
                "calendar_week": 2,
                "simulated_years": 3.02,
                "event_text": "First steps",
                "reaction": "Encourage",
                "trait_delta_peak": 4,
            }
        ]
        text = build_personality_analysis(
            child={"name": "Lee", "branch": "B"},
            traits=traits,
            week_history=[],
            simulation_length_years=18,
            simulated_years_approx=18.0,
            autoplay_highlights=hi,
        )
        self.assertIn("Auto-play key events", text)
        self.assertIn("milestone", text)


if __name__ == "__main__":
    unittest.main()
