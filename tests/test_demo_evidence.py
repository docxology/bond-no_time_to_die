"""Keep the demonstration from proving things its own inputs guarantee.

Through 2026-08-04 ``DEMO_REFERENCE`` was ``"AACCGGTTAACCGGTT" * 4``: a
period-16 string scanned by a 16-nt guide. Three headline results were therefore
arithmetic consequences of the input rather than findings —

* target specificity was 100% because a periodic reference cannot contain a
  window at Hamming distance 1 or 2 from its own period;
* population off-target risk was 0.0 for the same reason;
* the ``efficiency * (1 - off_target_risk)`` blend collapsed to raw efficiency,
  leaving the top two candidates tied at composite 1.0 and separating them by
  the alphabetical tie-break, so the advertised blend never ran.

The reference is now assembled from labelled segments with a planted structure.
This file does two jobs. First it checks the *declaration* against the sequence
— a segment claiming "near-miss at distance 2" must actually sit at distance 2
from the guide it names, so the documented structure cannot be a comfortable
fiction. Second it asserts non-degeneracy: each of the three collapses above is
a failing condition, checked by a property that the old reference violates and
the new one satisfies. ``TestDegeneracyIsDetected`` runs those same properties
against the old periodic reference and confirms every one of them reports it.
"""

from __future__ import annotations

import pytest

from no_time_to_die import bioweapon_counter as bc
from no_time_to_die import demo
from no_time_to_die import targeting_design as td

#: The degenerate reference this package used to ship, kept as a negative
#: control so the anti-degeneracy properties are demonstrably able to fail.
LEGACY_PERIODIC_REFERENCE = "AACCGGTTAACCGGTT" * 4


def specificity_of(guide: str, reference: str) -> tuple[int, int, float]:
    """``(on_target, off_target, specificity)`` for a guide against a genome."""
    on_target, off_target = bc.count_window_matches(guide, reference, demo.DEMO_MAX_MISMATCHES)
    return on_target, off_target, bc.compute_specificity(on_target, off_target)


def ranking_over(reference: str) -> tuple[dict[str, object], ...]:
    """The guide-design ranked table against an arbitrary reference."""
    report = td.design_report(
        demo.DEMO_CANDIDATES, (reference,), max_mismatches=demo.DEMO_MAX_MISMATCHES
    )
    ranked = report["ranked"]
    assert isinstance(ranked, tuple)
    return ranked


class TestPlantedStructureIsReal:
    """Every segment's declared role is recomputed from its sequence."""

    def test_segments_concatenate_to_the_reference(self) -> None:
        assert "".join(s.sequence for s in demo.DEMO_REFERENCE_SEGMENTS) == demo.DEMO_REFERENCE
        assert len(demo.DEMO_REFERENCE) == 144

    def test_every_declared_distance_is_the_true_distance(self) -> None:
        checked = 0
        for segment in demo.DEMO_REFERENCE_SEGMENTS:
            if segment.guide is None:
                assert segment.role == "filler"
                assert segment.distance is None
                continue
            actual = bc.hamming_distance(segment.guide, segment.sequence)
            assert actual == segment.distance, (
                f"segment {segment.sequence} claims distance {segment.distance} "
                f"from {segment.guide} but is at {actual}"
            )
            checked += 1
        assert checked == 5, "expected 2 on-target + 3 near-miss labelled segments"

    def test_roles_agree_with_distances(self) -> None:
        for segment in demo.DEMO_REFERENCE_SEGMENTS:
            if segment.role == "on_target":
                assert segment.distance == 0
            elif segment.role == "near_miss":
                assert segment.distance is not None
                assert 1 <= segment.distance <= demo.DEMO_MAX_MISMATCHES

    def test_fillers_are_far_from_every_candidate(self) -> None:
        """A "neutral" filler that is secretly a near-miss would inflate risk."""
        for segment in demo.DEMO_REFERENCE_SEGMENTS:
            if segment.role != "filler":
                continue
            for candidate in demo.DEMO_CANDIDATES:
                distance = bc.hamming_distance(candidate, segment.sequence)
                assert distance > demo.DEMO_MAX_MISMATCHES, (
                    f"filler {segment.sequence} is only {distance} from {candidate}"
                )

    def test_planted_counts_match_the_segments(self) -> None:
        counts = demo.planted_segment_counts()
        assert counts == {"on_target": 2, "near_miss": 3, "filler": 4}
        assert sum(counts.values()) == len(demo.DEMO_REFERENCE_SEGMENTS)


