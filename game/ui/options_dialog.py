"""Modal options editor for simulation usability."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from game.settings import AUTO_PLAY_REACTION_MODES, GameSettings
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
    top.minsize(440, 720)

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
    ff_batch_var = tk.BooleanVar(value=settings.auto_play_batch_summaries)
    ff_hi_var = tk.BooleanVar(value=settings.auto_play_collect_highlights)

    ttk.Checkbutton(
        frm,
        text="Jump to age 3 without simulating 0–2",
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

    ttk.Label(frm, text="Auto-play / fast-forward:", font=theme.FONT_UI_HEADER).grid(
        row=7, column=0, columnspan=2, sticky=tk.W, pady=(12, 4)
    )
    mode_var = tk.StringVar(
        value=settings.auto_play_reaction_mode
        if settings.auto_play_reaction_mode in AUTO_PLAY_REACTION_MODES
        else "random"
    )
    mf = ttk.Frame(frm)
    mf.grid(row=8, column=0, columnspan=2, sticky=tk.W)
    for m in AUTO_PLAY_REACTION_MODES:
        ttk.Radiobutton(
            mf,
            text={
                "random": "Random reactions",
                "neutral": "Neutral (Guide or Encourage, intensity 5)",
                "guide": "Always Guide",
                "encourage": "Always Encourage",
            }[m],
            variable=mode_var,
            value=m,
        ).pack(anchor=tk.W)

    ttk.Label(frm, text="Auto-play intensity (0–10):", font=theme.FONT_UI_HEADER).grid(
        row=9, column=0, sticky=tk.W, pady=(8, 2)
    )
    int_row = ttk.Frame(frm)
    int_row.grid(row=10, column=0, columnspan=2, sticky=tk.W)
    ttk.Label(int_row, text="Min").pack(side=tk.LEFT)
    int_min_var = tk.IntVar(value=settings.auto_play_intensity_min)
    int_max_var = tk.IntVar(value=settings.auto_play_intensity_max)
    ttk.Spinbox(int_row, from_=0, to=10, textvariable=int_min_var, width=5).pack(
        side=tk.LEFT, padx=(4, 12)
    )
    ttk.Label(int_row, text="Max").pack(side=tk.LEFT)
    ttk.Spinbox(int_row, from_=0, to=10, textvariable=int_max_var, width=5).pack(side=tk.LEFT, padx=(4, 0))

    summary_n_var = tk.IntVar(value=int(settings.auto_play_summary_every_n_weeks))
    ttk.Label(frm, text="Auto-play milestone summary every N weeks (0 = off):").grid(
        row=11, column=0, columnspan=2, sticky=tk.W, pady=(8, 2)
    )
    ttk.Spinbox(frm, from_=0, to=520, textvariable=summary_n_var, width=8).grid(
        row=12, column=0, sticky=tk.W
    )

    ttk.Checkbutton(
        frm,
        text="Fast-forward: batch summaries (compact panel + trait rollups; ages in band below)",
        variable=ff_batch_var,
    ).grid(row=13, column=0, columnspan=2, sticky=tk.W, pady=(10, 2))

    ttk.Checkbutton(
        frm,
        text="Fast-forward: collect key events (milestones, rare templates, large trait shifts)",
        variable=ff_hi_var,
    ).grid(row=14, column=0, columnspan=2, sticky=tk.W, pady=2)

    early_w_var = tk.IntVar(value=int(settings.auto_play_batch_weeks_early))
    later_w_var = tk.IntVar(value=int(settings.auto_play_batch_weeks_later))
    major_d_var = tk.IntVar(value=int(settings.auto_play_major_trait_delta))

    ttk.Label(frm, text="Batch window: simulated age low / high (years, early band):").grid(
        row=15, column=0, columnspan=2, sticky=tk.W, pady=(6, 2)
    )
    age_band = ttk.Frame(frm)
    age_band.grid(row=16, column=0, columnspan=2, sticky=tk.W)
    age_lo_var = tk.DoubleVar(value=float(settings.auto_play_early_batch_age_lo))
    age_hi_var = tk.DoubleVar(value=float(settings.auto_play_early_batch_age_hi))
    ttk.Label(age_band, text="Low").pack(side=tk.LEFT)
    ttk.Spinbox(age_band, from_=0.0, to=18.0, increment=0.5, textvariable=age_lo_var, width=6).pack(
        side=tk.LEFT, padx=(4, 12)
    )
    ttk.Label(age_band, text="High").pack(side=tk.LEFT)
    ttk.Spinbox(age_band, from_=0.0, to=18.0, increment=0.5, textvariable=age_hi_var, width=6).pack(
        side=tk.LEFT, padx=(4, 0)
    )

    ttk.Label(frm, text="Weeks per batch summary: early band / later ages (0 = later off):").grid(
        row=17, column=0, columnspan=2, sticky=tk.W, pady=(6, 2)
    )
    bw = ttk.Frame(frm)
    bw.grid(row=18, column=0, columnspan=2, sticky=tk.W)
    ttk.Label(bw, text="Early").pack(side=tk.LEFT)
    ttk.Spinbox(bw, from_=1, to=520, textvariable=early_w_var, width=7).pack(side=tk.LEFT, padx=(4, 12))
    ttk.Label(bw, text="Later").pack(side=tk.LEFT)
    ttk.Spinbox(bw, from_=0, to=520, textvariable=later_w_var, width=7).pack(side=tk.LEFT, padx=(4, 12))
    ttk.Label(bw, text="Major |Δtrait|").pack(side=tk.LEFT)
    ttk.Spinbox(bw, from_=1, to=50, textvariable=major_d_var, width=5).pack(side=tk.LEFT, padx=(4, 0))

    fixed_batch_var = tk.IntVar(value=int(settings.auto_play_fixed_batch_weeks))
    ttk.Label(frm, text="Fixed batch every N weeks (0 = use age bands only):").grid(
        row=19, column=0, columnspan=2, sticky=tk.W, pady=(8, 2)
    )
    ttk.Spinbox(frm, from_=0, to=520, textvariable=fixed_batch_var, width=8).grid(
        row=20, column=0, sticky=tk.W
    )

    sig_delta_var = tk.IntVar(value=int(settings.auto_play_significant_trait_delta))
    ttk.Label(frm, text="Highlight trait shift when per-event max |Δtrait| ≥:").grid(
        row=21, column=0, columnspan=2, sticky=tk.W, pady=(8, 2)
    )
    ttk.Spinbox(frm, from_=1, to=50, textvariable=sig_delta_var, width=8).grid(
        row=22, column=0, sticky=tk.W
    )

    hint = ttk.Label(
        frm,
        text=(
            "Uneventful auto-advance caps after many empty weeks to keep the UI responsive. "
            "Skip 0–2 applies once when you save options if the child is below age 3. "
            "Fast-forward uses the auto-play reaction mode and intensity above. "
            "Fixed batch N weeks overrides early/later band sizes when N > 0 (e.g. 4, 8, 12). "
            "Mark rare events in JSON with \"rarity\": \"rare\" on an event template."
        ),
        wraplength=400,
        foreground=theme.COLOR_NEUTRAL,
    )
    hint.grid(row=23, column=0, columnspan=2, sticky=tk.W, pady=(12, 8))

    btn_row = ttk.Frame(frm)
    btn_row.grid(row=24, column=0, columnspan=2, sticky=tk.E)

    def on_ok() -> None:
        settings.skip_years_zero_to_two = skip_var.get()
        settings.auto_simulate_uneventful_weeks = auto_var.get()
        settings.batch_early_years_stats = batch_var.get()
        settings.show_branch_timeline_panel = branch_panel_var.get()
        ly = len_var.get()
        settings.simulation_length_years = 18 if ly != 16 else 16
        settings.auto_play_reaction_mode = mode_var.get()
        settings.auto_play_intensity_min = int(int_min_var.get())
        settings.auto_play_intensity_max = int(int_max_var.get())
        settings.auto_play_summary_every_n_weeks = int(summary_n_var.get())
        settings.auto_play_batch_summaries = ff_batch_var.get()
        settings.auto_play_collect_highlights = ff_hi_var.get()
        settings.auto_play_early_batch_age_lo = float(age_lo_var.get())
        settings.auto_play_early_batch_age_hi = float(age_hi_var.get())
        settings.auto_play_batch_weeks_early = int(early_w_var.get())
        settings.auto_play_batch_weeks_later = int(later_w_var.get())
        settings.auto_play_major_trait_delta = int(major_d_var.get())
        settings.auto_play_fixed_batch_weeks = int(fixed_batch_var.get())
        settings.auto_play_significant_trait_delta = int(sig_delta_var.get())
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
