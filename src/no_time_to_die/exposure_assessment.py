"""Exposure pathway and cumulative risk assessment (HERACLES forensics).

Models how a poison dose reaches and accumulates in a target organism — the
exposure-assessment half of the Vesper scenario: the residue on the glass is
recovered, but the *absorbed dose* is what determines the hazard. Deterministic
classical risk-assessment arithmetic:

* :func:`absorbed_dose` — intake through an exposure pathway:
  ``concentration * contact_rate * duration * absorption_fraction``.
* :func:`cumulative_exposure` — body burden under first-order elimination:
  ``(intake_rate / k_e) * (1 - exp(-k_e * t))``.
* :func:`margin_of_exposure` — ``NOAEL / absorbed_dose`` (NRC 1983 framing).
* :func:`risk_quotient` — ``absorbed_dose / reference_dose`` (RfD-style).

:func:`exposure_scenario_report` composes the pathway into one deterministic,
JSON-serializable verdict. The module is pure, deterministic, and importable
without bond-api.
"""

from __future__ import annotations

import math

__all__ = [
    "absorbed_dose",
    "cumulative_exposure",
    "exposure_scenario_report",
    "margin_of_exposure",
    "risk_quotient",
]


def absorbed_dose(
    concentration: float,
    contact_rate: float,
    duration: float,
    absorption_fraction: float,
) -> float:
    """Mass absorbed through an exposure pathway (mass units).

    ``concentration * contact_rate * duration * absorption_fraction``.

    Raises:
        ValueError: if any rate is negative or ``absorption_fraction`` is
            outside ``[0, 1]``.
    """
    if concentration < 0:
        raise ValueError("concentration must be >= 0")
    if contact_rate < 0:
        raise ValueError("contact_rate must be >= 0")
    if duration < 0:
        raise ValueError("duration must be >= 0")
    if not 0.0 <= absorption_fraction <= 1.0:
        raise ValueError("absorption_fraction must be in [0, 1]")
    return float(concentration * contact_rate * duration * absorption_fraction)


def cumulative_exposure(
    intake_rate: float,
    elimination_rate: float,
    duration: float,
) -> float:
    """Body burden after continuous intake with first-order elimination.

    ``(intake_rate / k_e) * (1 - exp(-k_e * duration))`` — approaches the
    steady-state burden ``intake_rate / k_e`` as duration grows.

    Raises:
        ValueError: if ``intake_rate < 0``, ``elimination_rate <= 0``, or
            ``duration < 0``.
    """
    if intake_rate < 0:
        raise ValueError("intake_rate must be >= 0")
    if elimination_rate <= 0:
        raise ValueError("elimination_rate must be > 0")
    if duration < 0:
        raise ValueError("duration must be >= 0")
    return float((intake_rate / elimination_rate) * (1.0 - math.exp(-elimination_rate * duration)))


def margin_of_exposure(absorbed: float, noael: float) -> float:
    """Margin of exposure ``NOAEL / absorbed`` (infinite for zero exposure).

    Raises:
        ValueError: if ``absorbed < 0`` or ``noael <= 0``.
    """
    if absorbed < 0:
        raise ValueError("absorbed must be >= 0")
    if noael <= 0:
        raise ValueError("noael must be > 0")
    if absorbed == 0:
        return float("inf")
    return float(noael / absorbed)


def risk_quotient(absorbed: float, reference_dose: float) -> float:
    """Hazard quotient ``absorbed / reference_dose`` (RfD-style ratio).

    Raises:
        ValueError: if ``absorbed < 0`` or ``reference_dose <= 0``.
    """
    if absorbed < 0:
        raise ValueError("absorbed must be >= 0")
    if reference_dose <= 0:
        raise ValueError("reference_dose must be > 0")
    return float(absorbed / reference_dose)


def exposure_scenario_report(
    *,
    concentration: float,
    contact_rate: float,
    duration: float,
    absorption_fraction: float,
    elimination_rate: float,
    noael: float,
    reference_dose: float,
) -> dict[str, object]:
    """Compose an exposure scenario into a deterministic risk verdict.

    Computes the absorbed dose, the accumulated body burden, the margin of
    exposure, and the risk quotient. The verdict is ``"acceptable"`` when the
    margin of exposure is at least 1 and the risk quotient at most 1,
    otherwise ``"elevated risk"``.

    Raises:
        ValueError: if any pathway parameter is invalid (see the individual
            helpers).
    """
    absorbed = absorbed_dose(concentration, contact_rate, duration, absorption_fraction)
    intake_rate = absorbed / duration if duration > 0 else 0.0
    cumulative = cumulative_exposure(intake_rate, elimination_rate, duration)
    moe = margin_of_exposure(absorbed, noael)
    rq = risk_quotient(absorbed, reference_dose)
    verdict = "acceptable" if moe >= 1.0 and rq <= 1.0 else "elevated risk"
    return {
        "absorbed_dose": absorbed,
        "cumulative_exposure": cumulative,
        "margin_of_exposure": moe,
        "risk_quotient": rq,
        "verdict": verdict,
    }
