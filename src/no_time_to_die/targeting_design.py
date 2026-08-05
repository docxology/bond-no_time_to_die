"""DNA guide design and population off-target aggregation (HERACLES).

Deepens the DNA-targeted bioweapon concept with the *design* problem: given a
set of candidate nucleic-acid guides and a population of reference genomes,
which guide should HERACLES carry?

Three deterministic scoring layers are modelled:

* :func:`gc_content` / :func:`longest_homopolymer` — sequence descriptors.
* :func:`guide_efficiency` — a Doench-style composite score: a GC-content
  sweet-spot penalty, a homopolymer-run penalty, and an optional
  position-dependent nucleotide bonus (simplified, deterministic regression
  features in the spirit of Doench et al. 2014).
* :func:`population_off_target_risk` — expected off-target burden across a
  population of reference genomes, weighting near-miss windows by an
  exponential mismatch decay.

:func:`rank_guides` and :func:`design_report` combine efficiency and
off-target risk into a single deterministic ranking, so the mission adapter
and the manuscript tokens consume one shared result.

The module is pure (stdlib only), deterministic, and importable without
bond-api.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from no_time_to_die.bioweapon_counter import (
    hamming_distance,
    validate_sequence,
)

__all__ = [
    "DISTANCE_WEIGHT",
    "GC_PENALTY",
    "GC_SET",
    "HOMOPOLYMER_PENALTY",
    "IDEAL_GC",
    "GuideScore",
    "design_report",
    "gc_content",
    "guide_efficiency",
    "longest_homopolymer",
    "population_off_target_risk",
    "positional_bonus",
    "rank_guides",
]

#: Ideal GC fraction (Doench-style sweet spot for guide activity).
IDEAL_GC = 0.5

#: Linear penalty per unit deviation of GC fraction from the ideal.
GC_PENALTY = 1.0

#: Per-base penalty for homopolymer runs beyond 3.
HOMOPOLYMER_PENALTY = 0.05

#: Exponential mismatch decay weight for population off-target risk.
DISTANCE_WEIGHT = 0.5

#: Nucleotides counted toward the GC content.
GC_SET: frozenset[str] = frozenset("GC")


def gc_content(sequence: str) -> float:
    """Fraction of G/C bases in a validated DNA sequence, in ``[0, 1]``.

    Raises:
        ValueError: if the sequence is empty or contains a non-ACGT character.
    """
    validate_sequence(sequence)
    return sum(ch in GC_SET for ch in sequence) / len(sequence)


def longest_homopolymer(sequence: str) -> int:
    """Length of the longest run of an identical base in a sequence.

    Raises:
        ValueError: if the sequence is invalid.
    """
    validate_sequence(sequence)
    longest = 1
    run = 1
    previous = sequence[0]
    for ch in sequence[1:]:
        if ch == previous:
            run += 1
            longest = max(longest, run)
        else:
            run = 1
            previous = ch
    return longest


def positional_bonus(sequence: str, weights: tuple[float, ...]) -> float:
    """Position-weighted G/C preference bonus in ``[0, 1]``.

    Each position ``i`` contributes ``weights[i]`` when the base there is G or
    C, normalized by the number of positions — a simplified version of the
    position-dependent features used by sgRNA activity rules.

    Raises:
        ValueError: if ``weights`` length does not match the sequence length.
    """
    validate_sequence(sequence)
    if len(weights) != len(sequence):
        raise ValueError(
            f"positional weights length {len(weights)} must match sequence length {len(sequence)}"
        )
    if not weights:
        return 0.0
    return sum(w for i, w in enumerate(weights) if sequence[i] in GC_SET) / len(weights)


def guide_efficiency(
    sequence: str,
    *,
    weights: tuple[float, ...] | None = None,
) -> float:
    """Composite guide-efficiency score clamped to ``[0, 1]``.

    ``1 - GC_PENALTY*|gc - IDEAL_GC| - HOMOPOLYMER_PENALTY*max(0, run - 3)``
    plus an optional positional bonus. A perfectly balanced 20-mer with no long
    homopolymer scores 1.0; a GC-poor or homopolymer-heavy guide is penalised
    toward 0.

    Raises:
        ValueError: if the sequence is invalid or the weights are misaligned.
    """
    gc = gc_content(sequence)
    run = longest_homopolymer(sequence)
    base = 1.0 - GC_PENALTY * abs(gc - IDEAL_GC) - HOMOPOLYMER_PENALTY * max(0, run - 3)
    bonus = positional_bonus(sequence, weights) if weights is not None else 0.0
    return max(0.0, min(1.0, base + bonus))


def population_off_target_risk(
    guide: str,
    genomes: tuple[str, ...],
    *,
    max_mismatches: int = 2,
    distance_weight: float = DISTANCE_WEIGHT,
) -> float:
    """Expected off-target burden across a population of reference genomes.

    Every length-``|guide|`` window of every genome is scored by Hamming
    distance ``d``; windows at ``1 <= d <= max_mismatches`` contribute
    ``exp(-distance_weight * d)`` — near-misses count more than far-misses,
    and exact hits are excluded (they are the on-target signal). The sum is
    the population off-target risk.

    Raises:
        ValueError: if the guide is invalid, ``genomes`` is empty, a genome is
            shorter than the guide, or a parameter is negative.
    """
    validate_sequence(guide, label="guide")
    if not genomes:
        raise ValueError("genomes must not be empty")
    if max_mismatches < 0:
        raise ValueError("max_mismatches must be >= 0")
    if distance_weight < 0:
        raise ValueError("distance_weight must be >= 0")
    window = len(guide)
    total = 0.0
    for genome in genomes:
        validate_sequence(genome, label="genome")
        if len(genome) < window:
            raise ValueError(f"genome ({len(genome)}) is shorter than guide ({window})")
        for start in range(len(genome) - window + 1):
            dist = hamming_distance(guide, genome[start : start + window])
            if 1 <= dist <= max_mismatches:
                total += math.exp(-distance_weight * dist)
    return float(total)


@dataclass(frozen=True)
class GuideScore:
    """Deterministic design score for one candidate guide."""

    guide: str
    efficiency: float
    off_target_risk: float
    composite: float


def rank_guides(
    candidates: tuple[str, ...],
    genomes: tuple[str, ...],
    *,
    max_mismatches: int = 2,
    weights: tuple[float, ...] | None = None,
) -> tuple[GuideScore, ...]:
    """Rank candidate guides by efficiency-weighted off-target risk.

    ``composite = efficiency * (1 - min(1, off_target_risk))`` — a perfect
    guide scores its raw efficiency; off-target burden erodes it. Ties break
    alphabetically for determinism.

    Raises:
        ValueError: if ``candidates`` is empty.
    """
    if not candidates:
        raise ValueError("candidates must not be empty")
    scored: list[GuideScore] = []
    for guide in candidates:
        efficiency = guide_efficiency(guide, weights=weights)
        risk = population_off_target_risk(guide, genomes, max_mismatches=max_mismatches)
        composite = efficiency * (1.0 - min(1.0, risk))
        scored.append(GuideScore(guide, efficiency, risk, composite))
    scored.sort(key=lambda s: (-s.composite, s.guide))
    return tuple(scored)


def design_report(
    candidates: tuple[str, ...],
    genomes: tuple[str, ...],
    *,
    max_mismatches: int = 2,
    weights: tuple[float, ...] | None = None,
) -> dict[str, object]:
    """Full guide-design result as a plain, JSON-serializable dict.

    Includes the ranked scores and the best guide's efficiency, off-target
    risk, and composite score — consumed verbatim by the mission adapter and
    manuscript tokens.
    """
    ranked = rank_guides(candidates, genomes, max_mismatches=max_mismatches, weights=weights)
    best = ranked[0]
    return {
        "num_guides": len(candidates),
        "ranked": tuple(
            {
                "guide": score.guide,
                "efficiency": score.efficiency,
                "off_target_risk": score.off_target_risk,
                "composite": score.composite,
            }
            for score in ranked
        ),
        "best_guide": best.guide,
        "best_efficiency": best.efficiency,
        "best_off_target_risk": best.off_target_risk,
        "best_composite": best.composite,
    }
