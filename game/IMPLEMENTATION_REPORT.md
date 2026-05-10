# Child-raising simulation — implementation report

**Generated:** 2026-05-10  
**Scope:** `game/` package (GUI, simulation, templates, persistence, narrative, personality).

---

## Part A — Step-by-step coding instructions (Cursor-style)

Use this section as a repeatable playbook for the same feature set on a similar codebase.

### A1. Template age vs start-age option (core rule)

1. **Add a pure resolver** in `game/template_data.py` (e.g. `effective_new_game_age_and_week`) that takes the raw template dict and the player’s start-age option (`0` or `3`).
2. **Encode the contract:**  
   `effective_age = template.age_years if template.age_years > chosen_start else chosen_start`  
   with `chosen_start ∈ {0, 3}` (clamp odd values if tests pass arbitrary ints).
3. **Calendar week policy** (keep saves and event pools coherent):  
   - If the template age **overrides** the start option → use the template’s `calendar_week` (clamped to `1..52`).  
   - Else if the player chose **skip infancy (3)** → force `calendar_week = 1`.  
   - Else (birth path) → use the template’s `calendar_week` when the key exists; otherwise fall back to the caller’s `calendar_week` argument.
4. **Wire `apply_new_game_choices`** to call the resolver once, then set `profile["age_years"]` / `profile["calendar_week"]`, then apply gender, temperament, and optional stat overrides (unchanged order so overrides always win over template defaults).
5. **Update `game/main.py`** only if it still hard-codes `calendar_week=1`; keep passing the dialog’s `start_age_years` and optional stats.
6. **Tests:** add cases for (a) template older than both 0 and 3, (b) template `2` with start `3` → age `3`, week `1`, (c) birth with template `0` and explicit `calendar_week` fallback.

### A2. New-game dialog (UX refinement)

1. Import the resolver from `template_data` into `game/ui/new_game_dialog.py` (avoid duplicating rules in the UI).
2. Add a **live hint label** under the start-age radios; bind `<<ComboboxSelected>>` on the profile combobox and `trace_add("write", …)` on the start-age `IntVar`.
3. Refresh the hint on open (call once after wiring) so the first paint is correct.
4. Update the static help paragraph to mention the override rule in plain language.

### A3. Weekly narrative summary (events + reactions + traits)

1. Extend `build_weekly_narrative_feedback` in `game/narrative_placeholder.py` with an optional `week_reactions: list[dict] | None`.
2. **Reaction digest:** count `reaction` strings (e.g. `Guide×2`) for readable one-line summaries.
3. **Dominant trait shift:** walk `DEFAULT_TRAIT_KEYS`, compare `traits_now` vs `traits_week_start`, pick the largest absolute delta and describe sign/direction.
4. **Pass data from the GUI:** in `game/ui/layout.py` `_rebuild_week_summary`, pass `list(self._current_week_reactions)` into the narrative builder (same objects the events panel uses).

### A4. Branch tree visualization (beyond plain ASCII)

1. Keep `render_saved_branch_forest` in `game/persistence.py` returning `list[str]` so all callers stay simple.
2. **Enrich lines:** extend `BranchNodeMeta` with `age_years` from the save’s `child` object; print `Age N · W{week}` on each node line for clearer orientation.
3. **Optional week-diff hint:** when `node.branch_id == current_branch_id` and `|node.calendar_week - current_week| >= 8`, append a short suffix so the live session differs visibly from the last snapshot on disk.
4. **Tk styling:** in `game/ui/branch_tree.py`, centralize `configure_branch_tree_text_tags` + `fill_branch_tree_text` to tag “current” / “week note” rows; call from `BranchTreePanel.set_lines` and from the “View branch tree” popup in `layout.py` so both views behave the same.

### A5. Passive / age-linked child stats (simulation integration)

1. Implement `apply_passive_week_aging(child, traits, rng, *, calendar_week)` in `game/simulation.py` (or a small sibling module) so headless and GUI share one path.
2. At the **start** of `advance_game_week`, after reactions for the week are finished, extend `week_reaction_lines` with any `[Passive] …` log lines, then call `finalize_week_snapshot` so passive changes appear in the archived narrative.
3. Use `merge_child_stat_defaults` so missing keys behave like older saves.
4. Keep effects **small and probabilistic** so reaction-driven trait math remains dominant; avoid RNG-driven personality trait jumps if you want deterministic unit tests.

### A6. Personality end-of-run report (child stats)

1. In `game/personality_analysis.py`, after run metadata, emit a **Child attributes** block: intelligence, social tendency, health, energy (0–100) from the live `child` dict.
2. Extend **branch compare** (`format_branch_comparison` in `persistence.py`) with the same four stats so “Compare saves” matches what players see in the top bar.

### A7. Options copy (skip 0–2)

1. In `game/ui/options_dialog.py`, clarify that the jump applies **only while the child is still below age 3** so it doesn’t contradict template-age behavior.

### A8. Sample template data

1. Optionally add explicit `intelligence` / `social_tendency` / `health` / `energy` keys to one row in `game/data/child_templates.json` so “template defaults” are visible in JSON and in tests that load the first profile.

