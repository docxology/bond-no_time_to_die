"""Poison delivery forensics — trace detection on the Vesper's glass.

After a poison is delivered through a drink (the "Vesper" scenario) a residue
remains on the vessel. This module models the downstream forensic task with
deterministic signal-processing mathematics:

* :func:`signal_to_noise` / :func:`detection_confidence` — whether an observed
  analytical signal clears a limit of detection (LOD).
* :func:`estimate_concentration` / :func:`recovered_dose` — back-compute the
  transferred poison dose from a measured residue signal, volume, and the
  fraction of the drink transferred to the glass wall.
* :func:`match_unknown` — identify an unknown residue spectrum against a
  reference poison-signature library by cosine similarity.

Pure, deterministic, and importable without bond-api — the mission adapter
drives these functions through the protocol.
"""

from __future__ import annotations

import math

__all__ = [
    "SPECTRUM_LIBRARY",
    "cosine_similarity",
    "decompose_mixture",
    "detection_confidence",
    "estimate_concentration",
    "match_unknown",
    "mixture_analysis",
    "recovered_dose",
    "signal_to_noise",
    "vesper_trace_report",
]

#: Limit of detection: signal-to-noise ratio at which a trace is declared
#: present with ~50% confidence under the logistic model.
DEFAULT_LOD_SNR = 3.0


def signal_to_noise(signal_peak: float, noise_rms: float) -> float:
    """Peak signal divided by root-mean-square noise.

    Raises:
        ValueError: if ``signal_peak < 0`` or ``noise_rms <= 0``.
    """
    if signal_peak < 0:
        raise ValueError("signal_peak must be >= 0")
    if noise_rms <= 0:
        raise ValueError("noise_rms must be > 0")
    return signal_peak / noise_rms


def detection_confidence(snr: float, lod_snr: float = DEFAULT_LOD_SNR) -> float:
    """Logistic confidence (in ``(0, 1)``) that a trace of the given SNR is real.

    ``1 / (1 + exp(-(snr - lod_snr)))``: below the LOD SNR confidence falls
    under half; infinitely strong signals approach 1.

    Raises:
        ValueError: if ``snr < 0`` or ``lod_snr <= 0``.
    """
    if snr < 0:
        raise ValueError("snr must be >= 0")
    if lod_snr <= 0:
        raise ValueError("lod_snr must be > 0")
    return 1.0 / (1.0 + math.exp(-(snr - lod_snr)))


def estimate_concentration(
    signal: float,
    calibration_slope: float,
    calibration_intercept: float,
) -> float:
    """Back-compute concentration from a linear calibration model ``S = m*C + b``.

    Returns ``(signal - b) / m``, clamped to ``0.0`` when ``signal`` falls
    below the calibration **intercept** ``b`` (where the inverted line would
    return a physically meaningless negative concentration).

    This clamp is *not* a limit-of-detection test, and this function has no
    knowledge of the LOD. Earlier revisions described it as one ("sub-LOD
    signals clamp to zero"), which was wrong: with the demonstration's
    ``b = 0.5`` and ``DEFAULT_LOD_SNR = 3.0``, a signal of ``1.0`` sits well
    below the limit of detection yet still returns a positive concentration of
    ``0.25``. Deciding whether a signal is real is
    :func:`detection_confidence`'s job; this function only inverts the
    calibration line. ``tests/test_delivery_forensics.py`` pins that exact
    below-LOD-yet-positive case so the two cannot be conflated again.

    Raises:
        ValueError: if ``calibration_slope <= 0``.
    """
    if calibration_slope <= 0:
        raise ValueError("calibration_slope must be > 0")
    if signal < calibration_intercept:
        return 0.0
    return (signal - calibration_intercept) / calibration_slope


def recovered_dose(
    concentration: float,
    volume_ml: float,
    transfer_fraction: float,
) -> float:
    """Transferred poison dose (arbitrary mass units) left in a residue volume.

    ``concentration * volume_ml * transfer_fraction``.

    Raises:
        ValueError: if any argument is negative or ``volume_ml == 0``.
    """
    if concentration < 0:
        raise ValueError("concentration must be >= 0")
    if volume_ml <= 0:
        raise ValueError("volume_ml must be > 0")
    if not 0.0 <= transfer_fraction <= 1.0:
        raise ValueError("transfer_fraction must be in [0, 1]")
    return concentration * volume_ml * transfer_fraction


