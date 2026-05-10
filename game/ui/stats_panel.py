"""Personality stats: colored meters (responsive width), trends vs week baseline."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from game.ui import theme

_METER_DEFAULT = 280
_METER_MIN = 168
_METER_MAX = 720
_METER_H = 10


def _meter_fill_color(value: int) -> str:
    v = max(0, min(100, int(value)))
    if v <= 33:
        return theme.COLOR_STAT_LOW
    if v <= 66:
        return theme.COLOR_STAT_MID
    return theme.COLOR_STAT_HIGH


def paint_trait_meter(canvas: tk.Canvas, value: int, width: int | None = None) -> None:
    """Redraw the colored fill; ``width`` defaults from canvas ``_meter_px`` or pixel width."""
    w = width
    if w is None:
        w = int(getattr(canvas, "_meter_px", 0)) or canvas.winfo_width() or _METER_DEFAULT
    w = max(_METER_MIN, min(_METER_MAX, int(w)))
    canvas._meter_px = w
    if canvas.winfo_width() <= 1:
        canvas.config(width=w)
    h = _METER_H
    iv = max(0, min(100, int(value)))
    canvas.delete("all")
    canvas.create_rectangle(0, 0, w, h, fill=theme.COLOR_METER_BG, outline="#c8c8c8", width=1)
    fw = max(0, min(w, int(round(w * iv / 100))))
    if fw > 0:
        canvas.create_rectangle(0, 0, fw, h, fill=_meter_fill_color(iv), outline="")


class StatsPanel:
    """Trait meters are read-only; values change through gameplay (e.g. reactions)."""

    # Ignore layout churn between Tk passes (Windows can alternate ±few px if we write widths back).
    _METER_BW_HYSTERESIS_PX = 8
    _HINT_WRAP_HYSTERESIS_PX = 12

    def __init__(
        self,
        frame: ttk.LabelFrame,
        rows: dict[str, tuple[tk.Label, tk.Canvas, ttk.Label]],
        inner: ttk.Frame,
        hint_label: ttk.Label | None = None,
    ) -> None:
        self.frame = frame
        self._rows = rows
        self._inner = inner
        self._hint_label = hint_label
        self._last_meter_bw: int | None = None
        self._last_hint_wrap: int | None = None
        self._meter_sync_idle_pending = False
        self._values: dict[str, int] = {k: 0 for k in rows}

    def set_hint_wraplength(self, px: int) -> None:
        if self._hint_label is None or px <= 120:
            return
        px = max(121, int(px))
        px = (px // 8) * 8
        if (
            self._last_hint_wrap is not None
            and abs(px - self._last_hint_wrap) < self._HINT_WRAP_HYSTERESIS_PX
        ):
            return
        self._last_hint_wrap = px
        self._hint_label.config(wraplength=px)

    def _on_inner_configure(self, evt: tk.Event) -> None:
        if evt.widget is not self._inner:
            return
        self._queue_meter_width_sync()

    def _queue_meter_width_sync(self) -> None:
        if self._meter_sync_idle_pending:
            return
        self._meter_sync_idle_pending = True
        self.frame.after_idle(self._flush_meter_width_sync)

    def _flush_meter_width_sync(self) -> None:
        self._meter_sync_idle_pending = False
        if not self._rows:
            return
        _, probe, _ = next(iter(self._rows.values()))
        try:
            nw = int(probe.winfo_width())
        except tk.TclError:
            return
        if nw < 40:
            return
        bw = max(_METER_MIN, min(_METER_MAX, nw))
        if self._last_meter_bw is not None and abs(bw - self._last_meter_bw) < self._METER_BW_HYSTERESIS_PX:
            return
        self._last_meter_bw = bw
        for name, (_, meter, _) in self._rows.items():
            paint_trait_meter(meter, self._values.get(name, 0), bw)

    @classmethod
    def build(cls, parent: tk.Misc, trait_names: list[str]) -> StatsPanel:
        lf = ttk.LabelFrame(parent, text="Personality stats", padding=8)
        lf.pack(fill=tk.X, pady=(0, 8))

        hint = ttk.Label(
            lf,
            text=(
                "Eight traits (0–100). Meters scale with panel width (cool → warm → green tiers); "
                "arrows compare to the start of this calendar week."
            ),
            wraplength=700,
        )
        hint.pack(anchor=tk.W, pady=(0, 6))

        trait_col_chars = max((len(f"{n}:") for n in trait_names), default=18)

        inner = ttk.Frame(lf)
        inner.pack(fill=tk.X)
        ttk.Label(inner, text="Trait", width=trait_col_chars, font=theme.FONT_UI_HEADER).grid(
            row=0, column=0, sticky=tk.W, pady=(0, 4)
        )
        ttk.Label(inner, text="Meter", font=theme.FONT_UI_HEADER).grid(
            row=0, column=1, sticky=tk.W, pady=(0, 4)
        )
        ttk.Label(inner, text="Trend", width=5, anchor=tk.CENTER, font=theme.FONT_UI_HEADER).grid(
            row=0, column=2, pady=(0, 4)
        )
        ttk.Label(inner, text="Value", width=11, anchor=tk.E, font=theme.FONT_UI_HEADER).grid(
            row=0, column=3, sticky=tk.E, pady=(0, 4)
        )

        rows: dict[str, tuple[tk.Label, tk.Canvas, ttk.Label]] = {}
        for r, name in enumerate(trait_names, start=1):
            ttk.Label(inner, text=f"{name}:", width=trait_col_chars, anchor=tk.W).grid(
                row=r, column=0, sticky=tk.W, pady=3
            )

            stack = ttk.Frame(inner)
            stack.grid(row=r, column=1, sticky=tk.EW, padx=(0, 6), pady=3)

            meter = tk.Canvas(
                stack,
                width=_METER_DEFAULT,
                height=_METER_H,
                highlightthickness=0,
                bd=0,
            )
            meter.pack(fill=tk.X, expand=False, anchor=tk.W)

            trend = tk.Label(inner, text="—", width=5, anchor=tk.CENTER, fg=theme.COLOR_NEUTRAL)
            trend.grid(row=r, column=2, pady=3)

            val = ttk.Label(inner, text="0 / 100", width=11, anchor=tk.E)
            val.grid(row=r, column=3, sticky=tk.E, pady=3)

            rows[name] = (trend, meter, val)
            paint_trait_meter(meter, 0, _METER_DEFAULT)

        inner.columnconfigure(1, weight=1)

        panel = cls(lf, rows, inner=inner, hint_label=hint)
        inner.bind("<Configure>", panel._on_inner_configure)
        return panel

    def refresh_trends(self, values: dict[str, int], *, baseline: dict[str, int] | None = None) -> None:
        """Update trend arrows from the live trait map."""
        up, down, flat = "\u2191", "\u2193", "\u2192"
        for name, (trend_lbl, _meter, _val) in self._rows.items():
            v = max(0, min(100, int(values.get(name, 0))))
            if baseline is None or name not in baseline:
                trend_lbl.config(text="—", fg=theme.COLOR_NEUTRAL)
            else:
                diff = v - int(baseline[name])
                if diff > 0:
                    trend_lbl.config(text=up, fg=theme.COLOR_POSITIVE)
                elif diff < 0:
                    trend_lbl.config(text=down, fg=theme.COLOR_NEGATIVE)
                else:
                    trend_lbl.config(text=flat, fg=theme.COLOR_NEUTRAL)

    def set_traits(self, values: dict[str, int], *, baseline: dict[str, int] | None = None) -> None:
        for name in self._rows:
            self._values[name] = max(0, min(100, int(values.get(name, 0))))

        bw = self._last_meter_bw
        if bw is None:
            bw = _METER_DEFAULT

        for name, (_trend, meter, val_lbl) in self._rows.items():
            v = self._values[name]
            val_lbl.config(text=f"{v} / 100")
            paint_trait_meter(meter, v, bw)

        self.refresh_trends(self._values, baseline=baseline)
