# Game package plan (`game/`)

This document ties the **mockup** (reference UX) to the **real game** (rules and state).

## Relationship to `mockup/`

| Concern | `mockup/` | `game/` (planned) |
|--------|-----------|-------------------|
| Weekly layout | `mockup.ui.layout`, `mockup.ui.console_views` | Import the same modules; pass live data |
| Events list & reactions | Hard-coded strings + `input()` | Event definitions, validation, narrative lookup |
| Personality | Random / table deltas on `MockSession` | Formal trait model, caps, synergies, decay |
| Branch tree | `mock_branch_tree.build_branch_lines` + flags | Real progression graph; emit `list[str]` lines for `render_branch_panel` |
| Saves / controls | Labels only | Persistence, menus, “next week” orchestration |

The mockup remains the **visual and interaction contract**: same panels, same flow order (status → traits → optional cumulative → events → summary → tree → controls → last change).

## Suggested `game/` layout (incremental)

1. **`game/state.py`** — Immutable or tracked game state: child profile, calendar week, trait vector, unlocked branch ids, cumulative counters used for UI.
2. **`game/events.py`** — Event catalog: id, text, eligible reactions, handlers that return trait deltas and branch updates (pure functions where possible).
3. **`game/personality.py`** — Apply deltas with clamping, optional curves, and logging for the “last change” banner.
4. **`game/branches.py`** — Branch DAG or table: prerequisites, labels; function `tree_lines(state) -> list[str]` for ASCII (or swap renderer later).
5. **`game/engine.py`** — `advance_week`, `resolve_choice(event_id, reaction)`; coordinates events + personality + branches.
6. **`game/main.py`** (optional) — CLI entry that mirrors `mockup.main` prompts but calls the engine; imports `mockup.ui.console_views` for output.

Start by implementing **`tree_lines(state)`** and **`to_trait_panel(state)`** adapters that feed existing `render_*` functions without changing layout code.

## Visual feedback parity

- **Trend arrows**: Snapshot traits before each resolved week (same as `apply_trait_deltas` in mock).
- **Early-years strip**: Optional; feed cumulative gain map from the engine if you keep that metaphor.
- **Branch expansion**: Keep generating a `list[str]` so swapping ASCII for richer UI later stays localized.

## Non-goals for first integration

- Do not duplicate layout strings inside `game/`; extend `console_views` if a new panel is needed.
- Do not import `MockSession` from production code; treat mock types as reference-only.
