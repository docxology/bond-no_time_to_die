"""Tests for targeting_design.py — guide design & population off-target."""

from __future__ import annotations

import math

import pytest

from no_time_to_die.targeting_design import (
    GuideScore,
    design_report,
    gc_content,
    guide_efficiency,
    longest_homopolymer,
    population_off_target_risk,
    positional_bonus,
    rank_guides,
)


class TestGcContent:
    def test_pure_a(self) -> None:
        assert gc_content("AAAA") == 0.0

    def test_pure_gc(self) -> None:
        assert gc_content("GCGC") == 1.0

    def test_mixed(self) -> None:
        assert gc_content("ACGT") == 0.5

    def test_invalid_raises(self) -> None:
        with pytest.raises(ValueError):
            gc_content("ACGU")
        with pytest.raises(ValueError):
            gc_content("")


class TestLongestHomopolymer:
    def test_single_base(self) -> None:
        assert longest_homopolymer("AAAA") == 4

    def test_no_run(self) -> None:
        assert longest_homopolymer("ACGTACGT") == 1

    def test_double_run(self) -> None:
        assert longest_homopolymer("AACCGGTT") == 2


class TestPositionalBonus:
    def test_aligned_weights(self) -> None:
        # "ACGT" : G and C at positions 1 and 2 -> weights[1]+weights[2]=0.5
        bonus = positional_bonus("ACGT", weights=(0.0, 0.3, 0.2, 0.0))
        assert bonus == pytest.approx(0.125)  # (0.3+0.2)/4

    def test_misaligned_weights_raises(self) -> None:
        with pytest.raises(ValueError):
            positional_bonus("ACGT", weights=(1.0,))

    def test_invalid_sequence_raises(self) -> None:
        with pytest.raises(ValueError):
            positional_bonus("ACGU", weights=(1.0, 1.0, 1.0, 1.0))


class TestGuideEfficiency:
    def test_perfect_balanced(self) -> None:
        # GC exactly 0.5, no homopolymer > 2 -> efficiency 1.0
        assert guide_efficiency("AACCGGTTAACCGGTT") == pytest.approx(1.0)

    def test_gc_poor_clamped(self) -> None:
        # GC 0, homopolymer 16 -> base < 0 clamped to 0
        assert guide_efficiency("AAAAAAAAAAAAAAAA") == 0.0

    def test_positional_bonus_applied(self) -> None:
        # GC 0.5 but a homopolymer run of 4 drags the base below 1.0; the
        # positional G/C bonus lifts it back to the clamped ceiling.
        guide = "AAAACCCCGGGGTTTT"
        weights = (0.2,) * len(guide)
        assert guide_efficiency(guide) < guide_efficiency(guide, weights=weights)
        assert guide_efficiency(guide, weights=weights) == pytest.approx(1.0)

    def test_invalid_raises(self) -> None:
        with pytest.raises(ValueError):
            guide_efficiency("ACGU")

    def test_misaligned_weights_raises(self) -> None:
        with pytest.raises(ValueError):
            guide_efficiency("AACCGGTT", weights=(1.0,))


class TestPopulationOffTargetRisk:
    def test_known_single_near_match(self) -> None:
        # guide AAAA in AAAATTTT, max_mismatches=1 -> one d=1 window (offset 1)
        risk = population_off_target_risk("AAAA", ("AAAATTTT",), max_mismatches=1)
        assert risk == pytest.approx(math.exp(-0.5))

    def test_more_mismatch_weighs_less(self) -> None:
        # Raising the tolerance admits d=2..4 windows, so the loose total must
        # exceed the single d=1 window while each far mismatch weighs less.
        risk_tight = population_off_target_risk("AAAA", ("AAAATTTT",), max_mismatches=1)
        risk_loose = population_off_target_risk("AAAA", ("AAAATTTT",), max_mismatches=4)
        assert risk_tight == pytest.approx(math.exp(-0.5))
        assert risk_loose > risk_tight
        assert risk_loose < 2.0  # bounded: far near-misses decay fast

    def test_no_matches_zero(self) -> None:
        assert population_off_target_risk("GGGG", ("AAAA",), max_mismatches=2) == 0.0

    def test_empty_genomes_raises(self) -> None:
        with pytest.raises(ValueError):
            population_off_target_risk("AAAA", ())

    def test_short_genome_raises(self) -> None:
        with pytest.raises(ValueError):
            population_off_target_risk("AAAAGG", ("AAAA",))

    def test_negative_tolerance_raises(self) -> None:
        with pytest.raises(ValueError):
            population_off_target_risk("AAAA", ("AAAAAA",), max_mismatches=-1)

    def test_negative_weight_raises(self) -> None:
        with pytest.raises(ValueError):
            population_off_target_risk("AAAA", ("AAAAAA",), distance_weight=-1.0)

    def test_invalid_guide_raises(self) -> None:
        with pytest.raises(ValueError):
            population_off_target_risk("AAAU", ("AAAAAA",))


class TestRankGuides:
    def test_ranks_clean_guide_first(self) -> None:
        ranked = rank_guides(("AAAAAAAAAAAAAAAA", "AACCGGTTAACCGGTT"), ("AACCGGTTAACCGGTT",))
        assert ranked[0].guide == "AACCGGTTAACCGGTT"
        assert isinstance(ranked[0], GuideScore)

    def test_composite_scored(self) -> None:
        ranked = rank_guides(("AACCGGTTAACCGGTT",), ("AACCGGTTAACCGGTT",))
        assert ranked[0].efficiency == pytest.approx(1.0)
        assert ranked[0].composite == pytest.approx(1.0)

    def test_empty_candidates_raises(self) -> None:
        with pytest.raises(ValueError):
            rank_guides((), ("AACCGGTT",))


class TestDesignReport:
    def test_report_shape(self) -> None:
        report = design_report(("AACCGGTTAACCGGTT", "AAAAAAAAAAAAAAAA"), ("AACCGGTTAACCGGTT",))
        assert report["num_guides"] == 2
        assert report["best_guide"] == "AACCGGTTAACCGGTT"
        assert report["best_efficiency"] == pytest.approx(1.0)
        assert report["best_composite"] == pytest.approx(1.0)
        ranked = report["ranked"]
        assert isinstance(ranked, tuple)
        assert len(ranked) == 2
