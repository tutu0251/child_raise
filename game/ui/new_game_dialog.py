"""New game setup: profile, start age (0 vs 3), gender, temperament."""

from __future__ import annotations

import copy
import tkinter as tk
from tkinter import ttk

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
      template (deep copy), start_age_years (0 or 3), gender, temperament
    or None if cancelled.
    """
    if not profiles:
        return None

    top = tk.Toplevel(parent)
    top.title("New game")
    # Do not call transient(parent) when parent is withdrawn: on Windows the dialog
    # often never appears or stays unusably tied to a hidden root.
    top.grab_set()
    top.minsize(440, 380)

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

    hint = ttk.Label(
        frm,
        text=(
            "Choose a template for baseline personality traits and branch flavor. "
            "Starting age sets years to 0 or 3 (calendar week resets to 1). "
            "Gender and temperament can match the template or be customized."
        ),
        wraplength=400,
        foreground=theme.COLOR_NEUTRAL,
    )
    hint.grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=(12, 8))

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
    btn_row.grid(row=6, column=0, columnspan=2, sticky=tk.E, pady=(8, 0))

    def on_ok() -> None:
        nonlocal result
        idx = _index_from_label(profile_var.get())
        result = {
            "template": copy.deepcopy(profiles[idx]),
            "start_age_years": int(start_age_var.get()),
            "gender": gender_var.get().strip(),
            "temperament": temp_var.get().strip(),
        }
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
