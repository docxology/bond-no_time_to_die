"""DNA-targeted bioweapon countermeasure modelling (HERACLES).

This module models the hypothetical "Heracles" DNA-targeted bioweapon threat
from *No Time to Die* (2021) as real, deterministic mathematics. Three concerns
are captured:

* **Target specificity** — how precisely a designed nucleic-acid guide hits an
  intended target sequence while avoiding off-target matches across a
  reference genome.
* **Delivery** — a one-compartment kinetic model of how much of a delivered
  dose reaches the target compartment over time.
* **Countermeasure efficacy** — how target specificity, delivery, and
  countermeasure avidity combine into a neutralization probability.

Everything here is pure (no I/O, no randomness, no ``infrastructure.*``
imports) and importable in isolation, independent of bond-api. The film's
:mod:`no_time_to_die.mission` adapter drives these functions through the frozen
bond-api protocol.
"""

from __future__ import annotations

__all__ = [
    "DNA_ALPHABET",
    "compute_specificity",
    "count_window_matches",
    "countermeasure_model",
    "delivery_efficacy",
    "fraction_delivered",
    "hamming_distance",
    "neutralization_probability",
    "plasma_concentration",
    "select_best_guide",
    "validate_sequence",
]

#: Canonical nucleotide alphabet for HERACLES guide/target sequences.
DNA_ALPHABET: frozenset[str] = frozenset("ACGT")


def validate_sequence(sequence: str, *, label: str = "sequence") -> None:
    """Validate a DNA sequence against the canonical alphabet.

    Raises:
        ValueError: if the sequence is empty or contains a non-ACGT character.
    """
    if not sequence:
        raise ValueError(f"{label} must be a non-empty DNA sequence")
    invalid = sorted(set(sequence) - DNA_ALPHABET)
    if invalid:
        chars = "".join(invalid)
        raise ValueError(
            f"{label} contains invalid nucleotide(s) {chars!r}; "
            f"allowed alphabet is {''.join(sorted(DNA_ALPHABET))}"
        )


def hamming_distance(a: str, b: str) -> int:
    """Number of positions at which two equal-length sequences differ.

    Raises:
        ValueError: if either sequence is empty, invalid, or lengths differ.
    """
    validate_sequence(a, label="a")
    validate_sequence(b, label="b")
    if len(a) != len(b):
        raise ValueError(
            f"hamming_distance requires equal-length sequences, got {len(a)} vs {len(b)}"
        )
    return sum(x != y for x, y in zip(a, b))


def count_window_matches(
    target: str,
    reference: str,
    max_mismatches: int,
) -> tuple[int, int]:
    """Count on-target and off-target windows in a reference genome.

    Every length-``len(target)`` window of ``reference`` is scored by Hamming
    distance against ``target``. Windows at distance 0 count as on-target;
    windows at distance in ``[1, max_mismatches]`` count as off-target hits
    that pose a mis-address risk.

    Returns ``(on_target, off_target)``.

    Raises:
        ValueError: on invalid sequence, ``max_mismatches < 0``, or a
            reference shorter than the target.
    """
    validate_sequence(target, label="target")
    validate_sequence(reference, label="reference")
    if max_mismatches < 0:
        raise ValueError("max_mismatches must be >= 0")
    if len(reference) < len(target):
        raise ValueError(f"reference ({len(reference)}) is shorter than target ({len(target)})")
    window = len(target)
    on_target = 0
    off_target = 0
    for start in range(len(reference) - window + 1):
        dist = hamming_distance(target, reference[start : start + window])
        if dist == 0:
            on_target += 1
        elif dist <= max_mismatches:
            off_target += 1
    return on_target, off_target


def compute_specificity(on_target: int, off_target: int) -> float:
    """Specificity score in ``[0, 1]``: the share of hits that are on-target.

    ``on_target / (on_target + off_target)``. A zero-hit call yields ``0.0``
    (no usable signal); a perfectly clean call (off-targets absent) yields
    ``1.0``.

    Raises:
        ValueError: if either count is negative.
    """
    if on_target < 0 or off_target < 0:
        raise ValueError("hit counts must be non-negative")
    total = on_target + off_target
    if total == 0:
        return 0.0
    return on_target / total