class TestResultsAreNotForcedByTheInput:
    def test_specificity_is_strictly_inside_the_unit_interval(self) -> None:
        results = demo.run_demo()
        specificity = results["countermeasure"]["specificity"]
        assert isinstance(specificity, float)
        assert 0.0 < specificity < 1.0, (
            "a specificity pinned at 0 or 1 carries no information about the model"
        )

    def test_the_winning_guide_has_both_hit_classes_available(self) -> None:
        results = demo.run_demo()
        assert results["countermeasure"]["on_target"] == 2.0
        assert results["countermeasure"]["off_target"] == 1.0

    def test_the_off_target_term_actually_erodes_the_winner(self) -> None:
        """If best_off_target_risk is 0 the blend is inert by construction."""
        targeting = demo.run_demo()["targeting"]
        risk = targeting["best_off_target_risk"]
        efficiency = targeting["best_efficiency"]
        composite = targeting["best_composite"]
        assert isinstance(risk, float) and isinstance(efficiency, float)
        assert isinstance(composite, float)
        assert risk > 0.0, "the population off-target term contributed nothing"
        assert composite < efficiency, "the blend left the efficiency untouched"
        assert composite == pytest.approx(efficiency * (1.0 - risk))

    def test_the_blend_and_not_the_tie_break_decides_the_winner(self) -> None:
        ranked = ranking_over(demo.DEMO_REFERENCE)
        top, runner_up = ranked[0], ranked[1]
        assert top["efficiency"] == runner_up["efficiency"], (
            "this check is only meaningful while two candidates tie on efficiency"
        )
        assert top["composite"] > runner_up["composite"], (
            "the top two are separated by the alphabetical tie-break, not the model"
        )

    def test_both_selectors_agree_so_the_prose_can_cite_either(self) -> None:
        results = demo.run_demo()
        assert results["countermeasure"]["best_guide"] == results["targeting"]["best_guide"]


class TestDegeneracyIsDetected:
    """The same properties, run against the retired periodic reference."""

    def test_legacy_reference_forces_perfect_specificity(self) -> None:
        on_target, off_target, specificity = specificity_of(
            demo.DEMO_CANDIDATES[0], LEGACY_PERIODIC_REFERENCE
        )
        assert (on_target, off_target) == (7, 0)
        assert specificity == 1.0  # the property above rejects exactly this

    def test_legacy_reference_zeroes_the_off_target_term(self) -> None:
        risk = td.population_off_target_risk(
            demo.DEMO_CANDIDATES[0],
            (LEGACY_PERIODIC_REFERENCE,),
            max_mismatches=demo.DEMO_MAX_MISMATCHES,
        )
        assert risk == 0.0  # the property above requires risk > 0

    def test_legacy_reference_leaves_the_top_two_tied(self) -> None:
        ranked = ranking_over(LEGACY_PERIODIC_REFERENCE)
        assert ranked[0]["composite"] == ranked[1]["composite"] == 1.0

    def test_current_reference_passes_where_the_legacy_one_fails(self) -> None:
        """Both references through one comparison, so the contrast is explicit."""
        _, _, legacy = specificity_of(demo.DEMO_CANDIDATES[0], LEGACY_PERIODIC_REFERENCE)
        _, _, current = specificity_of(demo.DEMO_CANDIDATES[0], demo.DEMO_REFERENCE)
        assert legacy == 1.0
        assert 0.0 < current < 1.0


class TestInputDigestCoversEveryConstant:
    """The digest must fingerprint the inputs, not a subset of them."""

    def test_every_public_demo_constant_appears_in_the_payload(self) -> None:
        payload = demo.input_payload()
        skipped = {"DOMAIN_MODULES", "DEMO_REFERENCE_SEGMENTS"}
        checked = 0
        for name, value in vars(demo).items():
            if name.startswith("_") or not name.isupper() or name in skipped:
                continue
            if not isinstance(value, (int, float, str, tuple, dict)):
                continue
            assert f"{name.lower()}=" in payload, (
                f"{name} is a demonstration input but the canonical digest ignores it"
            )
            checked += 1
        assert checked >= 15, f"only {checked} constants scanned; the scan has gone blind"

    def test_payload_records_the_planted_reference(self) -> None:
        assert f"demo_reference={demo.DEMO_REFERENCE}" in demo.input_payload()

    def test_payload_expands_every_mapping_entry(self) -> None:
        payload = demo.input_payload()
        for key, value in demo.EXPOSURE_SCENARIO.items():
            assert f"{key}={value}" in payload
        for key, value in demo.FORENSIC_SCENARIO.items():
            assert f"{key}={value}" in payload
