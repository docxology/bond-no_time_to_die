"""Canonical deterministic demonstration for the HERACLES mission.

Both the mission adapter (:mod:`no_time_to_die.mission`) and the manuscript
variable generator share one fixed set of demonstration inputs and one
``run_demo`` result so numeric tokens and mission outcomes can never drift.
Everything here is pure and bond-api-free.
"""

from __future__ import annotations

import hashlib
from types import ModuleType
from typing import TypedDict

from no_time_to_die import (
    antidote_screening,
    bioweapon_counter,
    delivery_forensics,
    exposure_assessment,
    targeting_design,
    toxicology,
)

__all__ = [
    "ANTAGONIST_CONC",
    "DEMO_ABSORPTION_RATE",
    "DEMO_AVIDITY",
    "DEMO_CANDIDATES",
    "DEMO_EXPOSURE_TIME",
    "DEMO_MAX_MISMATCHES",
    "DEMO_REFERENCE",
    "DEMO_SEED",
    "DOMAIN_MODULES",
    "EXPOSURE_SCENARIO",
    "FORENSIC_SCENARIO",
    "FORENSIC_UNKNOWN_SPECTRUM",
    "DemoResult",
    "input_hash",
    "run_demo",
]

#: The pure domain modules this film ships, keyed by module name. Single source
#: of truth: :func:`no_time_to_die.mission.register_gadgets` registers exactly
#: these as gadgets, and the manuscript's module-count token is ``len()`` of it,
#: so neither can drift from what the package actually contains.
DOMAIN_MODULES: dict[str, ModuleType] = {
    "bioweapon_counter": bioweapon_counter,
    "targeting_design": targeting_design,
    "toxicology": toxicology,
    "antidote_screening": antidote_screening,
    "exposure_assessment": exposure_assessment,
    "delivery_forensics": delivery_forensics,
}


class DemoResult(TypedDict):
    """Typed shape of :func:`run_demo`.

    Declaring the shape here (rather than returning a bare ``dict[str, object]``
    and re-narrowing it downstream with ``isinstance`` guards that can never
    fire) is what lets :mod:`no_time_to_die.mission` and
    :mod:`no_time_to_die.manuscript_variables` consume the result directly.
    """

    countermeasure: dict[str, object]
    targeting: dict[str, object]
    toxicology_stats: dict[str, float]
    garden_risk_combined: float
    antidote: dict[str, object]
    exposure: dict[str, object]
    forensics: dict[str, object]


#: Fixed DNA reference "genome" for the specificity demonstration.
DEMO_REFERENCE = "AACCGGTTAACCGGTT" * 4

#: Guide candidates to rank — one perfect 50%-GC guide, one one-base off,
#: one reverse-complement style, and one GC-poor degenerate guide.
DEMO_CANDIDATES: tuple[str, ...] = (
    "AACCGGTTAACCGGTT",
    "AACCGGTTAACCGGTC",
    "TTGGCCAATTGGCCAA",
    "AAAAAAAAAAAAAAAA",
)

DEMO_MAX_MISMATCHES = 2
DEMO_ABSORPTION_RATE = 1.2
DEMO_EXPOSURE_TIME = 4.0
DEMO_AVIDITY = 3.0
DEMO_SEED = 11

_KNOWN_TOXINS: dict[str, float] = {"ricin": 0.5, "nicotine": 0.4, "cyanide": 0.2}

#: Antidote-screen demonstration concentration (mg/L).
ANTAGONIST_CONC = 10.0

#: Vesper trace-forensics demonstration parameters (deterministic). Hoisted out
#: of :func:`run_demo` so the manuscript's setup table can cite them as tokens
#: rather than repeating the literals in prose.
FORENSIC_SCENARIO: dict[str, float] = {
    "signal": 9.0,
    "noise_rms": 1.0,
    "volume_ml": 0.5,
    "transfer_fraction": 0.1,
    "calibration_slope": 2.0,
    "calibration_intercept": 0.5,
}

