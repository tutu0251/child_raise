"""
Regenerate game/data/events_templates.json (193 parametric events).

Run from repo root: python -m game.scripts.generate_events_templates
"""

from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

_TRAIT_KEYS: tuple[str, ...] = (
    "Openness",
    "Conscientiousness",
    "Extraversion",
    "Agreeableness",
    "Neuroticism",
    "Resilience",
    "Independence",
    "Risk-taking",
)


def _trait_weights(stage_id: str, index: int) -> dict[str, float]:
    """Stable pseudo-random weights per trait (seed independent of PYTHONHASHSEED)."""
    digest = hashlib.sha256(f"{stage_id}:{index}".encode()).digest()
    seed = int.from_bytes(digest[:8], "big")
    rng = random.Random(seed)
    return {k: round(rng.uniform(0.03, 0.14), 4) for k in _TRAIT_KEYS}


def _stage_specs() -> list[tuple[str, float, float, int]]:
    """stage_id, age_min_years, age_max_years, event_count — totals 193."""
    return [
        ("infant", 0.0, 0.999, 15),
        ("toddler", 1.0, 2.999, 25),
        ("preschool", 3.0, 4.999, 25),
        ("early_school", 5.0, 7.999, 35),
        ("middle_childhood", 8.0, 11.999, 38),
        ("adolescence", 12.0, 17.999, 55),
    ]