def cosine_similarity(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    """Cosine similarity of two equal-length spectral vectors in [-1, 1].

    Raises:
        ValueError: if the vectors differ in length, are empty, or either is
            all-zero (undefined cosine).
    """
    if not a or len(a) != len(b):
        raise ValueError("spectra must be equal-length and non-empty")
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        raise ValueError("cosine_similarity is undefined for a zero vector")
    return dot / (norm_a * norm_b)


#: Reference poison "spectral fingerprints" (normalized, non-negative,
#: deterministic synthetic calibrants — see claim_ledger). Each vector is a
#: 5-bin relative response profile for a poison the forensic lab can match
#: against.
SPECTRUM_LIBRARY: dict[str, tuple[float, ...]] = {
    "ricin": (1.0, 0.2, 0.1, 0.05, 0.02),
    "coniine": (0.1, 0.9, 0.3, 0.1, 0.04),
    "aconitine": (0.05, 0.2, 0.95, 0.3, 0.1),
    "cyanide": (0.02, 0.05, 0.1, 0.85, 0.4),
    "atropine": (0.3, 0.7, 0.4, 0.2, 0.9),
}


def match_unknown(
    unknown_spectrum: tuple[float, ...],
    library: dict[str, tuple[float, ...]] | None = None,
) -> tuple[tuple[str, float], ...]:
    """Rank library poisons by cosine similarity to an unknown residue spectrum.

    Returns a tuple of ``(name, similarity)`` sorted descending by similarity
    (deterministic tie-break by name). An empty library yields an empty tuple.

    Raises:
        ValueError: if ``unknown_spectrum`` is empty, all-zero, or its length
            differs from *any* library spectrum — matching is all-or-nothing,
            never a partial ranking over the compatible subset.
    """
    library = SPECTRUM_LIBRARY if library is None else library
    if not library:
        return ()
    scored: list[tuple[float, str]] = []
    for name, ref in library.items():
        scored.append((cosine_similarity(unknown_spectrum, ref), name))
    # Sort by similarity descending, then name ascending for determinism.
    scored.sort(key=lambda pair: (-pair[0], pair[1]))
    return tuple((name, sim) for sim, name in scored)


def _nonneg_scale_and_residual(
    unknown_spectrum: tuple[float, ...],
    refs: tuple[tuple[float, ...], ...],
) -> tuple[tuple[float, ...], float]:
    """Non-negative least-squares scale of ``refs`` onto an unknown spectrum.

    Minimizes ``||unknown - sum_k w_k * ref_k||^2`` subject to ``w_k >= 0``
    (``k`` is 1 or 2). Weights are then normalized to sum to 1 -- the result
    is reported as *mixing fractions*, not an absolute scale. Returns the
    normalized weights and the squared residual on those weights.

    The ``k == 2`` non-negativity and near-collinearity are handled
    explicitly rather than by clipping a signed solution blindly.
    """
    if not refs or any(len(r) != len(unknown_spectrum) for r in refs):
        raise ValueError("refs must be non-empty, equal-length, and match the unknown")

    def dot(a: tuple[float, ...], b: tuple[float, ...]) -> float:
        return sum(x * y for x, y in zip(a, b))

    def single(ref: tuple[float, ...]) -> float:
        denom = dot(ref, ref)
        return max(0.0, dot(ref, unknown_spectrum) / denom) if denom > 0 else 0.0

    k = len(refs)
    if k == 1:
        weights = [single(refs[0])]
    else:  # k == 2
        g00, g11 = dot(refs[0], refs[0]), dot(refs[1], refs[1])
        g01 = dot(refs[0], refs[1])
        r0, r1 = dot(refs[0], unknown_spectrum), dot(refs[1], unknown_spectrum)
        det = g00 * g11 - g01 * g01
        if abs(det) > 0.0:
            w0 = (r0 * g11 - g01 * r1) / det
            w1 = (g00 * r1 - g01 * r0) / det
            if w0 < 0.0:  # clip and re-solve single on the other
                weights = [0.0, single(refs[1])]
            elif w1 < 0.0:
                weights = [single(refs[0]), 0.0]
            else:
                weights = [w0, w1]
        else:  # refs are collinear; take the better single fit
            s0, s1 = single(refs[0]), single(refs[1])
            e0 = sum(
                (unknown_spectrum[i] - s0 * refs[0][i]) ** 2 for i in range(len(unknown_spectrum))
            )
            e1 = sum(
                (unknown_spectrum[i] - s1 * refs[1][i]) ** 2 for i in range(len(unknown_spectrum))
            )
            weights = [s0, 0.0] if e0 <= e1 else [0.0, s1]
    weights = [max(0.0, w) for w in weights]
    total = sum(weights)
    if total <= 0:
        return (0.0,) * k, sum(u * u for u in unknown_spectrum)
    normalized = tuple(w / total for w in weights)
    predicted = [
        sum(normalized[m] * refs[m][i] for m in range(k)) for i in range(len(unknown_spectrum))
    ]
    residual = sum((unknown_spectrum[i] - predicted[i]) ** 2 for i in range(len(unknown_spectrum)))
    return normalized, residual


def _combinations(items: tuple[str, ...], k: int) -> list[tuple[str, ...]]:
    """Deterministic unordered k-combinations in lexicographic order."""
    if k == 1:
        return [(item,) for item in items]
    result: list[tuple[str, ...]] = []
    for i in range(len(items)):
        for tail in _combinations(items[i + 1 :], k - 1):
            result.append((items[i], *tail))
    return result


def _run_mixture(
    unknown_spectrum: tuple[float, ...],
    library: dict[str, tuple[float, ...]],
) -> tuple[tuple[tuple[str, float], ...], float]:
    """Fit 1- and 2-component mixtures; return the best ``(name, weight)``
    set and its residual.

    Single entries are tried first, then every unordered pair; the lowest-
    residual fit wins, with ties resolved to fewer components (so a pure
    single poison is reported as one, not as a zero-weight pair). Candidates
    iterate in sorted-library order, which keeps the choice deterministic.
    """
    names = sorted(library)
    best: tuple[tuple[tuple[str, float], ...], float] | None = None
    for k in (1, 2):
        for combo in _combinations(tuple(names), k):
            refs = tuple(library[n] for n in combo)
            weights, residual = _nonneg_scale_and_residual(unknown_spectrum, refs)
            result = tuple((n, float(w)) for n, w in zip(combo, weights) if w > 0)
            if best is None or residual < best[1]:
                best = (result, residual)
    assert best is not None
    # Output sorted by weight descending (ties alphabetically), so the primary
    # component is always first regardless of library iteration order.
    return tuple(sorted(best[0], key=lambda pair: (-pair[1], pair[0]))), best[1]


def decompose_mixture(
    unknown_spectrum: tuple[float, ...],
    library: dict[str, tuple[float, ...]] | None = None,
) -> tuple[tuple[str, float], ...]:
    """Decompose an unknown residue spectrum into a non-negative blend.

    ``match_unknown`` answers *which single* entry the residue most resembles;
    ``decompose_mixture`` answers *how it is made up* when it is a blend. A
    non-negative least-squares fit over 1- and 2-component candidates returns
    the ``(name, weight)`` pairs with the smallest residual, where ``weight``
    is a mixing fraction (the weights sum to 1). A pure single poison is
    returned as a one-entry tuple; an empty library yields an empty tuple.

    Raises:
        ValueError: if the unknown is empty, all-zero, or its length differs
            from *any* library spectrum (all-or-nothing, as in
            :func:`match_unknown`).
    """
    library = SPECTRUM_LIBRARY if library is None else library
    if not library:
        return ()
    if not unknown_spectrum:
        raise ValueError("unknown_spectrum must be non-empty")
    if all(x == 0 for x in unknown_spectrum):
        raise ValueError("unknown_spectrum must not be the zero vector")
    if any(len(ref) != len(unknown_spectrum) for ref in library.values()):
        raise ValueError("unknown_spectrum length must match every library spectrum")
    result, _ = _run_mixture(unknown_spectrum, library)
    return result


def mixture_analysis(
    unknown_spectrum: tuple[float, ...],
    library: dict[str, tuple[float, ...]] | None = None,
) -> dict[str, object]:
    """Full mixture-decomposition result as a plain, JSON-serializable dict.

    Carries the per-component ``weights``, the primary/secondary components and
    their weights, and the squared residual (how much of the unknown the
    two-component fit does not explain). Consumed by ``vesper_trace_report``,
    the mission adapter, and manuscript tokens.
    """
    library = SPECTRUM_LIBRARY if library is None else library
    result, residual = _run_mixture(unknown_spectrum, library)
    weights = dict(result) if result else {}
    primary = result[0] if result else ("", 0.0)
    secondary = result[1] if len(result) > 1 else ("", 0.0)
    return {
        "components": weights,
        "primary": primary[0],
        "primary_weight": primary[1],
        "secondary": secondary[0] if secondary[0] else None,
        "secondary_weight": secondary[1] if secondary[0] else None,
        "residual": residual,
        "num_components": len(result),
    }


def vesper_trace_report(
    signal: float,
    noise_rms: float,
    volume_ml: float,
    transfer_fraction: float,
    *,
    calibration_slope: float,
    calibration_intercept: float,
    lod_snr: float = DEFAULT_LOD_SNR,
    unknown_spectrum: tuple[float, ...] | None = None,
    mixture_spectrum: tuple[float, ...] | None = None,
) -> dict[str, object]:
    """Full forensic narrative as a plain, JSON-serializable dict.

    Combines SNR, detection confidence, back-computed concentration, recovered
    dose, and — when ``unknown_spectrum`` is supplied — the top spectral match,
    plus — when ``mixture_spectrum`` is supplied — a non-negative mixture
    decomposition of the residue. Deterministic and side-effect free.
    """
    snr = signal_to_noise(signal, noise_rms)
    confidence = detection_confidence(snr, lod_snr)
    concentration = estimate_concentration(signal, calibration_slope, calibration_intercept)
    dose = recovered_dose(concentration, volume_ml, transfer_fraction)
    report: dict[str, object] = {
        "snr": snr,
        "detection_confidence": confidence,
        "concentration": concentration,
        "volume_ml": volume_ml,
        "transfer_fraction": transfer_fraction,
        "recovered_dose": dose,
    }
    if unknown_spectrum is not None:
        report["top_match"] = match_unknown(unknown_spectrum, SPECTRUM_LIBRARY)[0][0]
    if mixture_spectrum is not None:
        report["mixture"] = mixture_analysis(mixture_spectrum, SPECTRUM_LIBRARY)
    return report
