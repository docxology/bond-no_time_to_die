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
    "detection_confidence",
    "estimate_concentration",
    "match_unknown",
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

    Returns ``(signal - b) / m``; sub-LOD signals (below the intercept) clamp to
    ``0.0``.

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
        ValueError: if ``unknown_spectrum`` is incompatible with every library
            spectrum.
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
) -> dict[str, object]:
    """Full forensic narrative as a plain, JSON-serializable dict.

    Combines SNR, detection confidence, back-computed concentration, recovered
    dose, and (when an ``unknown_spectrum`` is supplied) the top spectral
    match. Deterministic and side-effect free.
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
    return report
