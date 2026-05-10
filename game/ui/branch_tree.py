"""ASCII branch tree visualization for the main window and optional popup."""

from __future__ import annotations

from tkinter import ttk

import tkinter as tk

from game.ui import theme


def placeholder_branch_lines(
    *,
    week_label: str,
    branch_name: str,
    highlight_debate: bool = False,
) -> list[str]:
    """Static demo tree; replace with session-driven lines later."""
    lines = [
        f"  Root: Childhood path  [{week_label}]",
        "  |",
        "  +-- Early focus: Observation",
        "  |     |",
        f"  |     +-- {branch_name}  <-- current",
        "  |     |     |",
    ]
    if highlight_debate:
        lines.extend(
            [
                "  |     |     +-- Debate club  (open) ---+",
                "  |     |     |                          |",
                "  |     |     |                          +-- Rhetoric circle",
                "  |     |     |                          +-- Peer panel prep",
            ]
        )
    else:
        lines.append("  |     |     +-- Debate club  (locked)")
    lines.extend(
        [
            "  |     |     |",
            "  |     |     +-- Maker lab  (open)",
            "  |     |",
            "  |     +-- Scholar | Arts (not taken)",
            "  |",
            "  +-- Alternate: Athletics ---+",
            "        |                     |",
            "        +-- Track & field     +-- Team sports (mock)",
        ]
    )
    return lines


class BranchTreePanel:
    """Mono-spaced text region with scrollbars for an ASCII tree."""

    def __init__(self, frame: ttk.LabelFrame, text: tk.Text) -> None:
        self.frame = frame
        self._text = text

    @classmethod
    def build(cls, parent: tk.Misc, *, autopack: bool = True) -> BranchTreePanel:
        lf = ttk.LabelFrame(parent, text="Branch timeline (saves + this run)", padding=8)
        if autopack:
            lf.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        txt = tk.Text(lf, height=14, wrap=tk.NONE, font=theme.FONT_MONO)
        bx = ttk.Scrollbar(lf, orient=tk.HORIZONTAL, command=txt.xview)
        by = ttk.Scrollbar(lf, orient=tk.VERTICAL, command=txt.yview)
        txt.configure(xscrollcommand=bx.set, yscrollcommand=by.set)
        txt.grid(row=0, column=0, sticky="nsew")
        by.grid(row=0, column=1, sticky="ns")
        bx.grid(row=1, column=0, sticky="ew")
        lf.rowconfigure(0, weight=1)
        lf.columnconfigure(0, weight=1)

        return cls(lf, txt)

    def set_lines(self, lines: list[str]) -> None:
        self._text.config(state=tk.NORMAL)
        self._text.delete("1.0", tk.END)
        self._text.insert("1.0", "\n".join(lines))
        self._text.config(state=tk.DISABLED)
