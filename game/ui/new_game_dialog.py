"""New game setup: profile, start age (0 vs 3), gender, temperament, optional stats."""

from __future__ import annotations

import copy
import tkinter as tk
from tkinter import messagebox, ttk

from game.template_data import effective_new_game_age_and_week
from game.ui import theme

TEMPERAMENT_PRESETS: tuple[str, ...] = ("Calm", "Curious", "Shy", "Active")


def _profile_labels(profiles: list[dict]) -> list[str]:
    out: list[str] = []
    for p in profiles:
        pid = str(p.get("id", "?"))
        name = str(p.get("name", "Child"))
        out.append(f"{pid} — {name}")
    return out


def show_new_game_dialog(parent: tk.Misc, profiles: list[dict]) -> dict | None:
    """
    Modal new-game setup. Returns a dict with:
      template (deep copy), start_age_years (0 or 3), gender, temperament,
      and optional intelligence, social_tendency, health, energy (0–100) when set,
    or None if cancelled.

    Gender is stored as ``Boy`` / ``Girl`` for compatibility with child templates.
    """
    if not profiles:
        return None

    top = tk.Toplevel(parent)
    top.title("New game")
    # Do not call transient(parent) when parent is withdrawn: on Windows the dialog
    # often never appears or stays unusably tied to a hidden root.
    top.grab_set()
    top.minsize(460, 620)

    result: dict | None = None

    frm = ttk.Frame(top, padding=12)
    frm.pack(fill=tk.BOTH, expand=True)

    ttk.Label(frm, text="Start a new run", font=theme.FONT_UI_HEADER).grid(
        row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 8)
    )

    labels = _profile_labels(profiles)
    ttk.Label(frm, text="Profile template:", font=theme.FONT_UI_HEADER).grid(
        row=1, column=0, sticky=tk.NW, pady=4
    )
    profile_var = tk.StringVar(value=labels[0])
    profile_cb = ttk.Combobox(frm, textvariable=profile_var, values=labels, state="readonly", width=42)
    profile_cb.grid(row=1, column=1, sticky=tk.EW, pady=4)

    ttk.Label(frm, text="Start age:", font=theme.FONT_UI_HEADER).grid(row=2, column=0, sticky=tk.NW, pady=(12, 4))
    age_fr = ttk.Frame(frm)
    age_fr.grid(row=2, column=1, sticky=tk.EW, pady=(12, 4))
    start_age_var = tk.IntVar(value=0)
    ttk.Radiobutton(age_fr, text="Birth (age 0)", variable=start_age_var, value=0).pack(anchor=tk.W)
    ttk.Radiobutton(age_fr, text="Skip infancy (age 3)", variable=start_age_var, value=3).pack(anchor=tk.W)
    age_effect_hint = ttk.Label(
        age_fr,
        text="",
        wraplength=400,
        foreground=theme.COLOR_NEUTRAL,
        justify=tk.LEFT,
    )
    age_effect_hint.pack(anchor=tk.W, pady=(8, 0))

    def refresh_age_effect_hint(*_a: object) -> None:
        try:
            ix = labels.index(profile_var.get())
        except ValueError:
            ix = 0
        tpl = profiles[ix]
        chosen = int(start_age_var.get())
        eff_age, eff_cw, over = effective_new_game_age_and_week(
            tpl, start_age_years=chosen, calendar_week_fallback=1
        )
        try:
            ta = int(tpl.get("age_years", 0))
        except (TypeError, ValueError):
            ta = 0
        if over:
            age_effect_hint.config(
                text=(
                    f"Template age is {ta} (above your start-age choice {chosen}); "
                    f"the run begins at age {eff_age}, calendar week {eff_cw}. "
                    "Other template fields (traits, branch, optional stats) stay on the profile."
                )
            )
        else:
            age_effect_hint.config(
                text=(
                    f"Resolved start: age {eff_age}, calendar week {eff_cw}. "
                    "(Choosing skip-infancy uses week 1 unless the template age overrides.)"
                )
            )

    profile_cb.bind("<<ComboboxSelected>>", refresh_age_effect_hint)
    start_age_var.trace_add("write", lambda *_: refresh_age_effect_hint())

    ttk.Label(frm, text="Gender:", font=theme.FONT_UI_HEADER).grid(row=3, column=0, sticky=tk.NW, pady=4)
    gender_fr = ttk.Frame(frm)
    gender_fr.grid(row=3, column=1, sticky=tk.W, pady=4)
    gender_var = tk.StringVar(value="Boy")
    ttk.Radiobutton(gender_fr, text="Male (Boy)", variable=gender_var, value="Boy").pack(side=tk.LEFT, padx=(0, 12))
    ttk.Radiobutton(gender_fr, text="Female (Girl)", variable=gender_var, value="Girl").pack(side=tk.LEFT)

    ttk.Label(frm, text="Temperament:", font=theme.FONT_UI_HEADER).grid(row=4, column=0, sticky=tk.NW, pady=4)
    temp_fr = ttk.Frame(frm)
    temp_fr.grid(row=4, column=1, sticky=tk.W, pady=4)
    temperament_var = tk.StringVar(value=TEMPERAMENT_PRESETS[0])
    for i, tlabel in enumerate(TEMPERAMENT_PRESETS):
        ttk.Radiobutton(temp_fr, text=tlabel, variable=temperament_var, value=tlabel).grid(
            row=i // 2, column=i % 2, sticky=tk.W, padx=(0, 16), pady=2
        )

    ttk.Label(frm, text="Starting stats (optional, 0–100):", font=theme.FONT_UI_HEADER).grid(
        row=5, column=0, columnspan=2, sticky=tk.W, pady=(12, 4)
    )
    stat_grid = ttk.Frame(frm)
    stat_grid.grid(row=6, column=0, columnspan=2, sticky=tk.EW)
    intel_e = ttk.Entry(stat_grid, width=8)
    social_e = ttk.Entry(stat_grid, width=8)
    health_e = ttk.Entry(stat_grid, width=8)
    energy_e = ttk.Entry(stat_grid, width=8)
    for col, (title, w) in enumerate(
        [
            ("Intelligence", intel_e),
            ("Social tendency", social_e),
            ("Health", health_e),
            ("Energy", energy_e),
        ]
    ):
        ttk.Label(stat_grid, text=f"{title}:").grid(row=0, column=col * 2, sticky=tk.W, padx=(0, 4), pady=2)
        w.grid(row=0, column=col * 2 + 1, sticky=tk.W, padx=(0, 12), pady=2)

    hint = ttk.Label(
        frm,
        text=(
            "Templates carry baseline traits, branch flavor, optional stats, and an age_years field. "
            "Birth vs skip-infancy normally sets 0 or 3; if template age_years is greater than that choice, "
            "the template age (and its calendar week when present) wins. "
            "Gender and temperament are chosen here for this run. "
            "Leave stat boxes empty to keep template defaults."
        ),
        wraplength=400,
        foreground=theme.COLOR_NEUTRAL,
    )
    hint.grid(row=7, column=0, columnspan=2, sticky=tk.W, pady=(12, 8))

    frm.columnconfigure(1, weight=1)

    btn_row = ttk.Frame(frm)
    btn_row.grid(row=8, column=0, columnspan=2, sticky=tk.E, pady=(8, 0))

    def _parse_optional_stat(raw: str, label: str) -> int | None:
        s = raw.strip()
        if not s:
            return None
        try:
            v = int(s)
        except ValueError:
            raise ValueError(f"{label} must be a whole number (0–100).") from None
        if v < 0 or v > 100:
            raise ValueError(f"{label} must be between 0 and 100.")
        return v

    def on_ok() -> None:
        nonlocal result
        try:
            o_intel = _parse_optional_stat(intel_e.get(), "Intelligence")
            o_social = _parse_optional_stat(social_e.get(), "Social tendency")
            o_health = _parse_optional_stat(health_e.get(), "Health")
            o_energy = _parse_optional_stat(energy_e.get(), "Energy")
        except ValueError as e:
            messagebox.showerror("New game", str(e), parent=top)
            return

        try:
            idx = labels.index(profile_var.get())
        except ValueError:
            idx = 0
        out: dict = {
            "template": copy.deepcopy(profiles[idx]),
            "start_age_years": int(start_age_var.get()),
            "gender": gender_var.get().strip(),
            "temperament": temperament_var.get().strip(),
        }
        if o_intel is not None:
            out["intelligence"] = o_intel
        if o_social is not None:
            out["social_tendency"] = o_social
        if o_health is not None:
            out["health"] = o_health
        if o_energy is not None:
            out["energy"] = o_energy
        result = out
        top.destroy()

    def on_cancel() -> None:
        top.destroy()

    ttk.Button(btn_row, text="Cancel", command=on_cancel).pack(side=tk.RIGHT, padx=(6, 0))
    ttk.Button(btn_row, text="Start", command=on_ok).pack(side=tk.RIGHT)

    top.protocol("WM_DELETE_WINDOW", on_cancel)
    top.update_idletasks()
    top.lift()
    top.focus_force()

    refresh_age_effect_hint()
    parent.wait_window(top)
    return result
