"""Tests for mission.py — the HERACLES bond-api MissionProvider adapter."""

from __future__ import annotations

from pathlib import Path

import pytest
from bond_api.discovery import load_provider
from bond_api.protocol import MissionProvider as ProtocolProvider
from bond_api.protocol import run_mission
from bond_api.registry import GadgetRegistry

from no_time_to_die import demo
from no_time_to_die.mission import (
    CODENAME,
    GADGET_REGISTRY,
    PROVIDER,
    MissionProvider,
    register_gadgets,
)

_SRC = Path(__file__).resolve().parents[1] / "src"


class TestProviderIdentity:
    def test_film_slug(self) -> None:
        assert PROVIDER.film == "no_time_to_die"

    def test_codename(self) -> None:
        assert CODENAME == "HERACLES"

    def test_runtime_checkable_protocol(self) -> None:
        assert isinstance(PROVIDER, ProtocolProvider)

    def test_class_name_is_provider(self) -> None:
        assert MissionProvider.__name__ == "MissionProvider"


class TestLifecycle:
    def test_brief(self) -> None:
        brief = PROVIDER.brief()
        assert brief.codename == "HERACLES"
        assert len(brief.objectives) == 6
        assert len(brief.assets) == 6
        assert any(a.name == "toxicology" for a in brief.assets)
        assert any(a.name == "targeting_design" for a in brief.assets)

    def test_recon(self) -> None:
        from bond_api.protocol import ReconRequest

        report = PROVIDER.recon(ReconRequest(goal="assess the island"))
        assert len(report.findings) == 3
        assert report.findings[0].label == "goal"

    def test_plan(self) -> None:
        plan = PROVIDER.plan(PROVIDER.brief())
        names = tuple(step.name for step in plan.steps)
        assert names == (
            "countermeasure",
            "targeting",
            "toxicology",
            "antidote",
            "exposure",
            "forensics",
        )

    def test_execute_results(self) -> None:
        outcome = PROVIDER.execute(PROVIDER.plan(PROVIDER.brief()))
        assert outcome.success is True
        assert outcome.results["steps_planned"] == 6
        assert outcome.results["forensics_top_match"] == "ricin"
        assert "targeting" in outcome.results
        assert "antidote" in outcome.results
        assert "exposure" in outcome.results

    def test_execute_provenance(self) -> None:
        outcome = PROVIDER.execute(PROVIDER.plan(PROVIDER.brief()))
        assert outcome.provenance.seed == demo.DEMO_SEED == 11
        assert outcome.provenance.input_hash == demo.input_hash()
        assert outcome.provenance.package_version == "1.0.0"

    def test_debrief(self) -> None:
        outcome = PROVIDER.execute(PROVIDER.plan(PROVIDER.brief()))
        debrief = PROVIDER.debrief(outcome)
        assert len(debrief.lessons) == 3
        assert debrief.outcome is outcome


class TestRunMissionFlow:
    def test_full_flow_returns_debrief(self) -> None:
        from bond_api.protocol import ReconRequest

        debrief = run_mission(PROVIDER, ReconRequest(goal="HERACLES"))
        assert debrief.outcome.success is True


class TestGadgets:
    def test_module_registry_populated(self) -> None:
        gadgets = GADGET_REGISTRY.gadgets_for("no_time_to_die")
        assert "bioweapon_counter" in gadgets
        assert "targeting_design" in gadgets
        assert "toxicology" in gadgets
        assert "antidote_screening" in gadgets
        assert "exposure_assessment" in gadgets
        assert "delivery_forensics" in gadgets

    def test_register_on_fresh_registry(self) -> None:
        registry = GadgetRegistry()
        register_gadgets(registry)
        assert registry.contains("no_time_to_die", "toxicology")
        assert registry.lookup("no_time_to_die", "bioweapon_counter") is not None

    def test_register_returns_registry(self) -> None:
        registry = GadgetRegistry()
        assert register_gadgets(registry) is registry

    def test_lookup_missing_raises(self) -> None:
        registry = GadgetRegistry()
        with pytest.raises(KeyError):
            registry.lookup("no_time_to_die", "nope")


class TestDiscovery:
    def test_load_provider_by_slug(self) -> None:
        provider = load_provider("no_time_to_die", search_paths=[str(_SRC)])
        assert provider.film == "no_time_to_die"
        assert isinstance(provider, ProtocolProvider)

    def test_discover_finds_film(self) -> None:
        from bond_api.discovery import discover

        found = discover(slugs=["no_time_to_die"], search_paths=[str(_SRC)])
        assert "no_time_to_die" in found
        assert found["no_time_to_die"].film == "no_time_to_die"


class TestPureCoreIsolation:
    def test_pure_domain_modules_never_import_bond_api(self) -> None:
        # The domain core must be liftable without the protocol layer; scan
        # their sources for any bond_api reference (a guardrail, not a mock).
        import inspect

        from no_time_to_die import (
            antidote_screening,
            bioweapon_counter,
            delivery_forensics,
            demo,
            exposure_assessment,
            targeting_design,
            toxicology,
        )

        modules = (
            antidote_screening,
            bioweapon_counter,
            delivery_forensics,
            demo,
            exposure_assessment,
            targeting_design,
            toxicology,
        )
        for module in modules:
            source = inspect.getsource(module)
            assert "bond_api" not in source, f"{module.__name__} references bond_api"
