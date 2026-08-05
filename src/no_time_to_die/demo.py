"""Canonical deterministic demonstration for the HERACLES mission.

Both the mission adapter (:mod:`no_time_to_die.mission`) and the manuscript
variable generator share one fixed set of demonstration inputs and one
``run_demo`` result so numeric tokens and mission outcomes can never drift.
Everything here is pure and bond-api-free.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from types import ModuleType
from typing import Literal, TypedDict

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
    "ANTIDOTE_SCREEN_DOSE",
    "DEMO_ABSORPTION_RATE",
    "DEMO_AVIDITY",
    "DEMO_CANDIDATES",
    "DEMO_EXPOSURE_TIME",
    "DEMO_MAX_MISMATCHES",
    "DEMO_REFERENCE",
    "DEMO_REFERENCE_SEGMENTS",
    "DEMO_SEED",
    "DOMAIN_MODULES",
    "EXPOSURE_SCENARIO",
    "FORENSIC_SCENARIO",
    "FORENSIC_UNKNOWN_SPECTRUM",
    "GARDEN_DOSES",
    "DemoResult",
    "ReferenceSegment",
    "input_hash",
    "input_payload",
    "planted_segment_counts",
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


@dataclass(frozen=True)
class ReferenceSegment:
    """One labelled 16-nt block of the demonstration reference genome.

    ``role`` declares what the block is *for*; ``guide`` names the candidate it
    relates to (``None`` for a filler); ``distance`` is the Hamming distance
    the block claims to sit at from that guide (``None`` for a filler). The
    declaration is checked against the sequence, never trusted.
    """

    role: Literal["on_target", "near_miss", "filler"]
    guide: str | None
    sequence: str
    distance: int | None


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


#: Fixed DNA reference "genome" for the specificity demonstration, declared as
#: labelled 16-nt segments rather than a single opaque literal.
#:
#: The reference this demonstration used through 2026-08-04 was
#: ``"AACCGGTTAACCGGTT" * 4`` — a periodic string whose period equalled the
#: winning guide's own length. That made the headline numbers *forced by the
#: input rather than discovered*: the winner could only ever score 100%
#: specificity, 0 off-target windows, and 0 population off-target risk, and the
#: ``efficiency * (1 - off_target_risk)`` blend never actually did any work
#: (the top two candidates tied at composite 1.0 and were separated by the
#: alphabetical tie-break, not by the model).
#:
#: This reference plants a known, auditable structure instead: two exact hits
#: for the A-guide, three near-miss windows at declared Hamming distances, and
#: four neutral fillers. The consequence is a demonstration whose outcome is
#: *not* a tautology — specificity lands strictly inside ``(0, 1)``, the winning
#: guide carries a non-zero off-target risk, and the composite blend is what
#: separates the two 1.0-efficiency candidates. ``tests/test_demo_evidence.py``
#: pins each planted window and fails if the demonstration ever degenerates
#: back into a self-fulfilling input.
DEMO_REFERENCE_SEGMENTS: tuple[ReferenceSegment, ...] = (
    ReferenceSegment("on_target", "AACCGGTTAACCGGTT", "AACCGGTTAACCGGTT", 0),
    ReferenceSegment("filler", None, "GATCTAGCATCGGACT", None),
    ReferenceSegment("near_miss", "AACCGGTTAACCGGTT", "AACCGGTTAACCGGAA", 2),
    ReferenceSegment("filler", None, "CTGACTTGCAAGTCAG", None),
    ReferenceSegment("on_target", "AACCGGTTAACCGGTT", "AACCGGTTAACCGGTT", 0),
    ReferenceSegment("near_miss", "TTGGCCAATTGGCCAA", "TTGGCCAATTGGCCAT", 1),
    ReferenceSegment("filler", None, "TCAGGATCCTAGGATC", None),
    ReferenceSegment("near_miss", "TTGGCCAATTGGCCAA", "TTGGCCAATTGGCCTT", 2),
    ReferenceSegment("filler", None, "GTCATGACCTGAATCG", None),
)

#: The concatenated reference genome the demonstration actually scans.
DEMO_REFERENCE = "".join(segment.sequence for segment in DEMO_REFERENCE_SEGMENTS)


def planted_segment_counts() -> dict[str, int]:
    """How many segments of each declared role the reference genome carries.

    The declared roles are not taken on trust: ``tests/test_demo_evidence.py``
    recomputes the Hamming distance of every segment against its declared guide
    and fails if a label and the sequence disagree.
    """
    counts = {"on_target": 0, "near_miss": 0, "filler": 0}
    for segment in DEMO_REFERENCE_SEGMENTS:
        counts[segment.role] += 1
    return counts


#: Guide candidates to rank — one balanced 50%-GC guide, one one-base off,
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

#: Garden-risk demonstration doses (mg/kg) by catalog toxin name.
GARDEN_DOSES: dict[str, float] = {"ricin": 0.5, "nicotine": 0.4, "cyanide": 0.2}

#: Ricin dose (mg/kg) the antidote library is screened against.
ANTIDOTE_SCREEN_DOSE = 0.5

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


def input_payload() -> str:
    """Canonical, labelled serialization of every demonstration input.

    Written out explicitly (rather than reflected off module globals) so the
    ordering — and therefore :func:`input_hash` — is stable across refactors.
    Completeness is not left to good intentions:
    ``tests/test_demo_evidence.py`` independently scans this module's public
    constants and asserts each one appears here under its own name, so a
    constant added without a payload line fails the build instead of quietly
    leaving the "canonical input digest" unchanged when the inputs changed.

    The pre-2026-08-05 digest covered only five of the sixteen inputs.
    """
    parts = [
        f"demo_reference={DEMO_REFERENCE}",
        "demo_candidates=" + ",".join(DEMO_CANDIDATES),
        f"demo_max_mismatches={DEMO_MAX_MISMATCHES}",
        f"demo_absorption_rate={DEMO_ABSORPTION_RATE}",
        f"demo_exposure_time={DEMO_EXPOSURE_TIME}",
        f"demo_avidity={DEMO_AVIDITY}",
        f"demo_seed={DEMO_SEED}",
        f"antagonist_conc={ANTAGONIST_CONC}",
        f"antidote_screen_dose={ANTIDOTE_SCREEN_DOSE}",
        f"delivery_plot_dose={DELIVERY_PLOT_DOSE}",
        f"delivery_plot_elimination_rate={DELIVERY_PLOT_ELIMINATION_RATE}",
        f"delivery_plot_horizon_h={DELIVERY_PLOT_HORIZON_H}",
        "garden_doses=" + ",".join(f"{k}={v}" for k, v in sorted(GARDEN_DOSES.items())),
        "exposure_scenario=" + ",".join(f"{k}={v}" for k, v in sorted(EXPOSURE_SCENARIO.items())),
        "forensic_scenario=" + ",".join(f"{k}={v}" for k, v in sorted(FORENSIC_SCENARIO.items())),
        "forensic_unknown_spectrum=" + ",".join(str(v) for v in FORENSIC_UNKNOWN_SPECTRUM),
    ]
    return "|".join(parts)


def input_hash() -> str:
    """Canonical sha256 fingerprint of the deterministic demonstration inputs."""
    return hashlib.sha256(input_payload().encode("utf-8")).hexdigest()


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
    garden_risk = toxicology.garden_risk_profile(GARDEN_DOSES)
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
        dose=ANTIDOTE_SCREEN_DOSE,
        antagonist_conc=ANTAGONIST_CONC,
    )
