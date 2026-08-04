"""Canonical deterministic demonstration for the HERACLES mission.

Both the mission adapter (:mod:`no_time_to_die.mission`) and the manuscript
variable generator share one fixed set of demonstration inputs and one
``run_demo`` result so numeric tokens and mission outcomes can never drift.
Everything here is pure and bond-api-free.
"""

from __future__ import annotations

import hashlib

from no_time_to_die import bioweapon_counter, delivery_forensics, toxicology

__all__ = [
    "DEMO_ABSORPTION_RATE",
    "DEMO_AVIDITY",
    "DEMO_CANDIDATES",
    "DEMO_EXPOSURE_TIME",
    "DEMO_MAX_MISMATCHES",
    "DEMO_REFERENCE",
    "DEMO_SEED",
    "input_hash",
    "run_demo",
]

#: Fixed DNA reference "genome" for the specificity demonstration.
DEMO_REFERENCE = "AACCGGTTAACCGGTT" * 4

#: Guide candidates to rank by target specificity.
DEMO_CANDIDATES: tuple[str, ...] = (
    "AACCGGTTAACCGGTT",
    "AACCGGTTAACCGGTC",
    "TTGGCCAATTGGCCAA",
)

DEMO_MAX_MISMATCHES = 2
DEMO_ABSORPTION_RATE = 1.2
DEMO_EXPOSURE_TIME = 4.0
DEMO_AVIDITY = 3.0
DEMO_SEED = 11

_KNOWN_TOXINS: dict[str, float] = {"ricin": 0.5, "nicotine": 0.4, "cyanide": 0.2}


def input_hash() -> str:
    """Canonical sha256 fingerprint of the deterministic demonstration inputs."""
    payload = "|".join([DEMO_REFERENCE, ",".join(DEMO_CANDIDATES), str(DEMO_SEED)])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def run_demo() -> dict[str, object]:
    """Run the full deterministic HERACLES demonstration and return its results.

    Composes the countermeasure specificity/delivery model, the poison-garden
    toxicology summary, and the vesper trace-detection forensics into one
    JSON-serializable result dict.
    """
    countermeasure = bioweapon_counter.countermeasure_model(
        DEMO_REFERENCE,
        DEMO_CANDIDATES,
        max_mismatches=DEMO_MAX_MISMATCHES,
        absorption_rate=DEMO_ABSORPTION_RATE,
        exposure_time=DEMO_EXPOSURE_TIME,
        avidity=DEMO_AVIDITY,
    )
    toxicology_stats = toxicology.catalog_stats()
    garden_risk = toxicology.garden_risk_profile(_KNOWN_TOXINS)
    forensics = delivery_forensics.vesper_trace_report(
        signal=9.0,
        noise_rms=1.0,
        volume_ml=0.5,
        transfer_fraction=0.1,
        calibration_slope=2.0,
        calibration_intercept=0.5,
        unknown_spectrum=(0.98, 0.25, 0.12, 0.06, 0.03),
    )
    return {
        "countermeasure": countermeasure,
        "toxicology_stats": toxicology_stats,
        "garden_risk_combined": garden_risk["combined_fraction"],
        "forensics": forensics,
    }
