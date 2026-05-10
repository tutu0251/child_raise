"""Branch tree visualization: readable tree lines with optional highlight tags."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from game.ui import theme

_TAG_CURRENT = "hl_current"
_TAG_WEEK_NOTE = "hl_weeknote"


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


def configure_branch_tree_text_tags(txt: tk.Text) -> None:
    """Tag styles for saved-branch vs week-delta hints (call once after widget exists)."""
    txt.tag_configure(_TAG_CURRENT, background="#e8f4fc", foreground="#0a3d62")
    txt.tag_configure(_TAG_WEEK_NOTE, foreground="#8a4b00")


def fill_branch_tree_text(txt: tk.Text, lines: list[str], *, clear_tags: bool = True) -> None:
    """Insert ``lines`` and apply highlight tags to known markers."""
    txt.config(state=tk.NORMAL)
    txt.delete("1.0", tk.END)
    if clear_tags:
        for t in txt.tag_names():
            if t not in ("sel",):
                txt.tag_delete(t)
    configure_branch_tree_text_tags(txt)
    for line in lines:
        start = txt.index("end-1c")
        txt.insert(tk.END, line + "\n")
        end = txt.index("end-1c")
        blob = line.lower()
        if "◀ current" in blob or "● week" in blob or "current(save)" in blob.replace(" ", ""):
            txt.tag_add(_TAG_CURRENT, start, end)
        elif "calendar week ahead" in blob or "[week" in line:
            txt.tag_add(_TAG_WEEK_NOTE, start, end)
    txt.config(state=tk.DISABLED)


class BranchTreePanel:
    """Mono-spaced text region with scrollbars for a branch / timeline tree."""

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
        fill_branch_tree_text(self._text, lines, clear_tags=True)
