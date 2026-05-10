"""Tkinter shell for the GUI mockup — layout and interactions only.

Game logic stays in `game/`; this module binds widgets to `mockup.mock_*` adapters.
For reuse: swap session/update callbacks for real `game` models (see `game/PLAN.md`)."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from mockup.mock_early_years import format_early_years_batch
from mockup.mock_branch_tree import build_branch_lines
from mockup.mock_constants import MOCK_CHILD, MOCK_EVENTS, MOCK_TRAITS_ORDER
from mockup.mock_session import (
    MockSession,
    apply_mock_choice,
    auto_simulate_weeks,
    build_summary,
    display_week,
    initial_traits,
    mock_uneventful_week,
)
from mockup.ui import gui_theme as theme


def _trait_order_names() -> list[str]:
    return [name for name, _ in MOCK_TRAITS_ORDER]


class MockupGuiApp:
    """Mock-specific window; a future `game.ui` can mirror this layout with real state."""

    def __init__(self) -> None:
        self.session = MockSession(traits=initial_traits())
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title(theme.WINDOW_TITLE_MOCKUP)
        self.root.minsize(*theme.WINDOW_MIN_SIZE)

        self._event_var = tk.IntVar(value=0)
        self._top_labels: dict[str, ttk.Label] = {}
        self._trait_rows: dict[str, tuple[ttk.Progressbar, ttk.Label, tk.Label, tk.Label]] = {}
        self._summary_text: tk.Text | None = None
        self._branch_text: tk.Text | None = None
        self._early_years_text: tk.Text | None = None

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

        self._build_personality_panel(left_inner)
        self._build_early_years_panel(left_inner)
        self._build_weekly_events_panel(left_inner)
        self._build_controls_panel(left_inner)

        self._build_weekly_summary_panel(right_col)
        self._build_branch_panel(right_col)

        self.refresh_all()

        self.root.update_idletasks()
        self.root.deiconify()

    def _build_top_bar(self, parent: ttk.Frame) -> None:
        bar = ttk.LabelFrame(parent, text="Child overview", padding=8)
        bar.pack(fill=tk.X, pady=(0, 8))
        grid = ttk.Frame(bar)
        grid.pack(fill=tk.X)

        fields = [
            ("name_lbl", "Name", MOCK_CHILD["name"]),
            ("week_lbl", "Age / week", ""),
            ("gender_lbl", "Gender", MOCK_CHILD["gender"]),
            ("branch_lbl", "Branch", MOCK_CHILD["branch"]),
            ("temp_lbl", "Temperament", MOCK_CHILD["temperament"]),
        ]
        for col, (key, title, initial) in enumerate(fields):
            ttk.Label(grid, text=f"{title}:", font=theme.FONT_UI_HEADER).grid(
                row=0, column=col, sticky=tk.W, padx=(0, 12), pady=(0, 2)
            )
            lbl = ttk.Label(grid, text=initial)
            lbl.grid(row=1, column=col, sticky=tk.W, padx=(0, 16))
            self._top_labels[key] = lbl

    def _build_personality_panel(self, parent: ttk.Frame) -> None:
        lf = ttk.LabelFrame(parent, text="Personality stats (placeholders)", padding=8)
        lf.pack(fill=tk.X, pady=(0, 8))

        hint = ttk.Label(
            lf,
            text=(
                "Big Five + resilience, independence, risk-taking — demo only. "
                "Trend vs prior snapshot (↑ / ↓ / →); Δ is the last mock increment."
            ),
            wraplength=700,
        )
        hint.pack(anchor=tk.W, pady=(0, 6))

        inner = ttk.Frame(lf)
        inner.pack(fill=tk.X)
        ttk.Label(inner, text="", width=18).grid(row=0, column=0)
        ttk.Label(inner, text="", width=28).grid(row=0, column=1)
        ttk.Label(inner, text="Value", width=9, anchor=tk.E, font=theme.FONT_UI_HEADER).grid(
            row=0, column=2, sticky=tk.E, pady=(0, 4)
        )
        ttk.Label(inner, text="Trend", width=6, anchor=tk.CENTER, font=theme.FONT_UI_HEADER).grid(
            row=0, column=3, pady=(0, 4)
        )
        ttk.Label(inner, text="Δ", width=5, anchor=tk.CENTER, font=theme.FONT_UI_HEADER).grid(
            row=0, column=4, pady=(0, 4)
        )

        for row, (name, _) in enumerate(MOCK_TRAITS_ORDER, start=1):
            ttk.Label(inner, text=f"{name}:", width=18, anchor=tk.W).grid(
                row=row, column=0, sticky=tk.W, pady=2
            )
            bar = ttk.Progressbar(inner, maximum=100, length=240, mode="determinate")
            bar.grid(row=row, column=1, sticky=tk.W, padx=(0, 8), pady=2)
            val = ttk.Label(inner, text="0/100", width=9, anchor=tk.E)
            val.grid(row=row, column=2, sticky=tk.E, pady=2)
            trend_lbl = tk.Label(
                inner, text="—", width=5, anchor=tk.CENTER, fg=theme.COLOR_NEUTRAL
            )
            trend_lbl.grid(row=row, column=3, pady=2)
            delta_lbl = tk.Label(
                inner, text="—", width=5, anchor=tk.CENTER, fg=theme.COLOR_NEUTRAL
            )
            delta_lbl.grid(row=row, column=4, sticky=tk.E, pady=2)
            self._trait_rows[name] = (bar, val, trend_lbl, delta_lbl)

    def _build_early_years_panel(self, parent: ttk.Frame) -> None:
        lf = ttk.LabelFrame(parent, text="Early years — mock batch stats", padding=8)
        lf.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(
            lf,
            text="Cumulative positive trait bumps since session start (placeholder summary).",
            wraplength=700,
        ).pack(anchor=tk.W, pady=(0, 6))
        self._early_years_text = tk.Text(lf, height=8, wrap=tk.WORD, font=theme.FONT_UI)
        self._early_years_text.pack(fill=tk.X)

    def _build_weekly_events_panel(self, parent: ttk.Frame) -> None:
        lf = ttk.LabelFrame(parent, text="Weekly events", padding=8)
        lf.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(
            lf,
            text="Step 1 — Select one situation. Step 2 — Choose how you responded (mock wiring).",
            wraplength=700,
        ).pack(anchor=tk.W, pady=(0, 8))

        choices = ttk.Frame(lf)
        choices.pack(fill=tk.X)

        for i, desc in enumerate(MOCK_EVENTS, start=1):
            row = ttk.Frame(choices)
            row.pack(fill=tk.X, pady=(0, 4))
            ttk.Radiobutton(
                row,
                text=f"Event {i}",
                variable=self._event_var,
                value=i,
                command=self._on_event_pick,
            ).pack(side=tk.LEFT, padx=(0, 8))
            ttk.Label(row, text=desc, wraplength=600).pack(side=tk.LEFT, fill=tk.X, expand=True)

        self._event_status = ttk.Label(lf, text=self._event_status_text())
        self._event_status.pack(anchor=tk.W, pady=(8, 4))

        react_lf = ttk.LabelFrame(lf, text="Reactions (apply to selected event)", padding=6)
        react_lf.pack(fill=tk.X, pady=(4, 0))
        btn_row = ttk.Frame(react_lf)
        btn_row.pack(fill=tk.X)
        for code in ("A", "B", "C"):
            label = theme.REACTION_LABELS[code]
            ttk.Button(
                btn_row,
                text=f"{code}: {label}",
                command=lambda c=code: self._on_reaction(c),
            ).pack(side=tk.LEFT, padx=(0, 6))

    def _build_weekly_summary_panel(self, parent: ttk.Frame) -> None:
        lf = ttk.LabelFrame(parent, text="Weekly summary", padding=8)
        lf.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        self._summary_text = tk.Text(lf, height=10, wrap=tk.WORD, font=theme.FONT_UI)
        self._summary_text.pack(fill=tk.BOTH, expand=True)

    def _build_branch_panel(self, parent: ttk.Frame) -> None:
        lf = ttk.LabelFrame(parent, text="Branch tree (ASCII)", padding=8)
        lf.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        self._branch_text = tk.Text(lf, height=14, wrap=tk.NONE, font=theme.FONT_MONO)
        bx = ttk.Scrollbar(lf, orient=tk.HORIZONTAL, command=self._branch_text.xview)
        by = ttk.Scrollbar(lf, orient=tk.VERTICAL, command=self._branch_text.yview)
        self._branch_text.configure(xscrollcommand=bx.set, yscrollcommand=by.set)
        self._branch_text.grid(row=0, column=0, sticky="nsew")
        by.grid(row=0, column=1, sticky="ns")
        bx.grid(row=1, column=0, sticky="ew")
        lf.rowconfigure(0, weight=1)
        lf.columnconfigure(0, weight=1)

    def _build_controls_panel(self, parent: ttk.Frame) -> None:
        lf = ttk.LabelFrame(parent, text="Controls", padding=8)
        lf.pack(fill=tk.X)

        row_a = ttk.Frame(lf)
        row_a.pack(fill=tk.X)
        row_b = ttk.Frame(lf)
        row_b.pack(fill=tk.X)

        for label, cmd in [
            ("Save", self._stub_save),
            ("Resume", self._stub_resume),
            ("Branch", self._stub_branch),
        ]:
            ttk.Button(row_a, text=label, command=cmd).pack(side=tk.LEFT, padx=(0, 6), pady=4)

        for label, cmd in [
            ("Next week (calm)", self._on_next_week),
            ("Noisy demo week", self._on_noisy_week),
            ("View branch tree", self._popup_branch_tree),
            ("Options", self._stub_options),
        ]:
            ttk.Button(row_b, text=label, command=cmd).pack(side=tk.LEFT, padx=(0, 6), pady=4)

    def _stub_save(self) -> None:
        messagebox.showinfo("Save", "Placeholder — no persistence in this mockup.")

    def _stub_resume(self) -> None:
        messagebox.showinfo("Resume", "Placeholder — nothing to load in this mockup.")

    def _stub_branch(self) -> None:
        messagebox.showinfo("Branch", "Placeholder — branch actions not wired in mockup.")

    def _stub_options(self) -> None:
        messagebox.showinfo("Options", "Placeholder settings panel.")

    def _on_next_week(self) -> None:
        mock_uneventful_week(self.session)
        self.session.summary = build_summary(self.session)
        self.refresh_all()

    def _on_noisy_week(self) -> None:
        auto_simulate_weeks(self.session, 1)
        self.session.summary = build_summary(self.session)
        self.refresh_all()

    def _event_status_text(self) -> str:
        ev = self._event_var.get()
        if ev in (1, 2, 3):
            return f"Selected: Event {ev} — choose a reaction below."
        return "No event selected — pick a radio button above."

    def _on_event_pick(self) -> None:
        self._event_status.config(text=self._event_status_text())

    def _on_reaction(self, reaction: str) -> None:
        ev = self._event_var.get()
        if ev not in (1, 2, 3):
            messagebox.showinfo(
                "Weekly events",
                "Select an event first (use the radio buttons next to each situation).",
            )
            return
        apply_mock_choice(self.session, ev, reaction)
        self.session.summary = build_summary(self.session)
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
        body = "\n".join(build_branch_lines(self.session))
        txt.insert("1.0", body)
        txt.config(state=tk.DISABLED)

    def _personality_updates_blurb(self) -> str:
        if self.session.last_deltas:
            parts = [f"• {k}: {v:+d}" for k, v in sorted(self.session.last_deltas.items())]
            return "Trait deltas (demo):\n" + "\n".join(parts)
        return "No personality deltas recorded yet — pick an event reaction or advance a week."

    def refresh_all(self) -> None:
        week = display_week(self.session)
        self._top_labels["week_lbl"].config(text=f"Week {week} (mock calendar)")
        self._top_labels["name_lbl"].config(text=str(MOCK_CHILD["name"]))
        self._top_labels["gender_lbl"].config(text=str(MOCK_CHILD["gender"]))
        self._top_labels["branch_lbl"].config(text=str(MOCK_CHILD["branch"]))
        self._top_labels["temp_lbl"].config(text=str(MOCK_CHILD["temperament"]))

        deltas = self.session.last_deltas or {}
        prev = self.session.trait_previous
        up, down, flat = "\u2191", "\u2193", "\u2192"
        for name in _trait_order_names():
            bar, val_lbl, trend_lbl, delta_lbl = self._trait_rows[name]
            v = self.session.traits[name]
            bar["value"] = v
            val_lbl.config(text=f"{v} / 100")
            if prev is None or name not in prev:
                trend_lbl.config(text="—", fg=theme.COLOR_NEUTRAL)
            else:
                diff = v - prev[name]
                if diff > 0:
                    trend_lbl.config(text=up, fg=theme.COLOR_POSITIVE)
                elif diff < 0:
                    trend_lbl.config(text=down, fg=theme.COLOR_NEGATIVE)
                else:
                    trend_lbl.config(text=flat, fg=theme.COLOR_NEUTRAL)
            if name in deltas:
                d = deltas[name]
                delta_lbl.config(
                    text=f"{d:+d}",
                    fg=theme.COLOR_POSITIVE if d > 0 else theme.COLOR_NEGATIVE,
                )
            else:
                delta_lbl.config(text="—", fg=theme.COLOR_NEUTRAL)

        if self._early_years_text:
            self._early_years_text.config(state=tk.NORMAL)
            self._early_years_text.delete("1.0", tk.END)
            self._early_years_text.insert("1.0", format_early_years_batch(self.session))
            self._early_years_text.config(state=tk.DISABLED)

        if self._summary_text:
            self._summary_text.config(state=tk.NORMAL)
            self._summary_text.delete("1.0", tk.END)
            self._summary_text.insert(tk.END, self.session.summary.strip())
            self._summary_text.insert(tk.END, "\n\n")
            self._summary_text.insert(tk.END, "--- Personality updates (placeholder) ---\n", "hdr")
            self._summary_text.insert(tk.END, self._personality_updates_blurb())
            self._summary_text.tag_configure("hdr", font=(theme.FONT_UI[0], theme.FONT_UI[1], "italic"))
            self._summary_text.config(state=tk.DISABLED)

        if self._branch_text:
            self._branch_text.config(state=tk.NORMAL)
            self._branch_text.delete("1.0", tk.END)
            self._branch_text.insert("1.0", "\n".join(build_branch_lines(self.session)))
            self._branch_text.config(state=tk.DISABLED)


def main() -> None:
    app = MockupGuiApp()
    app.root.mainloop()


__all__ = ["MockupGuiApp", "main"]
