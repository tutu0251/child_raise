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
from game.template_data import DEFAULT_TRAIT_KEYS, load_events_templates, sample_weekly_events
from game.trait_updates import REACTION_KINDS, apply_trait_deltas, trait_deltas


GAME_ROOT = Path(__file__).resolve().parents[1] / "game"
EVENTS_JSON = GAME_ROOT / "data" / "events_templates.json"


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


if __name__ == "__main__":
    unittest.main()
