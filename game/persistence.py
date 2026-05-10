"""Save / resume game state and branch metadata under ``game/save/``."""

from __future__ import annotations

import copy
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from game.template_data import DEFAULT_TRAIT_KEYS

SCHEMA_VERSION = 2


def default_save_dir(game_root: Path | None = None) -> Path:
    root = game_root if game_root is not None else Path(__file__).resolve().parent
    d = root / "save"
    d.mkdir(parents=True, exist_ok=True)
    return d


def traits_compact(traits: dict[str, int], *, max_traits: int = 5) -> str:
    parts = [f"{k[:3]}{int(traits.get(k, 0))}" for k in DEFAULT_TRAIT_KEYS[:max_traits]]
    return "·".join(parts)


def list_save_paths(save_dir: Path) -> list[Path]:
    return sorted(save_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)


@dataclass(frozen=True)
class BranchNodeMeta:
    """Minimal metadata read from disk for tree/compare."""

    file_path: Path
    branch_id: str
    branch_label: str
    parent_branch_id: str | None
    parent_save_file: str | None
    age_years: int
    calendar_week: int
    child_name: str
    game_branch: str
    traits: dict[str, int]
    history_weeks: int


def scan_branch_nodes(save_dir: Path) -> list[BranchNodeMeta]:
    out: list[BranchNodeMeta] = []
    for path in list_save_paths(save_dir):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if raw.get("schema_version") != SCHEMA_VERSION:
            continue
        traits = raw.get("traits") or {}
        if not isinstance(traits, dict):
            traits = {}
        hist = raw.get("week_history") or []
        child = raw.get("child") or {}
        try:
            age_y = int(child.get("age_years", 0))
        except (TypeError, ValueError):
            age_y = 0
        out.append(
            BranchNodeMeta(
                file_path=path,
                branch_id=str(raw.get("branch_id", "")),
                branch_label=str(raw.get("branch_label", "Unnamed")),
                parent_branch_id=str(raw["parent_branch_id"]) if raw.get("parent_branch_id") else None,
                parent_save_file=str(raw["parent_save_file"]) if raw.get("parent_save_file") else None,
                age_years=age_y,
                calendar_week=int(raw.get("calendar_week", 1)),
                child_name=str(child.get("name", "?")),
                game_branch=str(child.get("branch", "")),
                traits={k: int(traits[k]) for k in DEFAULT_TRAIT_KEYS if k in traits},
                history_weeks=len(hist) if isinstance(hist, list) else 0,
            )
        )
    return out


def _forest_roots(nodes: list[BranchNodeMeta]) -> list[BranchNodeMeta]:
    by_id = {n.branch_id: n for n in nodes if n.branch_id}
    roots: list[BranchNodeMeta] = []
    seen: set[str] = set()
    for n in nodes:
        pid = n.parent_branch_id
        if not pid or pid not in by_id:
            if n.branch_id not in seen:
                roots.append(n)
                seen.add(n.branch_id)
    roots.sort(key=lambda x: (x.child_name, x.calendar_week, x.branch_label))
    return roots


def render_saved_branch_forest(
    save_dir: Path,
    *,
    current_branch_id: str | None,
    current_week: int | None,
    current_traits: dict[str, int] | None,
    current_label: str | None,
) -> list[str]:
    """ASCII tree of saved branches plus live session marker."""
    nodes = scan_branch_nodes(save_dir)
    by_id = {n.branch_id: n for n in nodes if n.branch_id}

    def children_of(bid: str) -> list[BranchNodeMeta]:
        ch = [n for n in nodes if n.parent_branch_id == bid]
        ch.sort(key=lambda x: (x.calendar_week, x.branch_label, x.file_path.name))
        return ch

    lines: list[str] = [
        "Branching timeline (saved files under game/save/).",
        "Legend: Ope=Openness, Con=Conscientiousness, …  Node line: Age N · Week W.",
        "",
    ]

    def walk(node: BranchNodeMeta, prefix: str, is_last: bool) -> None:
        arm = "└── " if is_last else "├── "
        tw = traits_compact(node.traits) if node.traits else "—"
        cur = "  ◀ CURRENT(save)" if current_branch_id and node.branch_id == current_branch_id else ""
        wk_tag = ""
        if (
            current_week is not None
            and current_branch_id
            and node.branch_id == current_branch_id
            and abs(int(node.calendar_week) - int(current_week)) >= 8
        ):
            wk_tag = "  [calendar week ahead of last save snapshot]"
        lines.append(
            f"{prefix}{arm}Age {node.age_years} · W{node.calendar_week} — "
            f"{node.branch_label} — {node.child_name}{cur}{wk_tag}"
        )
        lines.append(f"{prefix}{'    ' if is_last else '│   '}    traits@save: {tw}")
        lines.append(f"{prefix}{'    ' if is_last else '│   '}    `{node.file_path.name}`")
        kids = children_of(node.branch_id)
        next_prefix = prefix + ("    " if is_last else "│   ")
        for i, ch in enumerate(kids):
            walk(ch, next_prefix, i == len(kids) - 1)

    roots = _forest_roots(nodes)
    if not nodes:
        lines.append("(No saves yet — use Save.)")
    elif not roots:
        lines.append("(Could not infer roots — listing flat:)")
        for n in sorted(nodes, key=lambda x: x.file_path.name):
            lines.append(f"  • {n.branch_label} W{n.calendar_week} `{n.file_path.name}`")
    else:
        if len(roots) == 1:
            lines.append(f"Root — {roots[0].child_name}:")
            walk(roots[0], "", True)
        else:
            lines.append(f"Multiple roots ({len(roots)}):")
            for i, r in enumerate(roots):
                walk(r, "", i == len(roots) - 1)

    lines.append("")
    lines.append("── Live session (may differ from last save) ──")
    if current_branch_id:
        ct = traits_compact(current_traits or {}) if current_traits else "…"
        short = current_branch_id[:10] + "…" if len(current_branch_id) > 10 else current_branch_id
        lines.append(
            f"● week {current_week}  `{current_label or 'Playing'}`  id {short}"
        )
        lines.append(f"   traits now: {ct}")
        if current_branch_id not in by_id:
            lines.append("   Tip: Save to attach this session to the forest above.")
    else:
        lines.append("(no branch id)")

    return lines


