"""Player-facing simulation options (does not change trait math)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields


AUTO_PLAY_REACTION_MODES: tuple[str, ...] = ("random", "guide", "encourage")


@dataclass
class GameSettings:
    """Usability toggles; safe defaults preserve prior behavior."""

    skip_years_zero_to_two: bool = False
    auto_simulate_uneventful_weeks: bool = False
    batch_early_years_stats: bool = False
    show_branch_timeline_panel: bool = True
    simulation_length_years: int = 18  # 16 or 18
    auto_play_reaction_mode: str = "random"
    auto_play_intensity_min: int = 5
    auto_play_intensity_max: int = 5
    auto_play_random_reaction_weights: dict[str, float] | None = None
    auto_play_summary_every_n_weeks: int = 0

    def __post_init__(self) -> None:
        if self.simulation_length_years not in (16, 18):
            self.simulation_length_years = 18
        if self.auto_play_reaction_mode not in AUTO_PLAY_REACTION_MODES:
            self.auto_play_reaction_mode = "random"
        self.auto_play_intensity_min = max(0, min(10, int(self.auto_play_intensity_min)))
        self.auto_play_intensity_max = max(0, min(10, int(self.auto_play_intensity_max)))
        if self.auto_play_intensity_max < self.auto_play_intensity_min:
            self.auto_play_intensity_min, self.auto_play_intensity_max = (
                self.auto_play_intensity_max,
                self.auto_play_intensity_min,
            )
        n = int(self.auto_play_summary_every_n_weeks)
        self.auto_play_summary_every_n_weeks = max(0, n)

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
