"""Interactive launcher — delegates to ``game.main`` (new-game dialog + main window)."""

from __future__ import annotations

from game.main import main as run_game_interactive

__all__ = ["run_game_interactive"]
