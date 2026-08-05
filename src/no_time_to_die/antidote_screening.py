"""Competitive-antagonist antidote screening (HERACLES countermeasure).

Models the pharmacology of counteracting a poison-garden toxin with a
competitive antagonist — the antidote competes with the toxin for the same
receptor, shifting the toxin's effective dose–response. Deterministic,
classical pharmacology:

* :func:`cheng_prusoff_ic50` — apparent IC50 of a competitive antagonist at a
  given substrate (toxin) concentration, per Cheng & Prusoff (1973):
  ``IC50_app = Ki * (1 + [S]/Km)``.
* :func:`fraction_antagonized` — Langmuir occupancy of the antagonist:
  ``[A] / ([A] + IC50_app)``.
* :func:`antagonist_at_fraction` — its analytic inverse.
* :func:`screen_antidotes` — rank a library of antidotes by the survival
  probability they restore against a specific toxin dose.

The :data:`ANTIDOTE_LIBRARY` carries published-approximation inhibition
constants (see ``data/claim_ledger.yaml``). The module is pure, deterministic,
and importable without bond-api.
"""

from __future__ import annotations

from dataclasses import dataclass

from no_time_to_die.toxicology import PlantToxin, fraction_affected

__all__ = [
    "ANTIDOTE_LIBRARY",
    "Antidote",
    "AntidoteResult",
    "antagonist_at_fraction",
    "cheng_prusoff_ic50",
    "fraction_antagonized",
    "margin_of_safety",
    "screen_antidotes",
    "screen_report",
    "therapeutic_window",
]


@dataclass(frozen=True)
class Antidote:
    """A competitive antagonist with a published-approximation inhibition constant."""

    name: str
    ki: float
    source: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Antidote.name must be non-empty")
        if self.ki <= 0:
            raise ValueError("Antidote.ki must be > 0")
        if not self.source.strip():
            raise ValueError("Antidote.source must be non-empty")


#: Deterministic antidote library (published-approximation Ki values).
ANTIDOTE_LIBRARY: tuple[Antidote, ...] = (
    Antidote(name="naloxone", ki=0.4, source="opioid receptor antagonist"),
    Antidote(name="flumazenil", ki=1.0, source="benzodiazepine antagonist"),
    Antidote(name="pralidoxime", ki=2.0, source="organophosphate reactivator"),
    Antidote(name="acetylcysteine", ki=0.8, source="paracetamol antidote"),
    Antidote(name="vitamin_k", ki=5.0, source="anticoagulant antidote"),
)


def cheng_prusoff_ic50(ki: float, substrate_conc: float, km: float) -> float:
    """Apparent IC50 of a competitive antagonist (Cheng–Prusoff 1973).

    ``Ki * (1 + substrate_conc / Km)``. Raising the substrate (toxin)
    concentration raises the antagonist concentration needed to occupy half
    the receptors.

    Raises:
        ValueError: if ``ki <= 0``, ``substrate_conc < 0``, or ``km <= 0``.
    """
    if ki <= 0:
        raise ValueError("ki must be > 0")
    if substrate_conc < 0:
        raise ValueError("substrate_conc must be >= 0")
    if km <= 0:
        raise ValueError("km must be > 0")
    return float(ki * (1.0 + substrate_conc / km))


def fraction_antagonized(antagonist_conc: float, ic50_app: float) -> float:
    """Fraction of receptors occupied by the antagonist (Langmuir isotherm).

    ``[A] / ([A] + IC50_app)``, in ``[0, 1)`` — at the apparent IC50 exactly
    half the receptors are blocked.

    Raises:
        ValueError: if ``antagonist_conc < 0`` or ``ic50_app <= 0``.
    """
    if antagonist_conc < 0:
        raise ValueError("antagonist_conc must be >= 0")
    if ic50_app <= 0:
        raise ValueError("ic50_app must be > 0")
    return antagonist_conc / (antagonist_conc + ic50_app)


