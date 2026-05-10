"""Personality stats: colored meters (responsive width), scales, trends vs week baseline."""

from __future__ import annotations

from collections.abc import Callable
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
    def __init__(
        self,
        frame: ttk.LabelFrame,
        rows: dict[str, tuple[tk.DoubleVar, ttk.Scale, tk.Label, tk.Canvas]],
        value_labels: dict[str, ttk.Label],
        hint_label: ttk.Label | None = None,
    ) -> None:
        self.frame = frame
        self._rows = rows
        self._value_labels = value_labels
        self._hint_label = hint_label

    def set_hint_wraplength(self, px: int) -> None:
        if self._hint_label is not None and px > 120:
            self._hint_label.config(wraplength=px)

    @classmethod
    def build(
        cls,
        parent: tk.Misc,
        trait_names: list[str],
        *,
        on_change: Callable[[str, int], None] | None = None,
    ) -> StatsPanel:
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

        inner = ttk.Frame(lf)
        inner.pack(fill=tk.X)
        ttk.Label(inner, text="Trait", width=18, font=theme.FONT_UI_HEADER).grid(
            row=0, column=0, sticky=tk.W, pady=(0, 4)
        )
        ttk.Label(inner, text="Meter & scale", font=theme.FONT_UI_HEADER).grid(
            row=0, column=1, sticky=tk.W, pady=(0, 4)
        )
        ttk.Label(inner, text="Trend", width=5, anchor=tk.CENTER, font=theme.FONT_UI_HEADER).grid(
            row=0, column=2, pady=(0, 4)
        )
        ttk.Label(inner, text="Value", width=11, anchor=tk.E, font=theme.FONT_UI_HEADER).grid(
            row=0, column=3, sticky=tk.E, pady=(0, 4)
        )

        rows: dict[str, tuple[tk.DoubleVar, ttk.Scale, tk.Label, tk.Canvas]] = {}
        value_labels: dict[str, ttk.Label] = {}

        for r, name in enumerate(trait_names, start=1):
            ttk.Label(inner, text=f"{name}:", width=18, anchor=tk.W).grid(
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
            meter.pack(fill=tk.X, anchor=tk.W)

            var = tk.DoubleVar(value=0.0)
            scale = ttk.Scale(
                stack,
                from_=0,
                to=100,
                orient=tk.HORIZONTAL,
                length=_METER_DEFAULT,
                variable=var,
            )
            scale.pack(fill=tk.X, anchor=tk.W, pady=(2, 0))

            trend = tk.Label(inner, text="—", width=5, anchor=tk.CENTER, fg=theme.COLOR_NEUTRAL)
            trend.grid(row=r, column=2, pady=3)

            val = ttk.Label(inner, text="0 / 100", width=11, anchor=tk.E)
            val.grid(row=r, column=3, sticky=tk.E, pady=3)
            value_labels[name] = val

            last_w: list[int] = [0]

            def make_trace(
                n: str,
                v: tk.DoubleVar,
                lbl: ttk.Label,
                cv: tk.Canvas,
            ) -> None:
                def _sync(_a: str | None = None, _b: str | None = None, _c: str | None = None) -> None:
                    raw = float(v.get())
                    iv = max(0, min(100, int(round(raw))))
                    lbl.config(text=f"{iv} / 100")
                    paint_trait_meter(cv, iv)
                    if on_change is not None:
                        on_change(n, iv)

                v.trace_add("write", lambda *_: _sync())

            make_trace(name, var, val, meter)

            def on_stack_configure(evt: tk.Event, *, cv: tk.Canvas = meter, sc: ttk.Scale = scale, v: tk.DoubleVar = var) -> None:
                if evt.widget != stack:
                    return
                nw = int(evt.width)
                if nw < 40 or nw == last_w[0]:
                    return
                last_w[0] = nw
                bw = max(_METER_MIN, min(_METER_MAX, nw))
                cv._meter_px = bw
                cv.config(width=bw)
                sc.configure(length=bw)
                iv = max(0, min(100, int(round(float(v.get())))))
                paint_trait_meter(cv, iv, bw)

            stack.bind("<Configure>", on_stack_configure)

            rows[name] = (var, scale, trend, meter)
            paint_trait_meter(meter, 0, _METER_DEFAULT)

        inner.columnconfigure(1, weight=1)

        return cls(lf, rows, value_labels, hint_label=hint)

    def refresh_trends(self, values: dict[str, int], *, baseline: dict[str, int] | None = None) -> None:
        """Update only trend arrows (cheap). Sliders already sync meters via traces."""
        up, down, flat = "\u2191", "\u2193", "\u2192"
        for name, (_var, _scale, trend_lbl, _meter) in self._rows.items():
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
        for name, (var, _scale, trend_lbl, meter) in self._rows.items():
            v = max(0, min(100, int(values.get(name, 0))))
            var.set(float(v))
            self._value_labels[name].config(text=f"{v} / 100")
            mw = int(getattr(meter, "_meter_px", 0)) or meter.winfo_width() or _METER_DEFAULT
            paint_trait_meter(meter, v, max(_METER_MIN, min(_METER_MAX, mw)))

        self.refresh_trends(values, baseline=baseline)
