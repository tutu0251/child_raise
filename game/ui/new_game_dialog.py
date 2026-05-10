"""New game setup: profile, start age (0 vs 3), gender, temperament, optional stats."""

from __future__ import annotations

import copy
import tkinter as tk
from tkinter import messagebox, ttk

from game.ui import theme


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
    """
    if not profiles:
        return None

    top = tk.Toplevel(parent)
    top.title("New game")
    # Do not call transient(parent) when parent is withdrawn: on Windows the dialog
    # often never appears or stays unusably tied to a hidden root.
    top.grab_set()
    top.minsize(440, 520)

    result: dict | None = None

    frm = ttk.Frame(top, padding=12)
    frm.pack(fill=tk.BOTH, expand=True)

    ttk.Label(frm, text="Start a new run", font=theme.FONT_UI_HEADER).grid(
        row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 8)
    )

    labels = _profile_labels(profiles)
    ttk.Label(frm, text="Profile:", font=theme.FONT_UI_HEADER).grid(row=1, column=0, sticky=tk.NW, pady=4)
    profile_var = tk.StringVar(value=labels[0])
    profile_cb = ttk.Combobox(frm, textvariable=profile_var, values=labels, state="readonly", width=42)
    profile_cb.grid(row=1, column=1, sticky=tk.EW, pady=4)

    ttk.Label(frm, text="Start age:", font=theme.FONT_UI_HEADER).grid(row=2, column=0, sticky=tk.NW, pady=(12, 4))
    age_fr = ttk.Frame(frm)
    age_fr.grid(row=2, column=1, sticky=tk.W, pady=(12, 4))
    start_age_var = tk.IntVar(value=0)
    ttk.Radiobutton(age_fr, text="Birth (age 0)", variable=start_age_var, value=0).pack(anchor=tk.W)
    ttk.Radiobutton(age_fr, text="Skip infancy (age 3)", variable=start_age_var, value=3).pack(anchor=tk.W)

    genders = sorted({str(p.get("gender", "")).strip() for p in profiles if str(p.get("gender", "")).strip()})
    if not genders:
        genders = ["Girl", "Boy", "Non-binary"]

    temps = sorted({str(p.get("temperament", "")).strip() for p in profiles if str(p.get("temperament", "")).strip()})

    ttk.Label(frm, text="Gender:", font=theme.FONT_UI_HEADER).grid(row=3, column=0, sticky=tk.NW, pady=4)
    gender_var = tk.StringVar()
    gender_cb = ttk.Combobox(frm, textvariable=gender_var, values=genders, width=40)
    gender_cb.grid(row=3, column=1, sticky=tk.EW, pady=4)

    ttk.Label(frm, text="Temperament:", font=theme.FONT_UI_HEADER).grid(row=4, column=0, sticky=tk.NW, pady=4)
    temp_var = tk.StringVar()
    temp_cb = ttk.Combobox(frm, textvariable=temp_var, values=temps if temps else [], width=40)
    temp_cb.grid(row=4, column=1, sticky=tk.EW, pady=4)

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
            "Choose a template for baseline personality traits and branch flavor. "
            "Starting age sets years to 0 or 3 (calendar week resets to 1). "
            "Gender and temperament can match the template or be customized. "
            "Leave stat boxes empty to use template defaults."
        ),
        wraplength=400,
        foreground=theme.COLOR_NEUTRAL,
    )
    hint.grid(row=7, column=0, columnspan=2, sticky=tk.W, pady=(12, 8))

    frm.columnconfigure(1, weight=1)

    def _index_from_label(label: str) -> int:
        try:
            return labels.index(label)
        except ValueError:
            return 0

    def _sync_from_profile(*_a: object) -> None:
        idx = _index_from_label(profile_var.get())
        p = profiles[idx]
        gender_var.set(str(p.get("gender", "")))
        temp_var.set(str(p.get("temperament", "")))

    profile_cb.bind("<<ComboboxSelected>>", _sync_from_profile)
    _sync_from_profile()

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

        idx = _index_from_label(profile_var.get())
        out: dict = {
            "template": copy.deepcopy(profiles[idx]),
            "start_age_years": int(start_age_var.get()),
            "gender": gender_var.get().strip(),
            "temperament": temp_var.get().strip(),
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

    parent.wait_window(top)
    return result
