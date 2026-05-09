"""Tk presentation tokens for the mockup shell.

The real game can import these when wiring a production window so fonts and
accent colors stay aligned with the mock layout."""

from __future__ import annotations

FONT_UI = ("Segoe UI", 10)
FONT_UI_HEADER = ("Segoe UI", 9, "bold")
FONT_MONO = ("Consolas", 10)

COLOR_NEUTRAL = "#666666"
COLOR_POSITIVE = "#156318"
COLOR_NEGATIVE = "#9a2020"

REACTION_LABELS = {
    "A": "Lean in — praise effort, reflect together",
    "B": "Step back — space now, check in later",
    "C": "Coach — one concrete next step",
}

WINDOW_TITLE_MOCKUP = "Child Raise — GUI mockup"
WINDOW_MIN_SIZE = (760, 640)
