"""Bind ``data/claim_ledger.yaml`` to the constants it claims to register.

The ledger header asserts that *every* numeric constant the demonstration
consumes is registered with its live value. Before this file existed nothing
checked that, and the assertion was false: all seven Hill coefficients, every
demonstration scalar, the whole forensic calibration, and the guide-design model
parameters were absent.

The expected id set here is **derived from the modules**, never hand-listed, so
the check cannot go stale:

* a new ``ALL_CAPS`` constant of a registrable type in any domain module fails
  the build until it is registered;
* a catalog/library/spectrum entry added to ``TOXIN_CATALOG``,
  ``ANTIDOTE_LIBRARY``, or ``SPECTRUM_LIBRARY`` fails the same way;
* a ledger entry whose constant was deleted fails as an orphan;
* a value edited on either side without the other fails on comparison.

``TestLedgerGateCanFail`` proves each of those three failure modes with a real
mutated ledger rather than asserting that the gate is strict.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest
import yaml

from no_time_to_die import (
    antidote_screening,
    delivery_forensics,
    demo,
    targeting_design,
    toxicology,
)

_PKG = Path(__file__).resolve().parents[1]
LEDGER_PATH = _PKG / "data" / "claim_ledger.yaml"

#: Modules whose module-level constants must be registered. ``demo`` carries the
#: demonstration inputs; the rest carry model parameters and catalogs.
_SCANNED_MODULES = (
    demo,
    toxicology,
    antidote_screening,
    delivery_forensics,
    targeting_design,
)


def _is_registrable(value: object) -> bool:
    """Whether a module-level constant is a numeric/sequence claim.

    Registrable: a number, a DNA/label string, a non-empty tuple of numbers or
    strings, or a non-empty mapping of names to numbers. Not registrable:
    booleans, module maps (``DOMAIN_MODULES``), alphabet frozensets, paths, and
    the structured catalogs/libraries, which are expanded per entry below.
    """
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float, str)):
        return True
    if isinstance(value, tuple):
        return bool(value) and all(isinstance(item, (int, float, str)) for item in value)
    if isinstance(value, dict):
        return bool(value) and all(isinstance(item, (int, float)) for item in value.values())
    return False


def live_constants() -> dict[str, Any]:
    """Build the id -> value map the ledger must mirror, straight from the code.

    Ids follow one mechanical rule so nothing is hand-maintained: a module
    constant registers under its lowercased name; a catalog/library entry
    registers under ``<field>_<entry name>``.
    """
    live: dict[str, Any] = {}
    for module in _SCANNED_MODULES:
        for name, value in vars(module).items():
            if name.startswith("_") or not name.isupper():
                continue
            if _is_registrable(value):
                live[name.lower()] = list(value) if isinstance(value, tuple) else value
    # Structured containers, expanded to one claim per entry.
    for toxin in toxicology.TOXIN_CATALOG:
        live[f"ld50_{toxin.name}"] = toxin.ld50_mg_kg
        live[f"hill_{toxin.name}"] = toxin.hill_coefficient
    for antidote in antidote_screening.ANTIDOTE_LIBRARY:
        live[f"ki_{antidote.name}"] = antidote.ki
    for poison, spectrum in delivery_forensics.SPECTRUM_LIBRARY.items():
        live[f"spectrum_{poison}"] = list(spectrum)
    return live


def load_ledger(path: Path | None = None) -> dict[str, Any]:
    """Parse the ledger into an id -> claim mapping, rejecting duplicate ids."""
    raw = yaml.safe_load((path or LEDGER_PATH).read_text(encoding="utf-8"))
    claims = raw["claims"]
    by_id: dict[str, Any] = {}
    for claim in claims:
        assert claim["id"] not in by_id, f"duplicate ledger id {claim['id']}"
        by_id[claim["id"]] = claim
    return by_id


def check_ledger(ledger: dict[str, Any], live: dict[str, Any]) -> list[str]:
    """Return every disagreement between a ledger and the live constants."""
    problems = [f"unregistered constant: {key}" for key in sorted(set(live) - set(ledger))]
    problems += [f"orphaned ledger entry: {key}" for key in sorted(set(ledger) - set(live))]
    for key in sorted(set(live) & set(ledger)):
        recorded = ledger[key].get("value")
        if recorded != live[key]:
            problems.append(f"value drift on {key}: ledger {recorded!r} vs code {live[key]!r}")
    return problems


class TestLedgerMatchesTheCode:
    def test_every_constant_is_registered_with_its_live_value(self) -> None:
        assert check_ledger(load_ledger(), live_constants()) == []

    def test_the_scan_actually_finds_constants(self) -> None:
        """Guard against a vacuous pass from an empty derived set."""
        live = live_constants()
        assert len(live) > 40, f"derived only {len(live)} constants; the scan has gone blind"
        # Spot-check one representative of each derivation path.
        assert live["hill_ricin"] == 2.0
        assert live["ki_naloxone"] == 0.4
        assert live["spectrum_ricin"] == [1.0, 0.2, 0.1, 0.05, 0.02]
        assert live["demo_exposure_time"] == 4.0
        assert live["exposure_scenario"]["noael"] == 0.5

    def test_every_claim_declares_a_provenance_class(self) -> None:
        for claim_id, claim in load_ledger().items():
            assert isinstance(claim.get("synthetic"), bool), (
                f"{claim_id} does not declare synthetic true/false"
            )
            assert str(claim.get("source", "")).strip(), f"{claim_id} has no source label"

    def test_no_antidote_ki_is_presented_as_a_measurement(self) -> None:
        """The withdrawn claim stays withdrawn.

        All five Ki values were labelled "Published approximation" and left
        unflagged; they are invented. If anyone re-flips one to
        ``synthetic: false`` this fails.
        """
        ledger = load_ledger()
        for antidote in antidote_screening.ANTIDOTE_LIBRARY:
            claim = ledger[f"ki_{antidote.name}"]
            assert claim["synthetic"] is True
            assert "published" not in claim["source"].lower()


class TestLedgerGateCanFail:
    """Positive controls: each failure mode is produced and observed."""

    def test_unregistered_constant_is_reported(self) -> None:
        ledger = load_ledger()
        live = live_constants()
        live["newly_added_demo_constant"] = 42.0
        problems = check_ledger(ledger, live)
        assert problems == ["unregistered constant: newly_added_demo_constant"]

    def test_orphaned_ledger_entry_is_reported(self) -> None:
        ledger = load_ledger()
        ledger["retired_constant"] = {"id": "retired_constant", "value": 1.0}
        problems = check_ledger(ledger, live_constants())
        assert problems == ["orphaned ledger entry: retired_constant"]

    def test_value_drift_is_reported(self) -> None:
        ledger = copy.deepcopy(load_ledger())
        ledger["ld50_ricin"]["value"] = 999.0
        problems = check_ledger(ledger, live_constants())
        assert problems == ["value drift on ld50_ricin: ledger 999.0 vs code 1.0"]

    def test_a_mutated_ledger_file_fails_the_real_check(self, tmp_path) -> None:
        """End-to-end through the real parser, not just the comparison helper."""
        raw = yaml.safe_load(LEDGER_PATH.read_text(encoding="utf-8"))
        raw["claims"] = [c for c in raw["claims"] if c["id"] != "hill_cyanide"]
        mutated = tmp_path / "claim_ledger.yaml"
        mutated.write_text(yaml.safe_dump(raw), encoding="utf-8")
        problems = check_ledger(load_ledger(mutated), live_constants())
        assert problems == ["unregistered constant: hill_cyanide"]

    def test_duplicate_ids_are_rejected(self, tmp_path) -> None:
        raw = yaml.safe_load(LEDGER_PATH.read_text(encoding="utf-8"))
        raw["claims"].append({"id": "ld50_ricin", "value": 1.0})
        mutated = tmp_path / "claim_ledger.yaml"
        mutated.write_text(yaml.safe_dump(raw), encoding="utf-8")
        with pytest.raises(AssertionError, match="duplicate ledger id"):
            load_ledger(mutated)
