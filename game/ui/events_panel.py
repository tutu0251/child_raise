"""Weekly events (0–3) with caregiver reactions and intensity."""

from __future__ import annotations

from collections.abc import Callable
import tkinter as tk
from tkinter import messagebox, ttk

from game.trait_updates import REACTION_KINDS
from game.ui import theme


class EventsPanel:
    def __init__(
        self,
        frame: ttk.LabelFrame,
        choices_host: ttk.Frame,
        event_var: tk.IntVar,
        intensity_var: tk.DoubleVar,
        intensity_label: ttk.Label,
        status: ttk.Label,
        on_reaction: Callable[[int, str, int], None],
    ) -> None:
        self.frame = frame
        self._choices_host = choices_host
        self._event_var = event_var
        self._intensity_var = intensity_var
        self._intensity_label = intensity_label
        self._status = status
        self._on_reaction = on_reaction

    @classmethod
    def build(
        cls,
        parent: tk.Misc,
        on_reaction: Callable[[int, str, int], None],
    ) -> EventsPanel:
        lf = ttk.LabelFrame(parent, text="Weekly events", padding=8)
        lf.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(
            lf,
            text="Pick an event, set intensity (0–10), then choose Praise / Punish / Guide / "
            "Encourage / Restrict / Ignore.",
            wraplength=700,
        ).pack(anchor=tk.W, pady=(0, 8))

        choices_host = ttk.Frame(lf)
        choices_host.pack(fill=tk.X)

        event_var = tk.IntVar(value=-1)

        status = ttk.Label(lf, text="")
        status.pack(anchor=tk.W, pady=(8, 4))

        intensity_row = ttk.Frame(lf)
        intensity_row.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(intensity_row, text="Reaction intensity:", font=theme.FONT_UI_HEADER).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        intensity_var = tk.DoubleVar(value=5.0)

        def sync_intensity_label(_arg: str | float | None = None) -> None:
            v = max(0, min(10, int(round(float(intensity_var.get())))))
            intensity_var.set(float(v))
            intensity_lbl.config(text=str(v))

        intensity_lbl = ttk.Label(intensity_row, text="5", width=3, anchor=tk.CENTER)
        intensity_lbl.pack(side=tk.RIGHT, padx=(6, 0))
        scale = ttk.Scale(
            intensity_row,
            from_=0,
            to=10,
            orient=tk.HORIZONTAL,
            length=220,
            variable=intensity_var,
            command=lambda _v: sync_intensity_label(),
        )
        scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        sync_intensity_label()

        react_lf = ttk.LabelFrame(lf, text="Reactions", padding=6)
        react_lf.pack(fill=tk.X, pady=(4, 0))

        btn_grid = ttk.Frame(react_lf)
        btn_grid.pack(fill=tk.X)

        def fire(reaction: str) -> None:
            idx = event_var.get()
            if idx < 0:
                messagebox.showinfo(
                    "Weekly events",
                    "Select an event first (use the radio buttons next to each situation).",
                )
                return
            intensity = max(0, min(10, int(round(float(intensity_var.get())))))
            on_reaction(idx, reaction, intensity)

        for col, kind in enumerate(REACTION_KINDS):
            r, c = divmod(col, 3)
            ttk.Button(btn_grid, text=kind, command=lambda k=kind: fire(k)).grid(
                row=r, column=c, padx=4, pady=4, sticky=tk.EW)
        for c in range(3):
            btn_grid.columnconfigure(c, weight=1)

        panel = cls(lf, choices_host, event_var, intensity_var, intensity_lbl, status, on_reaction)

        def update_status() -> None:
            ev = event_var.get()
            if ev >= 0:
                status.config(text=f"Selected: Event {ev + 1} — choose intensity and a reaction.")
            else:
                status.config(text="No event selected — pick a radio button above (if any).")

        event_var.trace_add("write", lambda *_: update_status())

        update_status()
        return panel

    def set_events(self, descriptions: list[str]) -> None:
        for w in self._choices_host.winfo_children():
            w.destroy()
        self._event_var.set(-1)

        if not descriptions:
            ttk.Label(
                self._choices_host,
                text="No events this week.",
                font=theme.FONT_UI,
            ).pack(anchor=tk.W)
            self._status.config(
                text="Quiet week — use Next week or Auto week (under age 6) for progression."
            )
            return

        for i, desc in enumerate(descriptions):
            row = ttk.Frame(self._choices_host)
            row.pack(fill=tk.X, pady=(0, 4))
            ttk.Radiobutton(
                row,
                text=f"Event {i + 1}",
                variable=self._event_var,
                value=i,
            ).pack(side=tk.LEFT, padx=(0, 8))
            ttk.Label(row, text=desc, wraplength=600).pack(side=tk.LEFT, fill=tk.X, expand=True)

        self._status.config(text="Select an event, set intensity, then tap a reaction.")