#: Unknown residue spectrum recovered from the glass (5-bin relative response).
FORENSIC_UNKNOWN_SPECTRUM: tuple[float, ...] = (0.98, 0.25, 0.12, 0.06, 0.03)

#: Delivery-kinetics figure parameters. These live here rather than inside
#: ``figures/plots.py`` so the rendered curve, its exposure-window marker, and
#: the manuscript caption all read the same constants — the figure previously
#: marked an exposure window that disagreed with ``DEMO_EXPOSURE_TIME``.
DELIVERY_PLOT_DOSE = 100.0
DELIVERY_PLOT_ELIMINATION_RATE = 0.4
DELIVERY_PLOT_HORIZON_H = 12.0

#: Exposure-scenario demonstration parameters (deterministic).
EXPOSURE_SCENARIO: dict[str, float] = {
    "concentration": 0.02,
    "contact_rate": 0.5,
    "duration": 30.0,
    "absorption_fraction": 0.2,
    "elimination_rate": 0.1,
    "noael": 0.5,
    "reference_dose": 0.001,
}


def input_hash() -> str:
    """Canonical sha256 fingerprint of the deterministic demonstration inputs."""
    payload = "|".join(
        [
            DEMO_REFERENCE,
            ",".join(DEMO_CANDIDATES),
            str(DEMO_SEED),
            str(ANTAGONIST_CONC),
            ",".join(f"{k}={v}" for k, v in sorted(EXPOSURE_SCENARIO.items())),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def run_demo() -> DemoResult:
    """Run the full deterministic HERACLES demonstration and return its results.

    Composes six concept results into one JSON-serializable :class:`DemoResult`:
    the countermeasure specificity/delivery model, the guide-design ranking, the
    poison-garden toxicology summary, the antidote screen, the exposure
    assessment, and the vesper trace-detection forensics.
    """
    countermeasure = bioweapon_counter.countermeasure_model(
        DEMO_REFERENCE,
        DEMO_CANDIDATES,
        max_mismatches=DEMO_MAX_MISMATCHES,
        absorption_rate=DEMO_ABSORPTION_RATE,
        exposure_time=DEMO_EXPOSURE_TIME,
        avidity=DEMO_AVIDITY,
    )
    targeting = _targeting_report()
    toxicology_stats = toxicology.catalog_stats()
    garden_risk = toxicology.garden_risk_profile(_KNOWN_TOXINS)
    antidote = _antidote_report()
    exposure = exposure_assessment.exposure_scenario_report(**EXPOSURE_SCENARIO)
    forensics = delivery_forensics.vesper_trace_report(
        signal=FORENSIC_SCENARIO["signal"],
        noise_rms=FORENSIC_SCENARIO["noise_rms"],
        volume_ml=FORENSIC_SCENARIO["volume_ml"],
        transfer_fraction=FORENSIC_SCENARIO["transfer_fraction"],
        calibration_slope=FORENSIC_SCENARIO["calibration_slope"],
        calibration_intercept=FORENSIC_SCENARIO["calibration_intercept"],
        unknown_spectrum=FORENSIC_UNKNOWN_SPECTRUM,
    )
    return {
        "countermeasure": countermeasure,
        "targeting": targeting,
        "toxicology_stats": toxicology_stats,
        "garden_risk_combined": garden_risk["combined_fraction"],
        "antidote": antidote,
        "exposure": exposure,
        "forensics": forensics,
    }


def _targeting_report() -> dict[str, object]:
    """Internal: build the deterministic guide-design report."""
    return targeting_design.design_report(
        DEMO_CANDIDATES,
        (DEMO_REFERENCE,),
        max_mismatches=DEMO_MAX_MISMATCHES,
    )


def _antidote_report() -> dict[str, object]:
    """Internal: build the deterministic antidote-screen report."""
    return antidote_screening.screen_report(
        toxicology.catalog_by_name("ricin"),
        dose=0.5,
        antagonist_conc=ANTAGONIST_CONC,
    )
