# Game package — integration plan

The **mockup** (`mockup/`) demonstrates layout, interactions, and ASCII branch visualization using placeholder data (`mock_session`, `mock_constants`, `mock_branch_tree`). The **`game/`** package ships the playable Tk shell under **`game/ui/`** (templates, persistence, options) and can still reuse **`mockup.ui`** helpers (`gui_theme`, `console_views`, `layout`) for a unified look.

## Responsibilities

| Area | Owner | Notes |
|------|--------|-------|
| Event definitions & scheduling | `game/data`, `game/template_data.py` | JSON templates, age pools |
| Branching / saves | `game/persistence.py`, `game/ui/layout.py` | Fork metadata, branch forest render |
| Personality model | `game/trait_updates.py` | Trait deltas; UI sliders do not change formulas |
| Options / UX | `game/settings.py`, `game/ui/options_dialog.py` | Skip 0–2y, auto-empty weeks, run length |
| UI binding | `game/ui/*` | Thin: loads templates, wires reactions → traits |

## Suggested layout (incremental)

```
game/
  session.py        # optional GameSession (traits, calendar, branch_state)
  events.py         # optional resolve_week_events(), apply_reaction(...)
  adapters.py       # optional strings for mockup.ui.console_views
```

Names are indicative; logic today lives in `layout.py` + helpers until split.

## Plugging into the GUI mockup (`mockup.ui.gui_app`)

`MockupGuiApp` remains the **reference** demo. Migration options:

1. **Share presentation tokens** — import `mockup.ui.gui_theme` from `game/ui/theme.py` or align fonts/colors manually (current `game/ui/theme.py` mirrors tokens).
2. **Share layout helpers** — `mockup.ui.layout`, `console_views` accept plain dicts; build those from game save/session payloads.
3. **Façade** — add `game/adapters.py` with `game_summary_text(session)`, `game_branch_lines(session)` so a thin `GameGuiApp` subclasses or copies `MockupGuiApp` and swaps handlers.

## Automated checks

From repo root:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

Covers trait progression, weekly sampling bounds, save/load + fork JSON, settings round-trip, narrative helper, branch forest renderer, stats/summary smoke (Tk withdrawn).

## Principles

- **mockup/** stays demo-first; avoid `mock_*` importing unfinished `game` rules until adapters exist.
- Prefer **function-by-function** swaps (summary → traits → branches) so at least one shell runs after each step.
- **Core mechanics** (trait deltas, template weights) stay in non-Tk modules so tests stay fast.
