"""Tests for bioweapon_counter.py — the DNA-targeted countermeasure model."""

from __future__ import annotations

import math

import pytest

from no_time_to_die.bioweapon_counter import (
    compute_specificity,
    count_window_matches,
    countermeasure_model,
    delivery_efficacy,
    fraction_delivered,
    hamming_distance,
    neutralization_probability,
    plasma_concentration,
    select_best_guide,
    validate_sequence,
)


class TestValidateSequence:
    def test_valid(self) -> None:
        validate_sequence("ACGTACGT")
        validate_sequence("A")  # single base is valid

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError):
            validate_sequence("")

    def test_invalid_char_raises(self) -> None:
        with pytest.raises(ValueError):
            validate_sequence("ACGTU")  # uracil not in ACGT alphabet

    def test_invalid_characters_are_listed(self) -> None:
        with pytest.raises(ValueError, match="N"):
            validate_sequence("NNN")


class TestHammingDistance:
    def test_identical(self) -> None:
        assert hamming_distance("ACGT", "ACGT") == 0

    def test_single_mismatch(self) -> None:
        assert hamming_distance("ACGT", "ACGA") == 1

    def test_all_mismatch(self) -> None:
        assert hamming_distance("AAAA", "CCCC") == 4

    def test_length_mismatch_raises(self) -> None:
        with pytest.raises(ValueError):
            hamming_distance("ACGT", "ACGTG")

    def test_invalid_raises(self) -> None:
        with pytest.raises(ValueError):
            hamming_distance("ACGU", "ACGT")


class TestCountWindowMatches:
    def test_small_reference(self) -> None:
        # reference has one exact and one one-mismatch window
        target = "ACGT"
        reference = "ACGTACGA"
        on, off = count_window_matches(target, reference, max_mismatches=1)
        assert on == 1  # offset 0: ACGT exact
        assert off == 1  # offset 4: ACGA is a 1-mismatch near-hit

    def test_known_counts(self) -> None:
        target = "AAAA"
        reference = "AAAATTTT"  # window0 exact; window1 is a 1-mismatch near-hit
        on, off = count_window_matches(target, reference, max_mismatches=1)
        assert on == 1
        assert off == 1

    def test_off_target_counted(self) -> None:
        target = "AAAA"
        reference = "AAAATTTT"
        on, off = count_window_matches(target, reference, max_mismatches=4)
        # window 0 exact (on=1); windows 1..4 each differ by <=4 -> off=4
        assert on == 1
        assert off == 4

    def test_negative_tolerance_raises(self) -> None:
        with pytest.raises(ValueError):
            count_window_matches("AAAA", "AAAAAA", max_mismatches=-1)

    def test_short_reference_raises(self) -> None:
        with pytest.raises(ValueError):
            count_window_matches("AAAAAA", "AAAA", max_mismatches=1)

    def test_invalid_sequence_raises(self) -> None:
        with pytest.raises(ValueError):
            count_window_matches("AAAU", "AAAA", max_mismatches=1)


class TestComputeSpecificity:
    def test_basic(self) -> None:
        assert compute_specificity(3, 1) == pytest.approx(0.75)

    def test_perfect(self) -> None:
        assert compute_specificity(5, 0) == 1.0

    def test_zero_total_returns_zero(self) -> None:
        assert compute_specificity(0, 0) == 0.0

    def test_negative_raises(self) -> None:
        with pytest.raises(ValueError):
            compute_specificity(-1, 2)
        with pytest.raises(ValueError):
            compute_specificity(1, -2)


class TestSelectBestGuide:
    def test_selects_cleanest_guide(self) -> None:
        reference = "AAAATTTT"
        # "CCCC" has no matches (spec 0); "AAAA" and "TTTT" tie at spec 0.5,
        # so the deterministic tie-break returns the first.
        best, spec = select_best_guide(reference, ("CCCC", "AAAA", "TTTT"), max_mismatches=1)
        assert best == "AAAA"
        assert spec == pytest.approx(0.5)

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError):
            select_best_guide("AAAATTTT", ())


