"""
Reusable console UI building blocks.

`layout` — widths, sections, trait bars, wrapping.
`console_views` — status bar, trait panel, events, summary, branch lines, controls.

The real game (`game/`) should import from here and supply data from its own models.
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
