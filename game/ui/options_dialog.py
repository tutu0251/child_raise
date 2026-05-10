"""Modal options editor for simulation usability."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from game.settings import GameSettings
from game.ui import theme


def show_options_dialog(parent: tk.Misc, settings: GameSettings) -> bool:
    """
    Edit ``settings`` in place.
    Returns True if user clicked Save, False if cancelled.
    """
    top = tk.Toplevel(parent)
    top.title("Options")
    top.transient(parent)
    top.grab_set()
    top.minsize(420, 310)

    result = {"ok": False}

    frm = ttk.Frame(top, padding=12)
    frm.pack(fill=tk.BOTH, expand=True)

    ttk.Label(
        frm,
        text="Usability (core trait math unchanged)",
        font=theme.FONT_UI_HEADER,
    ).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 8))

    skip_var = tk.BooleanVar(value=settings.skip_years_zero_to_two)
    auto_var = tk.BooleanVar(value=settings.auto_simulate_uneventful_weeks)
    batch_var = tk.BooleanVar(value=settings.batch_early_years_stats)
    branch_panel_var = tk.BooleanVar(value=settings.show_branch_timeline_panel)

    ttk.Checkbutton(
        frm,
        text="Skip ages 0–2 (jump child to age 3 on apply — faster starts)",
        variable=skip_var,
    ).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=2)

    ttk.Checkbutton(
        frm,
        text="Auto-advance weeks with zero events (responsive single-step ticks)",
        variable=auto_var,
    ).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=2)

    ttk.Checkbutton(
        frm,
        text="Batch early-years stats line in summary (ages under 6)",
        variable=batch_var,
    ).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=2)

    ttk.Checkbutton(
        frm,
        text="Show branch timeline panel (sidebar — full tree stays in View branch tree)",
        variable=branch_panel_var,
    ).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=2)

    ttk.Label(frm, text="Simulation length:", font=theme.FONT_UI_HEADER).grid(
        row=5, column=0, sticky=tk.W, pady=(12, 4)
    )
    len_var = tk.IntVar(value=settings.simulation_length_years)
    rf = ttk.Frame(frm)
    rf.grid(row=6, column=0, columnspan=2, sticky=tk.W)
    for years in (16, 18):
        ttk.Radiobutton(rf, text=f"{years} years", variable=len_var, value=years).pack(
            side=tk.LEFT, padx=(0, 16)
        )

    hint = ttk.Label(
        frm,
        text=(
            "Uneventful auto-advance caps after many empty weeks to keep the UI responsive. "
            "Skip 0–2 applies once when you save options if the child is below age 3."
        ),
        wraplength=400,
        foreground=theme.COLOR_NEUTRAL,
    )
    hint.grid(row=7, column=0, columnspan=2, sticky=tk.W, pady=(12, 8))

    btn_row = ttk.Frame(frm)
    btn_row.grid(row=8, column=0, columnspan=2, sticky=tk.E)

    def on_ok() -> None:
        settings.skip_years_zero_to_two = skip_var.get()
        settings.auto_simulate_uneventful_weeks = auto_var.get()
        settings.batch_early_years_stats = batch_var.get()
        settings.show_branch_timeline_panel = branch_panel_var.get()
        ly = len_var.get()
        settings.simulation_length_years = 18 if ly != 16 else 16
        settings.__post_init__()
        result["ok"] = True
        top.destroy()

    def on_cancel() -> None:
        top.destroy()

    ttk.Button(btn_row, text="Cancel", command=on_cancel).pack(side=tk.RIGHT, padx=(6, 0))
    ttk.Button(btn_row, text="Save options", command=on_ok).pack(side=tk.RIGHT)

    top.protocol("WM_DELETE_WINDOW", on_cancel)
    parent.wait_window(top)
    return bool(result["ok"])
