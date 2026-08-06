"""HERACLES — the no_time_to_die film mission (No Time to Die, 2021).

This is the thin adapter between the package's pure domain core
(:mod:`no_time_to_die.bioweapon_counter`, :mod:`no_time_to_die.targeting_design`,
:mod:`no_time_to_die.toxicology`, :mod:`no_time_to_die.antidote_screening`,
:mod:`no_time_to_die.exposure_assessment`,
:mod:`no_time_to_die.delivery_forensics`) and the frozen bond-api mission
protocol. It implements :class:`~bond_api.protocol.MissionProvider` so the
orchestrator can discover and drive this film purely through
``bond_api.discovery`` / ``bond_api.registry``.

Discovery contract (bond-api): a film package is a top-level module named by
its slug (``no_time_to_die``) exposing ``mission.MissionProvider``. The class
here is named ``MissionProvider``; a module-level ``PROVIDER`` instance and a
populated :class:`~bond_api.registry.GadgetRegistry` are also exported so
coordinators and scripts bind without re-importing.

Only this adapter imports bond-api; the domain modules under this package are
pure and importable in isolation.
"""

from __future__ import annotations

from bond_api.protocol import (  # type: ignore[import-untyped]
    Asset,
    Constraint,
    Debrief,
    Finding,
    MissionBrief,
    MissionOutcome,
    MissionPlan,
    Provenance,
    ReconReport,
    ReconRequest,
    Step,
)
from bond_api.registry import GadgetRegistry  # type: ignore[import-untyped]

from no_time_to_die import (
    __version__,
    antidote_screening,
    delivery_forensics,
    demo,
    toxicology,
)

__all__ = [
    "CODENAME",
    "GADGET_REGISTRY",
    "PROVIDER",
    "MissionProvider",
    "register_gadgets",
]

#: Mission codename for this film.
CODENAME = "HERACLES"

#: Module-level gadget registry; populated at import (deterministic merge).
GADGET_REGISTRY = GadgetRegistry()


def register_gadgets(registry: GadgetRegistry | None = None) -> GadgetRegistry:
    """Register the film's domain modules as gadgets on a registry.

    Uses :data:`GADGET_REGISTRY` unless an explicit ``registry`` is supplied —
    coordinators pass their own :class:`bond_api.registry.GadgetRegistry`. The
    gadget payload is a ``{name: module}`` mapping taken verbatim from
    :data:`no_time_to_die.demo.DOMAIN_MODULES`, so the registry can never
    advertise a different module set than the package actually ships. Returns
    the registry.
    """
    target = GADGET_REGISTRY if registry is None else registry
    target.register("no_time_to_die", dict(demo.DOMAIN_MODULES))
    return target


class MissionProvider:
    """Deterministic HERACLES implementation of the frozen mission protocol."""

    film = "no_time_to_die"

    def brief(self) -> MissionBrief:
        """Declare the HERACLES mission: six pharmaco-forensic objectives."""
        return MissionBrief(
            film=self.film,
            codename=CODENAME,
            objectives=(
                "assess DNA-targeted bioweapon countermeasure specificity and delivery",
                "design and rank the countermeasure guide across a population",
                "characterize poison-garden dose-response toxicology",
                "screen competitive-antagonist antidotes against a toxin dose",
                "assess poison exposure pathways and cumulative risk",
                "run vesper poison-delivery trace detection forensics",
            ),
            assets=(
                Asset(kind="module", name="bioweapon_counter", payload=demo.DEMO_REFERENCE),
                Asset(kind="module", name="targeting_design", payload=demo.DEMO_CANDIDATES),
                Asset(kind="module", name="toxicology", payload=len(toxicology.TOXIN_CATALOG)),
                Asset(
                    kind="module",
                    name="antidote_screening",
                    payload=len(antidote_screening.ANTIDOTE_LIBRARY),
                ),
                Asset(kind="module", name="exposure_assessment", payload=demo.EXPOSURE_SCENARIO),
                Asset(kind="module", name="delivery_forensics", payload=CODENAME),
            ),
            constraints=(
                Constraint(kind="determinism", detail="no clock, no RNG, no external calls"),
                Constraint(kind="protocol", detail="frozen bond-api types only"),
            ),
        )

    def recon(self, request: ReconRequest) -> ReconReport:
        """Survey the request, the domain assets, and the determinism constraint."""
        return ReconReport(
            findings=(
                Finding(label="goal", detail=request.goal),
                Finding(
                    label="assets",
                    detail=f"catalog holds {len(toxicology.TOXIN_CATALOG)} flora toxins",
                ),
                Finding(label="constraints", detail="deterministic execution required"),
            )
        )

    def plan(self, brief: MissionBrief) -> MissionPlan:
        """Plan one step per domain concept, ordered by evidence dependency."""
        return MissionPlan(
            steps=(
                Step(
                    name="countermeasure",
                    action="assess_specificity",
                    params={"objectives": len(brief.objectives)},
                ),
                Step(
                    name="targeting",
                    action="rank_guides",
                    params={
                        "candidates": len(demo.DEMO_CANDIDATES),
                        "max_mismatches": demo.DEMO_MAX_MISMATCHES,
                    },
                ),
                Step(
                    name="toxicology",
                    action="catalog_dose_response",
                    params={"flora": len(toxicology.TOXIN_CATALOG)},
                ),
                Step(
                    name="antidote",
                    action="screen_antagonists",
                    params={"antidotes": len(antidote_screening.ANTIDOTE_LIBRARY)},
                ),
                Step(
                    name="exposure",
                    action="assess_pathway",
                    params={"duration": demo.EXPOSURE_SCENARIO["duration"]},
                ),
                Step(
                    name="forensics",
                    action="vesper_trace",
                    params={"lod_snr": delivery_forensics.DEFAULT_LOD_SNR},
                ),
            )
        )

    def execute(self, plan: MissionPlan) -> MissionOutcome:
        """Run the deterministic domain assessment and return a full outcome."""
        results = demo.run_demo()
        forensics = results["forensics"]
        return MissionOutcome(
            success=True,
            results={
                "steps_planned": len(plan.steps),
                "steps": tuple(step.name for step in plan.steps),
                "countermeasure": results["countermeasure"],
                "targeting": results["targeting"],
                "toxicology_stats": results["toxicology_stats"],
                "garden_risk_combined": results["garden_risk_combined"],
                "antidote": results["antidote"],
                "exposure": results["exposure"],
                "forensics_top_match": forensics.get("top_match"),
                "forensics_recovered_dose": forensics.get("recovered_dose"),
            },
            provenance=Provenance(
                package_version=__version__,
                seed=demo.DEMO_SEED,
                input_hash=demo.input_hash(),
                wall_time_s=0.0,
            ),
        )

    def debrief(self, outcome: MissionOutcome) -> Debrief:
        """Summarize the mission and record the standing HERACLES lessons."""
        return Debrief(
            outcome=outcome,
            lessons=(
                "target specificity is the binding constraint on a DNA countermeasure",
                "deterministic provenance is mandatory for every mission outcome",
                "the garden catalog and the forensic library are the evidence ledger",
            ),
        )


#: Stable top-level provider instance (discovery/coordinator binding point).
PROVIDER = MissionProvider()

# Populate the module-level gadget registry at import (idempotent merge).
register_gadgets()
