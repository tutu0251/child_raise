"""End-of-run personality summary from traits and reaction history."""

from __future__ import annotations

from collections import Counter

from game.template_data import DEFAULT_TRAIT_KEYS


def _reaction_counts(week_history: list[dict]) -> Counter[str]:
    c: Counter[str] = Counter()
    for block in week_history:
        if not isinstance(block, dict):
            continue
        for r in block.get("reactions") or []:
            if isinstance(r, dict) and r.get("reaction"):
                c[str(r["reaction"])] += 1
    return c


def build_personality_analysis(
    *,
    child: dict[str, str | int],
    traits: dict[str, int],
    week_history: list[dict],
    simulation_length_years: int,
    simulated_years_approx: float,
    autoplay_highlights: list[dict] | None = None,
    autoplay_batch_summaries: list[str] | None = None,
    branch_comparison_text: str | None = None,
) -> str:
    name = str(child.get("name", "Child"))
    branch = str(child.get("branch", ""))
    lines: list[str] = [
        f"Personality analysis — {name}",
        f"Story branch label: {branch or '(none)'}",
        f"Run target: {simulation_length_years} years · simulated ≈ {simulated_years_approx:.2f} years.",
        "",
        "--- Trait profile (0–100) ---",
    ]
    ordered = [(k, int(traits.get(k, 50))) for k in DEFAULT_TRAIT_KEYS]
    ordered.sort(key=lambda x: -x[1])
    for k, v in ordered:
        lines.append(f"  {k:18} {v:3}")

    hi = [f"{k} ({v})" for k, v in ordered[:3]]
    lo = [f"{k} ({v})" for k, v in sorted(ordered, key=lambda x: x[1])[:3]]
    lines.extend(["", "--- Highlights ---", f"  Strongest: {', '.join(hi)}", f"  Lowest: {', '.join(lo)}"])

    rc = _reaction_counts(week_history)
    lines.extend(["", "--- Caregiver reactions (all weeks) ---"])
    if rc:
        total = sum(rc.values())
        for kind, n in rc.most_common():
            pct = 100.0 * n / total if total else 0.0
            lines.append(f"  {kind:12} {n:5} ({pct:4.1f}%)")
    else:
        lines.append("  (none recorded)")

    lines.extend(
        [
            "",
            "(Analysis text is deterministic from traits and logs; refine copy later.)",
        ]
    )
    if autoplay_highlights:
        from game.simulation import format_autoplay_highlight_line

        lines.extend(["", "--- Auto-play key events ---"])
        for h in autoplay_highlights[:80]:
            lines.append(f"  {format_autoplay_highlight_line(h)}")
        if len(autoplay_highlights) > 80:
            lines.append(f"  … and {len(autoplay_highlights) - 80} more")

    if autoplay_batch_summaries:
        lines.extend(["", "--- Fast-forward batch summaries ---"])
        for ln in autoplay_batch_summaries[-40:]:
            lines.append(f"  {ln}")

    if branch_comparison_text:
        lines.extend(["", "--- Branch comparison (latest saves) ---", branch_comparison_text])
    return "\n".join(lines)


__all__ = ["build_personality_analysis"]