class TestPlasmaConcentration:
    def test_known_halfpeak(self) -> None:
        # At t where exp(-ke t)==exp(-ka t) symmetrical; check simple case positivity
        c = plasma_concentration(100.0, absorption_rate=1.0, elimination_rate=0.5, time=2.0)
        assert c > 0

    def test_zero_dose_zero(self) -> None:
        assert plasma_concentration(0.0, 1.0, 0.5, 1.0) == 0.0

    def test_time_zero_zero(self) -> None:
        assert plasma_concentration(100.0, 1.0, 0.5, 0.0) == 0.0

    def test_negative_dose_raises(self) -> None:
        with pytest.raises(ValueError):
            plasma_concentration(-1.0, 1.0, 0.5, 1.0)

    def test_nonpositive_absorption_raises(self) -> None:
        with pytest.raises(ValueError):
            plasma_concentration(1.0, 0.0, 0.5, 1.0)

    def test_nonpositive_elimination_raises(self) -> None:
        with pytest.raises(ValueError):
            plasma_concentration(1.0, 1.0, -0.5, 1.0)

    def test_negative_time_raises(self) -> None:
        with pytest.raises(ValueError):
            plasma_concentration(1.0, 1.0, 0.5, -1.0)

    def test_equal_rates_raises(self) -> None:
        with pytest.raises(ValueError):
            plasma_concentration(1.0, 1.0, 1.0, 1.0)


class TestFractionDelivered:
    def test_known_value(self) -> None:
        # 1 - exp(-1*1) = 1 - 1/e
        assert fraction_delivered(1.0, 1.0) == pytest.approx(1 - math.exp(-1.0))

    def test_monotonic_in_time(self) -> None:
        assert fraction_delivered(1.0, 2.0) > fraction_delivered(1.0, 1.0)

    def test_nonpositive_absorption_raises(self) -> None:
        with pytest.raises(ValueError):
            fraction_delivered(0.0, 1.0)

    def test_negative_time_raises(self) -> None:
        with pytest.raises(ValueError):
            fraction_delivered(1.0, -1.0)


class TestDeliveryEfficacy:
    def test_equals_fraction_delivered(self) -> None:
        assert delivery_efficacy(100.0, 1.0, 1.0) == pytest.approx(fraction_delivered(1.0, 1.0))


class TestNeutralizationProbability:
    def test_known(self) -> None:
        # specificity 1.0, delivered 0.5, avidity 1 -> 1.0*0.5*(1/2)=0.25
        assert neutralization_probability(4, 0, 0.5, 1.0) == pytest.approx(0.25)

    def test_zero_avidity(self) -> None:
        assert neutralization_probability(4, 0, 0.5, 0.0) == 0.0

    def test_delivered_fraction_high_raises(self) -> None:
        with pytest.raises(ValueError):
            neutralization_probability(4, 0, 1.5, 1.0)

    def test_delivered_fraction_low_raises(self) -> None:
        with pytest.raises(ValueError):
            neutralization_probability(4, 0, -0.1, 1.0)

    def test_negative_avidity_raises(self) -> None:
        with pytest.raises(ValueError):
            neutralization_probability(4, 0, 0.5, -1.0)

    def test_clamped_upper(self) -> None:
        # all factors approach 1 -> clamped at <= 1
        assert neutralization_probability(1, 0, 1.0, 1e9) <= 1.0


class TestCountermeasureModel:
    def test_returns_full_dict(self) -> None:
        result = countermeasure_model(
            "AAAATTTT",
            ("CCCC", "AAAA", "TTTT"),
            max_mismatches=1,
            absorption_rate=1.0,
            exposure_time=1.0,
            avidity=1.0,
        )
        assert set(result) >= {
            "best_guide",
            "on_target",
            "off_target",
            "specificity",
            "delivered_fraction",
            "neutralization_probability",
        }
        assert result["best_guide"] == "AAAA"