def format_branch_comparison(a: dict[str, Any], b: dict[str, Any]) -> str:
    """Human-readable comparison for two save payloads."""
    ca = a.get("child") or {}
    cb = b.get("child") or {}
    ta = a.get("traits") or {}
    tb = b.get("traits") or {}
    ha = a.get("week_history") or []
    hb = b.get("week_history") or []

    lines: list[str] = []
    lines.append("=== Compare branches ===")
    lines.append("")
    lines.append(f"Left:  {a.get('branch_label')} (week {a.get('calendar_week')}, id {str(a.get('branch_id'))[:8]}…)")
    lines.append(f"Right: {b.get('branch_label')} (week {b.get('calendar_week')}, id {str(b.get('branch_id'))[:8]}…)")
    lines.append("")
    lines.append("--- Child / meta ---")
    lines.append(f"Name:     {ca.get('name')}  vs  {cb.get('name')}")
    lines.append(f"Branch:   {ca.get('branch')}  vs  {cb.get('branch')}")
    lines.append(f"Week:     {a.get('calendar_week')}  vs  {b.get('calendar_week')}")
    lines.append(f"History:  {len(ha)} completed week(s)  vs  {len(hb)}")
    lines.append("")
    lines.append("--- Child stats (0–100) ---")
    for label, ka, kb in (
        ("Intelligence", "intelligence", "intelligence"),
        ("Social tendency", "social_tendency", "social_tendency"),
        ("Health", "health", "health"),
        ("Energy", "energy", "energy"),
    ):
        va, vb = ca.get(ka), cb.get(kb)
        try:
            ia = int(va) if va is not None else None
        except (TypeError, ValueError):
            ia = None
        try:
            ib = int(vb) if vb is not None else None
        except (TypeError, ValueError):
            ib = None
        if isinstance(ia, int) and isinstance(ib, int):
            lines.append(f"  {label:18}  {ia:3}  vs  {ib:3}  ({ib - ia:+d})")
        else:
            lines.append(f"  {label:18}  {va!s}  vs  {vb!s}")
    lines.append("")
    lines.append("--- Personality outcomes (traits) ---")
    for k in DEFAULT_TRAIT_KEYS:
        va = int(ta.get(k, 0)) if k in ta else "—"
        vb = int(tb.get(k, 0)) if k in tb else "—"
        if isinstance(va, int) and isinstance(vb, int):
            lines.append(f"  {k:18}  {va:3}  vs  {vb:3}  ({vb - va:+d})")
        else:
            lines.append(f"  {k:18}  {va}  vs  {vb}")
    lines.append("")
    lines.append("--- Recent narrative (completed weeks) ---")

    def tail_weeks(hist: list[Any], n: int = 3) -> list[str]:
        out: list[str] = []
        if not isinstance(hist, list):
            return out
        for block in hist[-n:]:
            if not isinstance(block, dict):
                continue
            wk = block.get("calendar_week", "?")
            nar = str(block.get("narrative", "")).strip().replace("\n", " ")
            if len(nar) > 160:
                nar = nar[:157] + "…"
            reacts = block.get("reactions") or []
            rc = len(reacts) if isinstance(reacts, list) else 0
            out.append(f"  W{wk}: {rc} reaction(s). {nar}")
        return out

    lines.append("Left:")
    lines.extend(tail_weeks(ha) or ["  (none)"])
    lines.append("Right:")
    lines.extend(tail_weeks(hb) or ["  (none)"])
    lines.append("")
    lines.append("--- Cumulative reactions ---")

    def count_reactions(hist: list[Any]) -> dict[str, int]:
        counts: dict[str, int] = {}
        if not isinstance(hist, list):
            return counts
        for block in hist:
            if not isinstance(block, dict):
                continue
            for r in block.get("reactions") or []:
                if isinstance(r, dict) and r.get("reaction"):
                    k = str(r["reaction"])
                    counts[k] = counts.get(k, 0) + 1
        return counts

    ca_map = count_reactions(ha)
    cb_map = count_reactions(hb)
    keys = sorted(set(ca_map) | set(cb_map))
    for k in keys:
        lines.append(f"  {k:12}  {ca_map.get(k, 0):3}  vs  {cb_map.get(k, 0):3}")
    return "\n".join(lines)


def dump_save(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_save(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def fork_payload_from_loaded(data: dict[str, Any], *, new_label: str, parent_file_name: str) -> dict[str, Any]:
    """Deep-enough fork for new branch experiment."""
    out = copy.deepcopy(data)
    old_id = str(out.get("branch_id", ""))

    out["parent_branch_id"] = old_id or None
    out["parent_save_file"] = parent_file_name
    out["forked_at_week"] = int(out.get("calendar_week", 1))
    out["branch_id"] = str(uuid.uuid4())
    out["branch_label"] = new_label.strip() or "Fork"
    return out
