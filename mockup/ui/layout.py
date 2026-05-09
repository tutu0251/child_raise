"""Console layout primitives — reusable by `game/` when wiring real logic."""

from __future__ import annotations

import sys

WIDTH = 76


def clamp_trait(v: int, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, v))


def _trend_symbols() -> tuple[str, str, str]:
    enc = getattr(sys.stdout, "encoding", "") or ""
    if enc.lower().startswith("utf"):
        return ("\u2191", "\u2193", "\u2192")
    return ("^", "v", "=")


_T_UP, _T_DOWN, _T_FLAT = _trend_symbols()


def trend_legend() -> str:
    return f"{_T_UP} up / {_T_DOWN} down / {_T_FLAT} flat"


def hr(char: str = "=") -> None:
    print(char * WIDTH)


def section(title: str) -> None:
    print()
    hr("-")
    print(f" {title}")
    hr("-")


def trend_arrow(previous: dict[str, int] | None, name: str, current: int) -> str:
    if previous is None or name not in previous:
        return " "
    diff = current - previous[name]
    if diff > 0:
        return _T_UP
    if diff < 0:
        return _T_DOWN
    return _T_FLAT


def trait_bar(
    label: str,
    value: int,
    trend: str,
    *,
    max_val: int = 100,
    bar_w: int = 18,
) -> None:
    v = clamp_trait(value, hi=max_val)
    filled = round(bar_w * v / max_val)
    empty = bar_w - filled
    bar = "#" * filled + "-" * empty
    print(f"  {label:<14} [{bar}] {v:>3}/{max_val}  {trend}")


def wrap_paragraph(text: str, indent: str = "  ") -> None:
    max_chunk = WIDTH - len(indent)
    words = text.split()
    line: list[str] = []
    length = 0
    for w in words:
        add = len(w) + (1 if line else 0)
        if length + add > max_chunk and line:
            print(indent + " ".join(line))
            line = [w]
            length = len(w)
        else:
            line.append(w)
            length += add
    if line:
        print(indent + " ".join(line))


def footer(end_title: str = "End of mockup") -> None:
    print()
    hr("=")
    print(f" {end_title} ".center(WIDTH))
    hr("=")