def select_best_guide(
    reference: str,
    target_candidates: tuple[str, ...],
    max_mismatches: int = 2,
) -> tuple[str, float]:
    """Choose the candidate guide with the highest target specificity.

    Returns ``(best_guide, specificity)``. Ties resolve to the first candidate
    in order, keeping the result deterministic.

    Raises:
        ValueError: if ``target_candidates`` is empty.
    """
    if not target_candidates:
        raise ValueError("target_candidates must not be empty")
    best_guide: str | None = None
    best_specificity = -1.0
    for guide in target_candidates:
        on_target, off_target = count_window_matches(guide, reference, max_mismatches)
        spec = compute_specificity(on_target, off_target)
        if spec > best_specificity:
            best_specificity = spec
            best_guide = guide
    assert best_guide is not None
    return best_guide, best_specificity


def plasma_concentration(
    dose: float,
    absorption_rate: float,
    elimination_rate: float,
    time: float,
) -> float:
    """One-compartment concentration after an oral/absorbed dose.

    ``C(t) = dose * k_a / (k_a - k_e) * (exp(-k_e t) - exp(-k_a t))`` — the
    standard bateman equation for first-order absorption + elimination.

    Raises:
        ValueError: for non-positive dose/rates or a degenerate equal-rate case.
    """
    if dose < 0:
        raise ValueError("dose must be >= 0")
    if absorption_rate <= 0:
        raise ValueError("absorption_rate must be > 0")
    if elimination_rate <= 0:
        raise ValueError("elimination_rate must be > 0")
    if time < 0:
        raise ValueError("time must be >= 0")
    if absorption_rate == elimination_rate:
        raise ValueError(
            "absorption_rate must differ from elimination_rate (degenerate bateman case)"
        )
    import math

    return (
        dose
        * absorption_rate
        / (absorption_rate - elimination_rate)
        * (math.exp(-elimination_rate * time) - math.exp(-absorption_rate * time))
    )


def fraction_delivered(absorption_rate: float, exposure_time: float) -> float:
    """Fraction of a dose absorbed by ``exposure_time`` under first-order kinetics.

    ``1 - exp(-k_a * t)``, in ``[0, 1)``.

    Raises:
        ValueError: if ``absorption_rate <= 0`` or ``exposure_time < 0``.
    """
    if absorption_rate <= 0:
        raise ValueError("absorption_rate must be > 0")
    if exposure_time < 0:
        raise ValueError("exposure_time must be >= 0")
    import math

    return 1.0 - math.exp(-absorption_rate * exposure_time)


def delivery_efficacy(
    dose: float,
    absorption_rate: float,
    exposure_time: float,
) -> float:
    """Convenience: fraction of a dose absorbed (full delivery model reduced).

    Identical to :func:`fraction_delivered` for a given exposure; kept as a
    distinct name so procedural prose can read naturally.
    """
    return fraction_delivered(absorption_rate, exposure_time)


def neutralization_probability(
    on_target: int,
    off_target: int,
    delivered_fraction: float,
    avidity: float,
) -> float:
    """Combined countermeasure neutralization probability in ``[0, 1]``.

    ``specificity(on, off) * delivered_fraction * avidity/(1+avidity)``, a
    saturating product model in which any near-zero component drives the
    neutralization probability to zero.

    Raises:
        ValueError: if ``delivered_fraction`` is outside ``[0, 1]`` or
            ``avidity < 0``.
    """
    if not 0.0 <= delivered_fraction <= 1.0:
        raise ValueError("delivered_fraction must be in [0, 1]")
    if avidity < 0:
        raise ValueError("avidity must be >= 0")
    spec = compute_specificity(on_target, off_target)
    avidity_factor = avidity / (1.0 + avidity) if avidity > 0 else 0.0
    return max(0.0, min(1.0, spec * delivered_fraction * avidity_factor))


def countermeasure_model(
    reference: str,
    target_candidates: tuple[str, ...],
    *,
    max_mismatches: int,
    absorption_rate: float,
    exposure_time: float,
    avidity: float,
) -> dict[str, object]:
    """End-to-end HERACLES countermeasure assessment as a plain dict.

    Picks the best guide, computes specificity, absorption, and the combined
    neutralization probability. Returns a deterministic, JSON-serializable
    result for mission outcomes.
    """
    best_guide, specificity = select_best_guide(reference, target_candidates, max_mismatches)
    on_target, off_target = count_window_matches(best_guide, reference, max_mismatches)
    delivered = fraction_delivered(absorption_rate, exposure_time)
    neutralization = neutralization_probability(on_target, off_target, delivered, avidity)
    return {
        "best_guide": best_guide,
        "on_target": float(on_target),
        "off_target": float(off_target),
        "specificity": specificity,
        "delivered_fraction": delivered,
        "neutralization_probability": neutralization,
    }
