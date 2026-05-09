# Game package — integration plan

The **mockup** (`mockup/`) demonstrates layout, interactions, and ASCII branch visualization using placeholder data (`mock_session`, `mock_constants`, `mock_branch_tree`). The **game** package will replace those placeholders with real rules while reusing `mockup/ui/` presentation pieces where useful.

## Responsibilities

| Area | Owner | Notes |
|------|--------|--------|
| Event definitions & scheduling | `game/events` (suggested) | Structured weekly moments, triggers, copy |
| Branching / narrative graph | `game/branches` | Unlock conditions, path flags, history log |
| Personality model | `game/personality` | Trait definitions, deltas, caps, stability |
| Save/load | `game/persistence` | Serialize session + meta |
| UI binding | Thin adapter | Maps `game` models → strings / numbers for `mockup.ui` |

## Suggested layout (incremental)

```
game/
  __init__.py       # package marker (this file’s parent)
  PLAN.md           # this document
  session.py        # GameSession (traits, calendar, branch_state, …)
  events.py         # resolve_week_events(), apply_reaction(event_id, choice_id)
  branches.py       # evaluate unlocks, emit ASCII or graph view-model
  personality.py    # apply_deltas, trends, early-years aggregates
```

Names are indicative; start with one `session.py` and split when files grow.

## Plugging into the GUI mockup layout

`mockup.ui.gui_app.MockupGuiApp` currently:

1. Holds a `MockSession` and calls `apply_mock_choice`, `mock_uneventful_week`, `auto_simulate_weeks`, `build_summary`, `build_branch_lines`, `format_early_years_batch`.
2. Refreshes widgets from that session in `refresh_all()`.

**Migration path:**

1. Define a **`GameSession`** (or equivalent) in `game/session.py` with the fields the UI needs (child overview, traits dict, summary text, branch lines or raw branch state, last deltas, cumulative gains).
2. Introduce **`game/adapters.py`** (optional) with functions that mirror today’s mock API, e.g. `game_summary_text(session) -> str`, `game_branch_lines(session) -> list[str]`, so `gui_app` can swap imports behind a small façade.
3. Either subclass **`MockupGuiApp`** into **`GameGuiApp`** that uses `GameSession`, or replace `self.session` type and wire button handlers to `game.events` / `game.personality`.
4. Keep **`mockup.ui.gui_theme`** for fonts/colors so the production window stays visually aligned with the mock.

## Plugging into console panels

`mockup.ui.console_views` already accepts plain data. The game can build the same structures `mock_console.render_full()` uses, but sourcing lists/dicts from `GameSession` instead of `MOCK_*`.

## Principles

- **mockup/** stays demo-only; no circular imports from `game/` into `mock_*` during early development.
- **game/** never imports Tk; UI stays in `mockup.ui.gui_app` (or a future `game/ui.py` that only imports Tk + game adapters).
- Replace placeholders **function-by-function** (summary → traits → branches) so the GUI keeps running at each step.
