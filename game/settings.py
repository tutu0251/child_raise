"""Player-facing simulation options (does not change trait math)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields


@dataclass
class GameSettings:
    """Usability toggles; safe defaults preserve prior behavior."""

    skip_years_zero_to_two: bool = False
    auto_simulate_uneventful_weeks: bool = False
    batch_early_years_stats: bool = False
    show_branch_timeline_panel: bool = True
    simulation_length_years: int = 18  # 16 or 18

    def __post_init__(self) -> None:
        if self.simulation_length_years not in (16, 18):
            self.simulation_length_years = 18

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict | None) -> GameSettings:
        if not raw:
            return cls()
        base = asdict(cls())
        for f in fields(cls):
            if f.name in raw:
                base[f.name] = raw[f.name]
        o = cls(**base)
        o.__post_init__()
        return o