---

## Part B — Full report (post-implementation)

### B1. Feature comparison table

| Target feature | Status | Notes |
|----------------|--------|--------|
| Weekly events from JSON by age/week | **Implemented** | `template_data.sample_weekly_events` |
| Caregiver reactions → trait deltas | **Implemented** | `trait_updates` + `simulation` |
| Save / resume / fork branches | **Implemented** | `persistence.py`, schema v2 |
| Branch forest + compare saves | **Implemented** | Richer node lines, age on nodes, week hint vs live same-branch |
| Auto-play / fast-forward batches & highlights | **Implemented** | `GameSettings`, `simulation.AutoplayContext` |
| New game: profile + start age 0 vs 3 | **Implemented** | Template age override + live dialog hint |
| New game: gender, temperament, optional stats | **Implemented** | Stats merged in `apply_new_game_choices` |
| Child overview: name, age/week, branch, stats | **Implemented** | Top bar includes intelligence, social, health, energy |
| Personality stats panel (8 traits) | **Implemented** | `stats_panel.py` |
| Weekly summary narrative | **Partial → improved** | Concrete events, reaction digest, dominant trait line; still heuristic prose |
| Skip simulate 0–2 (jump to 3) | **Implemented** | Clarified in options; respects `age >= 3` |
| Passive / age development | **Partial** | Weekly nudges to child stats (+ logs); not a full growth model |
| Branch tree “graph” UI | **Partial** | Text + tags, not a graph canvas |
| Narrative / story generation | **Partial** | Structured summary, not authored story arcs |
| Multi-caregiver / co-parent mechanics | **Missing** | Single caretaker voice in templates |
| Long-term goals / education path selection | **Missing** | Branch label is flavor, not deep simulation |

### B2. Gap analysis

**Missing or light**

- **Story authoring:** Event text is templated from JSON pools; no long-form seasonal arcs or character dialogue trees.
- **Child stats ↔ events:** Intelligence/social/health/energy react to passive aging but are not yet tied to specific event categories (e.g. Health events could move `health` directly).
- **Graphical branch editor:** Timeline remains text-based; no interactive DAG, no drag-and-drop fork naming from the graph.
- **Validation UX:** New-game stat boxes validate on OK only; no inline soft warnings for unusual combinations.
- **Mobile / web:** Tk desktop only.

**Design strengths**

- Clear separation: `template_data` (content), `simulation` (rules), `ui/layout` (orchestration), `persistence` (I/O).
- Headless autoplay shares the same week advance path as the GUI, which keeps regressions visible in tests.

**Weak points**

- **Asymmetry:** Trait reactions are rich; child stat reactions are still thin (passive only).
- **Week-diff highlight** only triggers for the **same** `branch_id` as the live session vs last save; comparing two arbitrary files still relies on “Compare saves”.

### B3. Priority roadmap

**High**

- Tie **Health / Learning / Social** event categories to small bounded changes in `health`, `energy`, `intelligence`, `social_tendency` when reactions resolve (configurable weights in JSON or `trait_updates`).
- Add **one golden integration test** that loads real `child_templates.json` + `events_templates.json` and asserts template-age override end-to-end through `profile_to_game_child`.

**Medium**

- Optional **meter widgets** for the four child stats (mirror trait panel) instead of labels-only.
- **Branch tree:** second pass for fork lineage (e.g. color parent/child edges) using structured data instead of string tags only.

**Low**

- Export week history to CSV for external analysis.
- Localize UI strings.

### B4. Immediate next steps (actionable coding tasks)

1. Add `event_category → child_stat` mapping in `trait_updates` or `simulation` when applying `_apply_reaction` / auto-reactions (clamp ±1…3 per week).
2. Extend `week_history` schema (optional keys) with `child_stats_end` if you need graphs without parsing narrative text.
3. Add a **developer toggle** in `GameSettings` to disable passive aging for deterministic regression suites if RNG becomes an issue.
4. Smoke-test **Resume** + **fork** after a week with passive lines present to ensure payload size and JSON still load quickly.

---

## Files touched (this pass)

| File | Change summary |
|------|------------------|
| `game/template_data.py` | `effective_new_game_age_and_week`, calendar clamp, `apply_new_game_choices` uses resolver |
| `game/simulation.py` | `apply_passive_week_aging` + call from `advance_game_week` |
| `game/narrative_placeholder.py` | Reaction digest, dominant trait line, richer weekly copy |
| `game/persistence.py` | `BranchNodeMeta.age_years`, forest line format, week hint, compare child stats |
| `game/personality_analysis.py` | Child attributes block in end-of-run report |
| `game/ui/new_game_dialog.py` | Live age-resolution hint, help text |
| `game/ui/options_dialog.py` | Clearer skip 0–2 description |
| `game/ui/branch_tree.py` | Tags + `fill_branch_tree_text` |
| `game/ui/layout.py` | Narrative args, branch popup uses fill helper, summary heading |
| `game/data/child_templates.json` | Example explicit stats on `infant_calm` |
| `tests/test_game_integration.py` | New cases + updates for override semantics |

---

*End of report.*