def antagonist_at_fraction(target_fraction: float, ic50_app: float) -> float:
    """Antagonist concentration producing a target occupancy fraction.

    Inverse Langmuir: ``ic50_app * f / (1 - f)``.

    Raises:
        ValueError: if ``target_fraction`` is not strictly in ``(0, 1)`` or
            ``ic50_app <= 0``.
    """
    if not 0.0 < target_fraction < 1.0:
        raise ValueError("target_fraction must be strictly between 0 and 1")
    if ic50_app <= 0:
        raise ValueError("ic50_app must be > 0")
    return float(ic50_app * target_fraction / (1.0 - target_fraction))


def therapeutic_window(lethal_dose: float, effective_dose: float) -> float:
    """Therapeutic window ratio ``lethal_dose / effective_dose``.

    Raises:
        ValueError: if either dose is non-positive.
    """
    if lethal_dose <= 0:
        raise ValueError("lethal_dose must be > 0")
    if effective_dose <= 0:
        raise ValueError("effective_dose must be > 0")
    return float(lethal_dose / effective_dose)


def margin_of_safety(lethal_dose: float, effective_dose: float) -> float:
    """Margin of safety ``window - 1`` (negative means the hazard precedes the cure).

    Raises:
        ValueError: if either dose is non-positive.
    """
    return therapeutic_window(lethal_dose, effective_dose) - 1.0


@dataclass(frozen=True)
class AntidoteResult:
    """Deterministic screening result for one antidote against one toxin dose."""

    name: str
    ic50_app: float
    antagonized_fraction: float
    net_effect_fraction: float
    survival_probability: float


def screen_antidotes(
    toxin: PlantToxin,
    dose: float,
    antagonist_conc: float,
    *,
    library: tuple[Antidote, ...] | None = None,
) -> tuple[AntidoteResult, ...]:
    """Rank a library of antidotes against a toxin dose by survival probability.

    For each antidote: the apparent IC50 follows Cheng–Prusoff with the
    toxin's LD50 standing in as the affinity proxy (``Km = ld50_mg_kg``); the
    antagonized fraction follows the Langmuir isotherm; the residual toxin
    effect is ``f_tox * (1 - f_antag)``; survival is ``1 - residual``. Ranked
    by survival descending, ties alphabetical.

    Raises:
        ValueError: if ``dose < 0``, ``antagonist_conc < 0``, or the library
            is empty.
    """
    if dose < 0:
        raise ValueError("dose must be >= 0")
    if antagonist_conc < 0:
        raise ValueError("antagonist_conc must be >= 0")
    library = ANTIDOTE_LIBRARY if library is None else library
    if not library:
        raise ValueError("antidote library must not be empty")
    toxin_effect = fraction_affected(dose, toxin.ld50_mg_kg, toxin.hill_coefficient)
    scored: list[AntidoteResult] = []
    for antidote in library:
        ic50_app = cheng_prusoff_ic50(antidote.ki, substrate_conc=dose, km=toxin.ld50_mg_kg)
        antagonized = fraction_antagonized(antagonist_conc, ic50_app)
        net_effect = toxin_effect * (1.0 - antagonized)
        scored.append(
            AntidoteResult(
                name=antidote.name,
                ic50_app=ic50_app,
                antagonized_fraction=antagonized,
                net_effect_fraction=net_effect,
                survival_probability=1.0 - net_effect,
            )
        )
    scored.sort(key=lambda r: (-r.survival_probability, r.name))
    return tuple(scored)


def screen_report(
    toxin: PlantToxin,
    dose: float,
    antagonist_conc: float,
    *,
    library: tuple[Antidote, ...] | None = None,
) -> dict[str, object]:
    """Full antidote-screen result as a plain, JSON-serializable dict.

    Carries the ranked results plus the best antidote's name, antagonized
    fraction, and survival probability — consumed by the mission adapter and
    manuscript tokens.
    """
    ranked = screen_antidotes(toxin, dose, antagonist_conc, library=library)
    best = ranked[0]
    return {
        "antidote_count": len(ranked),
        "ranked": tuple(
            {
                "name": result.name,
                "ic50_app": result.ic50_app,
                "antagonized_fraction": result.antagonized_fraction,
                "net_effect_fraction": result.net_effect_fraction,
                "survival_probability": result.survival_probability,
            }
            for result in ranked
        ),
        "best_antidote": best.name,
        "best_antagonized_fraction": best.antagonized_fraction,
        "best_survival_probability": best.survival_probability,
    }
