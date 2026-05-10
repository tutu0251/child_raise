"""Apply caregiver reactions to traits.

Each template carries per-trait `trait_weights`. Effective shift uses intensity (0–10)
and reaction-specific modifiers:

    Δtrait ≈ round(template_weight × intensity × modifier[reaction][trait])

which implements the design goal ``trait += template_weight × reaction_intensity`` while
letting each reaction style bias different traits.
"""

from __future__ import annotations

from game.template_data import DEFAULT_TRAIT_KEYS

REACTION_KINDS: tuple[str, ...] = (
    "Praise",
    "Punish",
    "Guide",
    "Encourage",
    "Restrict",
    "Ignore",
)

# Multipliers align reaction style with traits before rounding. Effective delta:
#   Δtrait ≈ round(template_weight[trait] × intensity × multiplier[reaction][trait])
REACTION_TRAIT_MULTIPLIERS: dict[str, dict[str, float]] = {
    "Praise": {
        "Openness": 0.18,
        "Conscientiousness": 0.10,
        "Extraversion": 0.14,
        "Agreeableness": 0.22,
        "Neuroticism": -0.08,
        "Resilience": 0.16,
        "Independence": 0.08,
        "Risk-taking": 0.06,
    },
    "Punish": {
        "Openness": -0.06,
        "Conscientiousness": 0.08,
        "Extraversion": -0.10,
        "Agreeableness": -0.18,
        "Neuroticism": 0.22,
        "Resilience": -0.12,
        "Independence": -0.08,
        "Risk-taking": -0.14,
    },
    "Guide": {
        "Openness": 0.12,
        "Conscientiousness": 0.22,
        "Extraversion": 0.06,
        "Agreeableness": 0.10,
        "Neuroticism": -0.06,
        "Resilience": 0.14,
        "Independence": 0.12,
        "Risk-taking": 0.04,
    },
    "Encourage": {
        "Openness": 0.14,
        "Conscientiousness": 0.12,
        "Extraversion": 0.20,
        "Agreeableness": 0.14,
        "Neuroticism": -0.12,
        "Resilience": 0.20,
        "Independence": 0.16,
        "Risk-taking": 0.16,
    },
    "Restrict": {
        "Openness": -0.08,
        "Conscientiousness": 0.14,
        "Extraversion": -0.14,
        "Agreeableness": -0.06,
        "Neuroticism": 0.10,
        "Resilience": -0.06,
        "Independence": -0.18,
        "Risk-taking": -0.20,
    },
    "Ignore": {
        "Openness": -0.06,
        "Conscientiousness": -0.04,
        "Extraversion": -0.12,
        "Agreeableness": -0.08,
        "Neuroticism": 0.12,
        "Resilience": -0.10,
        "Independence": 0.06,
        "Risk-taking": -0.04,
    },
}


def trait_deltas(
    trait_weights: dict[str, float],
    reaction: str,
    intensity: int,
    *,
    response_gain: float = 22.0,
) -> dict[str, int]:
    """Integer deltas: round(template_weight × intensity × modifier × response_gain)."""
    if reaction not in REACTION_TRAIT_MULTIPLIERS:
        return {}
    mult = REACTION_TRAIT_MULTIPLIERS[reaction]
    i = max(0, min(10, int(intensity)))
    out: dict[str, int] = {}
    for key in DEFAULT_TRAIT_KEYS:
        w = float(trait_weights.get(key, 0.0))
        m = float(mult.get(key, 0.0))
        raw = w * float(i) * m * response_gain
        if raw == 0:
            continue
        delta = int(round(raw))
        if delta != 0:
            out[key] = delta
    return out


def apply_trait_deltas(traits: dict[str, int], deltas: dict[str, int]) -> dict[str, int]:
    updated = dict(traits)
    for k, d in deltas.items():
        updated[k] = max(0, min(100, int(updated.get(k, 50)) + int(d)))
    return updated


def format_delta_line(deltas: dict[str, int]) -> str:
    if not deltas:
        return "No measurable trait shift from this reaction (intensity 0 or neutral overlap)."
    parts = [f"{k} {v:+d}" for k, v in sorted(deltas.items())]
    return "Trait updates: " + ", ".join(parts)
