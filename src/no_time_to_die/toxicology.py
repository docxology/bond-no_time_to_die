"""Poison-garden toxicology (Safin's island flora).

Models dose–response toxicology of the plant toxins that populate the poison
garden in *No Time to Die* (2021). Deterministic Hill-equation pharmacology:

* :func:`fraction_affected` — the sigmoidal dose–response curve.
* :func:`dose_for_fraction` — its analytic inverse (dose for a target effect).
* :data:`PlantToxin` / :data:`TOXIN_CATALOG` — a deterministic registry of the
  garden's flora with published-approximation LD50 values.
* :func:`combined_fraction_affected` — response addition across a mixture.

The module is pure and importable without bond-api; only the mission adapter
depends on the protocol. LD50 values are standard published approximations
(documented in ``data/claim_ledger.yaml``); the mathematics and the ledger, not
the prose, are the source of truth.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict

__all__ = [
    "TOXIN_CATALOG",
    "GardenRiskProfile",
    "PlantToxin",
    "catalog_by_name",
    "catalog_stats",
    "combined_fraction_affected",
    "dose_for_fraction",
    "fraction_affected",
    "garden_risk_profile",
    "toxin_names",
]


class GardenRiskProfile(TypedDict):
    """Typed shape of :func:`garden_risk_profile`."""

    per_agent_fraction: dict[str, float]
    combined_fraction: float


def fraction_affected(dose: float, ld50: float, hill: float) -> float:
    """Hill dose–response: fraction of a population affected at ``dose``.

    ``dose^hill / (dose^hill + ld50^hill)``. At ``dose == ld50`` exactly half
    the population is affected. Returns ``0.0`` at zero dose.

    Raises:
        ValueError: if ``dose < 0``, ``ld50 <= 0``, or ``hill <= 0``.
    """
    if dose < 0:
        raise ValueError("dose must be >= 0")
    if ld50 <= 0:
        raise ValueError("ld50 must be > 0")
    if hill <= 0:
        raise ValueError("hill must be > 0")
    if dose == 0:
        return 0.0
    return float(dose**hill / (dose**hill + ld50**hill))


def dose_for_fraction(fraction: float, ld50: float, hill: float) -> float:
    """Inverse Hill equation: dose producing a target effect fraction.

    ``ld50 * (fraction / (1 - fraction))**(1/hill)``.

    Raises:
        ValueError: if ``fraction`` is not strictly within ``(0, 1)``, or the
            LD50/Hill parameters are invalid.
    """
    if not 0.0 < fraction < 1.0:
        raise ValueError("fraction must be strictly between 0 and 1")
    if ld50 <= 0:
        raise ValueError("ld50 must be > 0")
    if hill <= 0:
        raise ValueError("hill must be > 0")
    return float(ld50 * (fraction / (1.0 - fraction)) ** (1.0 / hill))


@dataclass(frozen=True)
class PlantToxin:
    """A toxin from the poison garden with a Hill-curve profile.

    ``ld50_mg_kg`` is the dose (mg per kg body mass) lethal to 50% of a
    population — a standard published approximation; ``hill_coefficient`` is
    the Hill slope. ``source`` names the botanical origin.
    """

    name: str
    source: str
    ld50_mg_kg: float
    hill_coefficient: float

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("PlantToxin.name must be non-empty")
        if not self.source.strip():
            raise ValueError("PlantToxin.source must be non-empty")
        if self.ld50_mg_kg <= 0:
            raise ValueError("PlantToxin.ld50_mg_kg must be > 0")
        if self.hill_coefficient <= 0:
            raise ValueError("PlantToxin.hill_coefficient must be > 0")


#: Deterministic poison-garden flora catalog. LD50 figures are standard
#: published approximations for human/mammalian exposure (see claim_ledger).
TOXIN_CATALOG: tuple[PlantToxin, ...] = (
    PlantToxin(
        name="ricin",
        source="castor bean (Ricinus communis)",
        ld50_mg_kg=1.0,
        hill_coefficient=2.0,
    ),
    PlantToxin(
        name="atropine",
        source="deadly nightshade (Atropa belladonna)",
        ld50_mg_kg=10.0,
        hill_coefficient=1.5,
    ),
    PlantToxin(
        name="coniine",
        source="poison hemlock (Conium maculatum)",
        ld50_mg_kg=6.0,
        hill_coefficient=1.2,
    ),
    PlantToxin(
        name="aconitine",
        source="monkshood (Aconitum napellus)",
        ld50_mg_kg=1.5,
        hill_coefficient=2.5,
    ),
    PlantToxin(
        name="strychnine",
        source="strychnine tree (Strychnos nux-vomica)",
        ld50_mg_kg=2.0,
        hill_coefficient=1.8,
    ),
    PlantToxin(
        name="nicotine",
        source="tobacco (Nicotiana tabacum)",
        ld50_mg_kg=0.8,
        hill_coefficient=1.4,
    ),
    PlantToxin(
        name="cyanide",
        source="prussic acid from cyanogenic flora",
        ld50_mg_kg=1.5,
        hill_coefficient=3.0,
    ),
)

#: Name -> toxin lookup, built once for cheap deterministic access.
_BY_NAME: dict[str, PlantToxin] = {toxin.name: toxin for toxin in TOXIN_CATALOG}


def toxin_names() -> tuple[str, ...]:
    """Names of every toxin in the catalog, in catalog order."""
    return tuple(toxin.name for toxin in TOXIN_CATALOG)


def catalog_by_name(name: str) -> PlantToxin:
    """Return the catalog toxin with the given name.

    Raises:
        ValueError: if ``name`` is not a catalog toxin.
    """
    toxin = _BY_NAME.get(name)
    if toxin is None:
        raise ValueError(f"unknown toxin {name!r}; available: {', '.join(toxin_names())}")
    return toxin


def catalog_stats(catalog: tuple[PlantToxin, ...] | None = None) -> dict[str, float]:
    """Deterministic summary statistics over a flora catalog's LD50 values.

    Returns the count, min, max, and median of ``ld50_mg_kg``. ``catalog``
    defaults to :data:`TOXIN_CATALOG`; passing an explicit catalog lets callers
    (and the test suite) exercise both the odd- and even-length median branches
    against real toxin data.

    Raises:
        ValueError: if the catalog is empty (an undefined median).
    """
    source = TOXIN_CATALOG if catalog is None else catalog
    if not source:
        raise ValueError("catalog must not be empty")
    lds = sorted(toxin.ld50_mg_kg for toxin in source)
    n = len(lds)
    if n % 2 == 1:
        median = float(lds[n // 2])
    else:
        median = (lds[n // 2 - 1] + lds[n // 2]) / 2.0
    return {
        "count": float(n),
        "min_ld50": float(lds[0]),
        "max_ld50": float(lds[-1]),
        "median_ld50": median,
    }


def combined_fraction_affected(
    agents: tuple[tuple[PlantToxin, float], ...],
) -> float:
    """Effect fraction under response addition across a toxin mixture.

    Each ``(toxin, dose_mg_kg)`` pair contributes an independent hit
    probability; the mixture is unaffected only if every agent misses:
    ``1 - prod(1 - f_i(dose_i))``.

    Raises:
        ValueError: if ``agents`` is empty.
    """
    if not agents:
        raise ValueError("agents must not be empty")
    unaffected = 1.0
    for toxin, dose in agents:
        unaffected *= 1.0 - fraction_affected(dose, toxin.ld50_mg_kg, toxin.hill_coefficient)
    return 1.0 - unaffected


def garden_risk_profile(
    doses_mg_kg: dict[str, float],
) -> GardenRiskProfile:
    """Assess a garden-wide dosing plan over the whole catalog.

    For each toxin name in ``doses_mg_kg``, resolve the toxin and its effect
    fraction; then combine every present agent under response addition to give
    a single garden risk score. Doses are given as ``{name: mg_per_kg}``.
    """
    if not doses_mg_kg:
        raise ValueError("doses_mg_kg must not be empty")
    agents = tuple((catalog_by_name(name), dose) for name, dose in doses_mg_kg.items())
    per_agent: dict[str, float] = {}
    for toxin, dose in agents:
        per_agent[toxin.name] = fraction_affected(dose, toxin.ld50_mg_kg, toxin.hill_coefficient)
    return {
        "per_agent_fraction": per_agent,
        "combined_fraction": combined_fraction_affected(agents),
    }
