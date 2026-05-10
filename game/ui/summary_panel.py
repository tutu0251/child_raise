"""Weekly narrative summary and stat-update blurb (formatted sections)."""

from __future__ import annotations

import re
import tkinter as tk
from tkinter import ttk

from game.ui import theme


def normalize_paragraphs(text: str) -> str:
    """Collapse excessive blank lines for cleaner Text widget layout."""
    t = text.strip()
    t = re.sub(r"[ \t]+\n", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t


class SummaryPanel:
    def __init__(self, frame: ttk.LabelFrame, text: tk.Text) -> None:
        self.frame = frame
        self._text = text

    @classmethod
    def build(cls, parent: tk.Misc) -> SummaryPanel:
        lf = ttk.LabelFrame(parent, text="Weekly summary", padding=8)
        lf.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        txt = tk.Text(lf, height=12, wrap=tk.WORD, font=theme.FONT_UI)
        txt.pack(fill=tk.BOTH, expand=True)
        txt.tag_configure(
            "section",
            font=(theme.FONT_UI[0], theme.FONT_UI[1], "bold"),
            spacing1=4,
            spacing3=2,
        )

        return cls(lf, txt)

    def set_content(self, narrative: str, stats_blurb: str) -> None:
        body = normalize_paragraphs(narrative)
        stats = normalize_paragraphs(stats_blurb)

        self._text.config(state=tk.NORMAL)
        self._text.delete("1.0", tk.END)

        for line in body.split("\n"):
            stripped = line.strip()
            if stripped.startswith("---") and stripped.endswith("---"):
                self._text.insert(tk.END, line + "\n", "section")
            else:
                self._text.insert(tk.END, line + "\n")

        self._text.insert(tk.END, "\n")
        self._text.insert(tk.END, "--- Stats update (placeholder) ---\n", "section")
        self._text.insert(tk.END, stats)

        self._text.config(state=tk.DISABLED)
