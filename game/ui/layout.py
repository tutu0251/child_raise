"""Main Tk window: top bar, body panels, controls."""

from __future__ import annotations

import random
import re
import uuid
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

from game.persistence import (
    SCHEMA_VERSION,
    default_save_dir,
    dump_save,
    fork_payload_from_loaded,
    format_branch_comparison,
    load_save,
    list_save_paths,
    render_saved_branch_forest,
    traits_compact,
    utc_now_iso,
)
from game.narrative_placeholder import build_weekly_narrative_feedback
from game.settings import GameSettings
from game.template_data import DEFAULT_TRAIT_KEYS, merge_child_stat_defaults, sample_weekly_events
from game.trait_updates import REACTION_KINDS, apply_trait_deltas, format_delta_line, trait_deltas
from game.ui.options_dialog import show_options_dialog
from game.ui.branch_tree import BranchTreePanel
from game.ui.events_panel import EventsPanel
from game.ui.stats_panel import StatsPanel
from game.ui.summary_panel import SummaryPanel
from game.ui import theme


def _safe_filename_slug(label: str) -> str:
    s = re.sub(r"[^\w\-]+", "_", label.strip(), flags=re.UNICODE).strip("_")
    return (s[:40] if s else "save") or "save"


class GameMainWindow:
    """Tk shell with weekly events, traits, saves, and branch visualization."""

    def __init__(
        self,
        *,
        child: dict[str, str | int],
        traits: dict[str, int],
        events_catalog: list[dict],
        summary_narrative: str,
        stats_blurb: str,
        rng: random.Random | None = None,
        resume_payload: dict | None = None,
    ) -> None:
        self._game_root = Path(__file__).resolve().parents[1]
        self._save_dir = default_save_dir(self._game_root)
        self._child = dict(child)
        self._traits = dict(traits)
        self._events_catalog = list(events_catalog)
        self._rng = rng or random.Random()
        self._summary_narrative = summary_narrative
        self._stats_blurb = stats_blurb
        self._calendar_week = int(child.get("calendar_week", 12))
        self._debate_highlight = False
        self._weekly_slots: list[dict] = []
        self._handled_events: set[int] = set()
        self._week_reaction_lines: list[str] = []
        self._event_descriptions: list[str] = []
        self._week_history: list[dict] = []
        self._current_week_reactions: list[dict] = []
        self._branch_id = str(uuid.uuid4())
        self._branch_label = str(child.get("branch", "Playthrough"))[:48]
        self._parent_branch_id: str | None = None
        self._parent_save_file: str | None = None
        self._forked_at_week: int | None = None
        self._last_save_path: Path | None = None
        self._settings = GameSettings()
        self._traits_at_week_start: dict[str, int] = {}
        self._uneventful_auto_chain = 0
        self._auto_advancing_uneventful = False
        self._sim_complete_shown = False
        self._narrative_auto_uneventful = False

        if resume_payload is not None:
            self._restore_save_payload(resume_payload)
        else:
            self._resample_weekly_events()

        self._child = merge_child_stat_defaults(self._child)

        self.root = tk.Tk()
        # Avoid visible resize/reflow flicker while widgets are packed (common on Windows).
        self.root.withdraw()
        self._update_title()
        self.root.minsize(*theme.WINDOW_MIN_SIZE)

        self._top_labels: dict[str, ttk.Label] = {}

        outer = ttk.Frame(self.root, padding=8)
        outer.pack(fill=tk.BOTH, expand=True)

        self._build_top_bar(outer)

        body = ttk.Frame(outer)
        body.pack(fill=tk.BOTH, expand=True)

        right_col = ttk.Frame(body)
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(12, 0))

        left_wrap = ttk.Frame(body)
        left_wrap.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        left_inner = ttk.Frame(left_wrap, padding=(0, 0, 8, 0))
        left_inner.pack(fill=tk.BOTH, expand=True)

        trait_names = list(self._traits.keys())
        self._stats_panel = StatsPanel.build(left_inner, trait_names)
        self._bind_summary_wraplength(left_inner)

        self._events_panel = EventsPanel.build(left_inner, self._on_event_reaction)
        self._build_controls(left_inner)

        self._summary_panel = SummaryPanel.build(right_col)
        self._branch_panel = BranchTreePanel.build(right_col, autopack=False)
        self._sync_branch_panel_visibility()

        self._snapshot_trait_week_start()
        self.refresh_all()

        self.root.update_idletasks()
        self.root.deiconify()

    def _bind_summary_wraplength(self, left_inner: ttk.Frame) -> None:
        """Keep stats hint readable when the left panel is resized."""

        last_w: list[int | None] = [None]

        def _go(evt: tk.Event) -> None:
            if evt.widget is not left_inner:
                return
            try:
                nw = int(evt.width)
            except tk.TclError:
                return
            if last_w[0] == nw:
                return
            last_w[0] = nw
            self._stats_panel.set_hint_wraplength(max(260, nw - 72))

        left_inner.bind("<Configure>", _go)

    def _sync_branch_panel_visibility(self) -> None:
        """Sidebar branch ASCII panel; optional via Options (popup still available)."""
        if self._settings.show_branch_timeline_panel:
            if not self._branch_panel.frame.winfo_ismapped():
                self._branch_panel.frame.pack(fill=tk.BOTH, expand=True)
        else:
            self._branch_panel.frame.pack_forget()

    def _update_title(self) -> None:
        self.root.title(f"{theme.WINDOW_TITLE} — {self._branch_label}")

    def _finalize_week_snapshot(self) -> None:
        self._week_history.append(
            {
                "calendar_week": self._calendar_week,
                "event_texts": list(self._event_descriptions),
                "reactions": list(self._current_week_reactions),
                "traits_end": dict(self._traits),
                "narrative": "\n".join(self._week_reaction_lines),
            }
        )
        self._week_reaction_lines.clear()
        self._current_week_reactions.clear()

    def _collect_save_payload(self) -> dict:
        return {
            "schema_version": SCHEMA_VERSION,
            "saved_at": utc_now_iso(),
            "branch_id": self._branch_id,
            "branch_label": self._branch_label,
            "parent_branch_id": self._parent_branch_id,
            "parent_save_file": self._parent_save_file,
            "forked_at_week": self._forked_at_week,
            "child": dict(self._child),
            "traits": dict(self._traits),
            "calendar_week": self._calendar_week,
            "week_history": list(self._week_history),
            "game_settings": self._settings.to_dict(),
            "current_week_pending": {
                "weekly_slots": list(self._weekly_slots),
                "handled_events": sorted(self._handled_events),
                "week_reaction_lines": list(self._week_reaction_lines),
                "current_week_reactions": list(self._current_week_reactions),
                "event_descriptions": list(self._event_descriptions),
            },
        }

    def _restore_save_payload(self, data: dict) -> None:
        if int(data.get("schema_version", 0)) != SCHEMA_VERSION:
            raise ValueError("Unsupported save version (expected schema_version 2).")
        self._child = dict(data.get("child") or {})
        tr = data.get("traits") or {}
        self._traits = {
            k: max(0, min(100, int(tr[k]))) for k in DEFAULT_TRAIT_KEYS if k in tr
        }
        for k in DEFAULT_TRAIT_KEYS:
            self._traits.setdefault(k, 50)

        self._calendar_week = int(data.get("calendar_week", 1))
        self._branch_id = str(data.get("branch_id") or uuid.uuid4())
        self._branch_label = str(data.get("branch_label", "Playthrough"))[:48]
        pb = data.get("parent_branch_id")
        self._parent_branch_id = str(pb) if pb else None
        pf = data.get("parent_save_file")
        self._parent_save_file = str(pf) if pf else None
        fw = data.get("forked_at_week")
        self._forked_at_week = int(fw) if fw is not None else None
        self._week_history = list(data.get("week_history") or [])
        gs = data.get("game_settings")
        if isinstance(gs, dict):
            self._settings = GameSettings.from_dict(gs)

        pend = data.get("current_week_pending") or {}
        self._weekly_slots = list(pend.get("weekly_slots") or [])
        self._handled_events = set(pend.get("handled_events") or [])
        self._week_reaction_lines = list(pend.get("week_reaction_lines") or [])
        self._current_week_reactions = list(pend.get("current_week_reactions") or [])
        self._event_descriptions = list(
            pend.get("event_descriptions")
            or [str(s.get("text", "")) for s in self._weekly_slots]
        )
        if not self._weekly_slots:
            self._resample_weekly_events()
        self._rebuild_week_summary()

    def _snapshot_trait_week_start(self) -> None:
        self._traits_at_week_start = dict(self._traits)

    def _simulated_years(self) -> float:
        ay = float(self._child.get("age_years", 0))
        cw = max(1, int(self._calendar_week))
        return ay + (cw - 1) / 52.0

    def _check_simulation_complete(self) -> None:
        if self._simulated_years() + 1e-9 < float(self._settings.simulation_length_years):
            return
        if self._sim_complete_shown:
            return
        self._sim_complete_shown = True

        def _toast() -> None:
            messagebox.showinfo(
                "Run length",
                f"Reached about {self._settings.simulation_length_years} simulated years (options). "
                "You can keep playing or save a snapshot.",
            )

        self.root.after(120, _toast)

    def _apply_skip_infant_toddler_if_enabled(self) -> None:
        if not self._settings.skip_years_zero_to_two:
            return
        ay = int(self._child.get("age_years", 0))
        if ay >= 3:
            return
        self._child["age_years"] = 3
        self._resample_weekly_events()
        self._snapshot_trait_week_start()
        self._stats_blurb = "Options: ages 0–2 skipped — child set to age 3 for faster play (placeholder)."

    def _on_save(self) -> None:
        slug = _safe_filename_slug(self._branch_label)
        initial = f"{slug}_w{self._calendar_week}.json"
        path_str = filedialog.asksaveasfilename(
            title="Save game",
            initialdir=str(self._save_dir),
            initialfile=initial,
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
        )
        if not path_str:
            return
        path = Path(path_str)
        payload = self._collect_save_payload()
        dump_save(payload, path)
        self._last_save_path = path
        messagebox.showinfo("Save", f"Saved branch state to:\n{path}")
        self.refresh_all()

    def _on_resume(self) -> None:
        path_str = filedialog.askopenfilename(
            title="Resume game",
            initialdir=str(self._save_dir),
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
        )
        if not path_str:
            return
        path = Path(path_str)
        try:
            data = load_save(path)
        except OSError as e:
            messagebox.showerror("Resume", str(e))
            return

        fork = messagebox.askyesno(
            "Resume",
            "Fork as a NEW branch experiment?\n\n"
            "Yes — duplicate state with a new branch id (compare outcomes).\n"
            "No — continue the same branch id from this file.",
        )
        if fork:
            label = simpledialog.askstring(
                "Branch label",
                "Name this fork:",
                initialvalue=f"{data.get('branch_label', 'run')}-fork",
            )
            if label is None:
                return
            data = fork_payload_from_loaded(data, new_label=label, parent_file_name=path.name)

        try:
            self._restore_save_payload(data)
        except ValueError as e:
            messagebox.showerror("Resume", str(e))
            return
        self._child = merge_child_stat_defaults(self._child)
        self._last_save_path = path if not fork else None
        self._update_title()
        self.refresh_all()

    def _compare_branches_dialog(self) -> None:
        paths = list_save_paths(self._save_dir)
        if len(paths) < 2:
            messagebox.showinfo(
                "Compare branches",
                "Need at least two .json saves in game/save/ to compare.",
            )
            return

        top = tk.Toplevel(self.root)
        top.title("Compare branch saves")
        top.minsize(560, 420)
        frm = ttk.Frame(top, padding=10)
        frm.pack(fill=tk.BOTH, expand=True)

        names = [p.name for p in paths]
        ttk.Label(frm, text="Save A:").grid(row=0, column=0, sticky=tk.W)
        cb_a = ttk.Combobox(frm, values=names, width=42, state="readonly")
        cb_a.grid(row=0, column=1, sticky=tk.EW)
        cb_a.current(0)

        ttk.Label(frm, text="Save B:").grid(row=1, column=0, sticky=tk.W)
        cb_b = ttk.Combobox(frm, values=names, width=42, state="readonly")
        cb_b.grid(row=1, column=1, sticky=tk.EW)
        cb_b.current(min(1, len(names) - 1))

        txt = tk.Text(frm, height=18, wrap=tk.WORD, font=theme.FONT_UI)
        ys = ttk.Scrollbar(frm, orient=tk.VERTICAL, command=txt.yview)
        txt.configure(yscrollcommand=ys.set)
        txt.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=(8, 0))
        ys.grid(row=3, column=2, sticky="ns")
        frm.rowconfigure(3, weight=1)
        frm.columnconfigure(1, weight=1)

        def run_compare() -> None:
            na, nb = cb_a.get(), cb_b.get()
            pa = self._save_dir / na
            pb = self._save_dir / nb
            try:
                a, b = load_save(pa), load_save(pb)
                body = format_branch_comparison(a, b)
            except OSError as e:
                messagebox.showerror("Compare", str(e))
                return
            txt.config(state=tk.NORMAL)
            txt.delete("1.0", tk.END)
            txt.insert("1.0", body)
            txt.config(state=tk.DISABLED)

        ttk.Button(frm, text="Compare", command=run_compare).grid(row=2, column=1, sticky=tk.E, pady=6)
        run_compare()

    def _resample_weekly_events(self) -> None:
        self._weekly_slots = sample_weekly_events(
            self._events_catalog,
            age_years=int(self._child.get("age_years", 8)),
            calendar_week=int(self._calendar_week),
            child_name=str(self._child.get("name", "Child")),
            rng=self._rng,
            max_events=3,
        )
        self._handled_events.clear()
        self._event_descriptions = [str(s.get("text", "")) for s in self._weekly_slots]

    def _rebuild_week_summary(self) -> None:
        name = str(self._child.get("name", "Child"))
        auto_note = self._narrative_auto_uneventful
        self._narrative_auto_uneventful = False

        head = (
            f"Week {self._calendar_week} — {name}. "
            f"Run target: {self._settings.simulation_length_years}y · "
            f"~{self._simulated_years():.1f}y on calendar (placeholder pacing)."
        )
        feedback = build_weekly_narrative_feedback(
            calendar_week=self._calendar_week,
            child_name=name,
            event_count=len(self._weekly_slots),
            reaction_lines_count=len(self._week_reaction_lines),
            traits_now=self._traits,
            traits_week_start=self._traits_at_week_start,
            simulation_target_years=self._settings.simulation_length_years,
            simulated_years_approx=self._simulated_years(),
            auto_uneventful_note=auto_note,
        )
        body = (
            "\n".join(self._week_reaction_lines)
            if self._week_reaction_lines
            else "No reactions logged yet this week."
        )
        parts = [head, "", "--- Placeholder narrative feedback ---", feedback, "", "--- This week's log ---", body]
        if self._settings.batch_early_years_stats and self._is_early_childhood():
            tail_weeks = [h for h in self._week_history[-10:] if isinstance(h, dict)]
            rx = sum(len(h.get("reactions") or []) for h in tail_weeks)
            parts.extend(
                [
                    "",
                    f"[Early-years batch line] Last {len(tail_weeks)} completed week(s): "
                    f"{rx} total reactions in window (placeholder rollup).",
                ]
            )
        self._summary_narrative = "\n".join(parts)

    def _advance_week(self) -> None:
        self._finalize_week_snapshot()
        self._calendar_week += 1
        self._debate_highlight = self._calendar_week % 5 == 0
        self._resample_weekly_events()
        self._snapshot_trait_week_start()
        self._rebuild_week_summary()
        self._stats_blurb = (
            f"Week {self._calendar_week}: drew {len(self._weekly_slots)} event(s) "
            "(0–3, age-matched). Traits carry over from prior choices."
        )
        self._check_simulation_complete()

    def _branch_lines(self) -> list[str]:
        forest = render_saved_branch_forest(
            self._save_dir,
            current_branch_id=self._branch_id,
            current_week=self._calendar_week,
            current_traits=self._traits,
            current_label=self._branch_label,
        )
        tail: list[str] = [
            "",
            "── Personality along this branch (after each completed week) ──",
        ]
        if not self._week_history:
            tail.append("  (no completed weeks yet on this branch)")
        else:
            for h in self._week_history[-20:]:
                tw = traits_compact(h.get("traits_end") or {})
                wk = h.get("calendar_week", "?")
                nar = str(h.get("narrative", "")).replace("\n", " ").strip()
                if len(nar) > 100:
                    nar = nar[:97] + "…"
                react_n = len(h.get("reactions") or [])
                tail.append(f"  W{wk}: {tw}  | {react_n} reaction(s)")
                if nar:
                    tail.append(f"      {nar}")
        return forest + tail

    def _build_top_bar(self, parent: ttk.Frame) -> None:
        bar = ttk.LabelFrame(parent, text="Child overview", padding=8)
        bar.pack(fill=tk.X, pady=(0, 8))
        grid = ttk.Frame(bar)
        grid.pack(fill=tk.X)

        placeholders = [
            ("name_lbl", "Child name", str(self._child.get("name", ""))),
            ("week_lbl", "Age / week", self._format_age_week()),
            ("gender_lbl", "Gender", str(self._child.get("gender", ""))),
            ("branch_lbl", "Branch", str(self._child.get("branch", ""))),
            ("temp_lbl", "Temperament", str(self._child.get("temperament", ""))),
        ]
        for col, (key, title, initial) in enumerate(placeholders):
            ttk.Label(grid, text=f"{title}:", font=theme.FONT_UI_HEADER).grid(
                row=0, column=col, sticky=tk.W, padx=(0, 12), pady=(0, 2)
            )
            lbl = ttk.Label(grid, text=initial)
            lbl.grid(row=1, column=col, sticky=tk.W, padx=(0, 16))
            self._top_labels[key] = lbl

        stat_placeholders = [
            ("intel_lbl", "Intelligence", str(self._child.get("intelligence", ""))),
            ("social_lbl", "Social", str(self._child.get("social_tendency", ""))),
            ("health_lbl", "Health", str(self._child.get("health", ""))),
            ("energy_lbl", "Energy", str(self._child.get("energy", ""))),
        ]
        for col, (key, title, initial) in enumerate(stat_placeholders):
            ttk.Label(grid, text=f"{title}:", font=theme.FONT_UI_HEADER).grid(
                row=2, column=col, sticky=tk.W, padx=(0, 12), pady=(8, 2)
            )
            lbl = ttk.Label(grid, text=initial)
            lbl.grid(row=3, column=col, sticky=tk.W, padx=(0, 16))
            self._top_labels[key] = lbl

    def _format_age_week(self) -> str:
        age = self._child.get("age_years", "?")
        return f"Age {age} · Week {self._calendar_week}"

    def _build_controls(self, parent: ttk.Frame) -> None:
        lf = ttk.LabelFrame(parent, text="Controls", padding=8)
        lf.pack(fill=tk.X)

        row = ttk.Frame(lf)
        row.pack(fill=tk.X)

        for label, cmd in [
            ("Save", self._on_save),
            ("Resume", self._on_resume),
            ("Compare saves", self._compare_branches_dialog),
            ("Next week", self._on_next_week),
            ("Auto week (<6)", self._on_auto_simulate_week),
            ("View branch tree", self._popup_branch_tree),
            ("Options", self._open_options),
        ]:
            ttk.Button(row, text=label, command=cmd).pack(side=tk.LEFT, padx=(0, 6), pady=4)

    def _open_options(self) -> None:
        if not show_options_dialog(self.root, self._settings):
            return
        self._apply_skip_infant_toddler_if_enabled()
        self._rebuild_week_summary()
        self._sync_branch_panel_visibility()
        self.refresh_all()

    def _schedule_auto_uneventful(self) -> None:
        if not self._settings.auto_simulate_uneventful_weeks:
            return
        if self._weekly_slots:
            self._uneventful_auto_chain = 0
            return
        if self._auto_advancing_uneventful:
            return
        if self._uneventful_auto_chain >= 52:
            return
        self._auto_advancing_uneventful = True
        self.root.after(40, self._step_auto_uneventful)

    def _step_auto_uneventful(self) -> None:
        self._auto_advancing_uneventful = False
        try:
            if not self._settings.auto_simulate_uneventful_weeks:
                return
            if self._weekly_slots:
                self._uneventful_auto_chain = 0
                return
            self._uneventful_auto_chain += 1
            self._narrative_auto_uneventful = True
            self._advance_week()
            self.refresh_all()
        except tk.TclError:
            pass

    def _on_next_week(self) -> None:
        self._narrative_auto_uneventful = False
        self._advance_week()
        self.refresh_all()

    def _is_early_childhood(self) -> bool:
        return int(self._child.get("age_years", 99)) < 6

    def _on_auto_simulate_week(self) -> None:
        if not self._is_early_childhood():
            messagebox.showinfo(
                "Auto week",
                "Auto-simulate is for ages under 6 only (early childhood batching).",
            )
            return
        if not self._weekly_slots:
            messagebox.showinfo("Auto week", "No events this week — try Next week.")
            return
        kinds = list(REACTION_KINDS)
        applied = 0
        for i in range(len(self._weekly_slots)):
            if i in self._handled_events:
                continue
            reaction = self._rng.choice(kinds)
            intensity = self._rng.randint(4, 9)
            self._apply_reaction(i, reaction, intensity, prefix="[Auto] ", refresh=False)
            applied += 1
        if applied == 0:
            messagebox.showinfo("Auto week", "All events were already handled this week.")
            self.refresh_all()
            return
        self._advance_week()
        self.refresh_all()

    def _on_event_reaction(self, event_index: int, reaction: str, intensity: int) -> None:
        self._apply_reaction(event_index, reaction, intensity)

    def _apply_reaction(
        self,
        event_index: int,
        reaction: str,
        intensity: int,
        *,
        prefix: str = "",
        refresh: bool = True,
    ) -> None:
        if event_index < 0 or event_index >= len(self._weekly_slots):
            return
        if event_index in self._handled_events:
            messagebox.showinfo(
                "Weekly events",
                "You already responded to this event this week.",
            )
            return
        if reaction not in REACTION_KINDS:
            return
        slot = self._weekly_slots[event_index]
        weights = slot.get("trait_weights") or {}
        deltas = trait_deltas(weights, reaction, intensity)
        self._traits = apply_trait_deltas(self._traits, deltas)
        self._handled_events.add(event_index)
        line = (
            f"{prefix}Event {event_index + 1}: {reaction} at intensity {intensity}. "
            f"{format_delta_line(deltas)}"
        )
        self._week_reaction_lines.append(line)
        self._current_week_reactions.append(
            {
                "event_index": event_index,
                "event_id": slot.get("id"),
                "event_text": slot.get("text"),
                "reaction": reaction,
                "intensity": intensity,
                "deltas": deltas,
                "line": line,
            }
        )
        self._rebuild_week_summary()
        self._stats_blurb = format_delta_line(deltas)
        if refresh:
            self.refresh_all()

    def _popup_branch_tree(self) -> None:
        top = tk.Toplevel(self.root)
        top.title("Branch tree — full view")
        top.minsize(640, 480)
        txt = tk.Text(top, font=theme.FONT_MONO, wrap=tk.NONE)
        ys = ttk.Scrollbar(top, orient=tk.VERTICAL, command=txt.yview)
        xs = ttk.Scrollbar(top, orient=tk.HORIZONTAL, command=txt.xview)
        txt.configure(yscrollcommand=ys.set, xscrollcommand=xs.set)
        txt.grid(row=0, column=0, sticky="nsew")
        ys.grid(row=0, column=1, sticky="ns")
        xs.grid(row=1, column=0, sticky="ew")
        top.rowconfigure(0, weight=1)
        top.columnconfigure(0, weight=1)
        body = "\n".join(self._branch_lines())
        txt.insert("1.0", body)
        txt.config(state=tk.DISABLED)

    def refresh_all(self) -> None:
        self._top_labels["name_lbl"].config(text=str(self._child.get("name", "")))
        self._top_labels["week_lbl"].config(text=self._format_age_week())
        self._top_labels["gender_lbl"].config(text=str(self._child.get("gender", "")))
        self._top_labels["branch_lbl"].config(text=str(self._child.get("branch", "")))
        self._top_labels["temp_lbl"].config(text=str(self._child.get("temperament", "")))
        self._top_labels["intel_lbl"].config(text=str(self._child.get("intelligence", "")))
        self._top_labels["social_lbl"].config(text=str(self._child.get("social_tendency", "")))
        self._top_labels["health_lbl"].config(text=str(self._child.get("health", "")))
        self._top_labels["energy_lbl"].config(text=str(self._child.get("energy", "")))

        if self._weekly_slots:
            self._uneventful_auto_chain = 0

        self._stats_panel.set_traits(self._traits, baseline=self._traits_at_week_start)
        self._events_panel.set_events(self._event_descriptions)
        self._summary_panel.set_content(self._summary_narrative, self._stats_blurb)
        self._branch_panel.set_lines(self._branch_lines())
        self.root.after_idle(self._schedule_auto_uneventful)

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    """Same entry as ``python -m game.main`` (new-game dialog + main window)."""
    from game.main import main as game_main

    game_main()


__all__ = ["GameMainWindow", "main"]
