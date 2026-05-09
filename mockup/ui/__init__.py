"""
Presentation layer shared between the mockup and (later) the real game.

Layers
------
`layout` — Console-width helpers, trait bar rendering, wrapping (no game imports).
`console_views` — Composed printf-style panels; pass plain dicts/lists from any model.
`gui_theme` — Fonts and colors for Tk; import without pulling in the full window.
`gui_app` — Tk mock shell (`MockupGuiApp`). Import when running or embedding the GUI.

The real game (`game/`) should:
  - Import `mockup.ui.layout` / `console_views` for terminal-style debug views.
  - Import `mockup.ui.gui_theme` for consistent styling, or fork tokens.
  - Replace `MockupGuiApp`’s `mockup.mock_*` calls with `game` services (see `game/PLAN.md`).

Tkinter is **not** imported from this package root — use `from mockup.ui.gui_app import main`.
"""

from mockup.ui.console_views import (
    render_branch_panel,
    render_change_banner,
    render_controls_panel,
    render_early_years_panel,
    render_events_panel,
    render_star_separator,
    render_status_bar,
    render_summary_panel,
    render_trait_panel,
)
from mockup.ui.layout import (
    WIDTH,
    clamp_trait,
    footer,
    hr,
    section,
    trait_bar,
    trend_arrow,
    trend_legend,
    wrap_paragraph,
)

__all__ = [
    "WIDTH",
    "clamp_trait",
    "footer",
    "hr",
    "render_branch_panel",
    "render_change_banner",
    "render_controls_panel",
    "render_early_years_panel",
    "render_events_panel",
    "render_star_separator",
    "render_status_bar",
    "render_summary_panel",
    "render_trait_panel",
    "section",
    "trait_bar",
    "trend_arrow",
    "trend_legend",
    "wrap_paragraph",
]