def _patterns(stage_id: str) -> list[tuple[str, dict[str, list[str]]]]:
    """(template, pools) — reuse rotates across the stage."""
    caretakers = ["you", "your partner", "a caregiver", "a grandparent", "a trusted adult"]
    common = {"caretaker": caretakers}

    if stage_id == "infant":
        return [
            (
                "{child_name} settled quickly after {routine} while {caretaker} offered {comfort}.",
                {
                    **common,
                    "routine": ["a feeding", "a diaper change", "tummy time", "a nap wind-down"],
                    "comfort": ["soft humming", "a gentle pat", "low light", "a familiar blanket"],
                },
            ),
            (
                "During {activity}, {child_name} tracked sounds with {focus} while {caretaker} stayed close.",
                {
                    **common,
                    "activity": ["quiet play", "a stroller walk", "bath time"],
                    "focus": ["bright eyes", "brief pauses", "quick startles then calm"],
                },
            ),
            (
                "{child_name} signaled {need}; {caretaker} responded with {response}.",
                {
                    **common,
                    "need": ["hunger", "overstimulation", "tiredness", "discomfort"],
                    "response": ["a slower pace", "a tighter swaddle", "a dim room", "a change of scene"],
                },
            ),
        ]

    if stage_id == "toddler":
        return [
            (
                "{child_name} {verb} when asked to share {toy} at {place}.",
                {
                    **common,
                    "verb": ["hesitated", "blurted 'mine!'", "handed it over", "needed a timer cue"],
                    "toy": ["a bucket truck", "play-dough tools", "a stuffed fox", "building blocks"],
                    "place": ["playgroup", "the living room", "the park sandbox"],
                },
            ),
            (
                "At {routine}, {child_name} wanted {preference}; {caretaker} offered {boundary}.",
                {
                    **common,
                    "routine": ["bedtime", "mealtime", "leaving the house"],
                    "preference": ["one more story", "a different cup", "to carry the heavy bag"],
                    "boundary": ["two choices", "a countdown", "a calm repeat of the rule", "a comfort hug first"],
                },
            ),
            (
                "{child_name} practiced {skill} and reacted with {emotion} after {outcome}.",
                {
                    **common,
                    "skill": ["potty tries", "putting on shoes", "using words for mad"],
                    "emotion": ["pride", "a quick meltdown", "quiet focus", "silly giggles"],
                    "outcome": ["success", "a miss", "partial help", "an interrupted try"],
                },
            ),
        ]

    if stage_id == "preschool":
        return [
            (
                "At preschool, {child_name} joined {activity} and later described it as {takeaway}.",
                {
                    **common,
                    "activity": ["circle time", "an art station", "block city", "a nature walk"],
                    "takeaway": ["fun", "scary at first", "too loud", "the best part"],
                },
            ),
            (
                "{child_name} negotiated {issue} with a peer using {strategy}.",
                {
                    **common,
                    "issue": ["who goes first", "which costume", "clean-up turns"],
                    "strategy": ["trading turns", "asking a teacher", "walking away", "a silly compromise"],
                },
            ),
            (
                "During {outing}, {child_name} noticed {detail} and asked {question}.",
                {
                    **common,
                    "outing": ["the grocery trip", "a museum morning", "a neighborhood walk"],
                    "detail": ["a loud machine", "a friendly dog", "a rainbow sticker"],
                    "question": ["why it beeps", "if dogs dream", "can we keep it forever"],
                },
            ),
        ]

    if stage_id == "early_school":
        return [
            (
                "In class, {child_name} {class_behavior} during {subject}.",
                {
                    **common,
                    "class_behavior": ["raised a thoughtful hand", "got distracted by chatter", "paired up willingly", "needed a quiet corner"],
                    "subject": ["reading groups", "math stations", "science demo", "music"],
                },
            ),
            (
                "At recess, {child_name} tried {play_choice} and ended the block feeling {mood}.",
                {
                    **common,
                    "play_choice": ["four-square", "tag", "swings", "chalk art"],
                    "mood": ["wired", "left out", "proud", "exhausted"],
                },
            ),
            (
                "{child_name} brought home {artifact}; {caretaker} noticed {follow_up}.",
                {
                    **common,
                    "artifact": ["a corrected worksheet", "a friendship bracelet", "a worried note"],
                    "follow_up": ["extra practicing tone", "a spark of confidence", "a need for reassurance"],
                },
            ),
        ]

    if stage_id == "middle_childhood":
        return [
            (
                "{child_name} navigated {social_test} with teammates and reflected {reflection}.",
                {
                    **common,
                    "social_test": ["a group project deadline", "a fairness dispute", "tryouts chatter"],
                    "reflection": ["it felt unfair", "we figured it out", "I stayed quiet", "I spoke up"],
                },
            ),
            (
                "Homework night: {child_name} hit friction on {topic}; {caretaker} coached with {approach}.",
                {
                    **common,
                    "topic": ["fractions", "a paragraph outline", "science vocabulary", "instrument practice"],
                    "approach": ["one tiny step", "a timer sprint", "a worked example", "a break then retry"],
                },
            ),
            (
                "{child_name} experimented with {hobby} and compared themselves to {comparison}.",
                {
                    **common,
                    "hobby": ["coding club", "debate team", "art club", "community soccer"],
                    "comparison": ["an older sibling", "a fast friend", "an online video", "last year's self"],
                },
            ),
        ]

    # adolescence
    return [
        (
            "{child_name} debated {topic} with {tone}; boundaries landed as {result}.",
            {
                **common,
                "topic": ["phone limits", "weekend plans", "grades vs effort", "dating norms"],
                "tone": ["sharp sarcasm", "quiet withdrawal", "calm reasoning", "heated bursts"],
                "result": ["a pause and repair", "a stalemate", "a negotiated compromise", "more tension later"],
            },
        ),
        (
            "After {stress}, {child_name} sought {coping} instead of {avoidance}.",
            {
                **common,
                "stress": ["a friend conflict", "a coach critique", "exam week", "identity comments"],
                "coping": ["a walk", "music", "talking it through", "journaling"],
                "avoidance": ["total shutdown", "snap replies", "risky scrolling", "skipping meals"],
            },
        ),
        (
            "{child_name} pursued {goal} and needed {support_type} from {caretaker}.",
            {
                **common,
                "goal": ["a leadership role", "a scholarship deadline", "driver training", "creative portfolio work"],
                "support_type": ["logistics help", "emotional validation", "firm accountability", "space to fail"],
            },
        ),
    ]


def build_events() -> list[dict]:
    events: list[dict] = []
    for stage_id, lo, hi, count in _stage_specs():
        patterns = _patterns(stage_id)
        for i in range(count):
            template, pools = patterns[i % len(patterns)]
            events.append(
                {
                    "id": f"{stage_id}_{i + 1:03d}",
                    "stage_id": stage_id,
                    "age_min_years": lo,
                    "age_max_years": hi,
                    "template": template,
                    "pools": pools,
                    "trait_weights": _trait_weights(stage_id, i),
                }
            )
    return events


def main() -> None:
    game_root = Path(__file__).resolve().parents[1]
    out = game_root / "data" / "events_templates.json"
    payload = {
        "schema_version": 1,
        "description": "Parametric weekly events with trait_weights (× intensity × reaction modifiers).",
        "event_count": 193,
        "events": build_events(),
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(payload['events'])} events to {out}")


if __name__ == "__main__":
    main()
