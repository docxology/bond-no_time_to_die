"""Tests for delivery_forensics.py — vesper trace detection forensics."""

from __future__ import annotations

import pytest

from no_time_to_die import demo
from no_time_to_die.delivery_forensics import (
    DEFAULT_LOD_SNR,
    cosine_similarity,
    detection_confidence,
    estimate_concentration,
    match_unknown,
    recovered_dose,
    signal_to_noise,
    vesper_trace_report,
)


class TestSignalToNoise:
    def test_value(self) -> None:
        assert signal_to_noise(9.0, 3.0) == pytest.approx(3.0)

    def test_negative_peak_raises(self) -> None:
        with pytest.raises(ValueError):
            signal_to_noise(-1.0, 1.0)

    def test_nonpositive_noise_raises(self) -> None:
        with pytest.raises(ValueError):
            signal_to_noise(1.0, 0.0)


class TestDetectionConfidence:
    def test_at_lod_half(self) -> None:
        assert detection_confidence(DEFAULT_LOD_SNR, DEFAULT_LOD_SNR) == pytest.approx(0.5)

    def test_strong_signal_high_confidence(self) -> None:
        assert detection_confidence(9.0, DEFAULT_LOD_SNR) > 0.99

    def test_zero_snr_low_confidence(self) -> None:
        assert detection_confidence(0.0, DEFAULT_LOD_SNR) < 0.05

    def test_negative_snr_raises(self) -> None:
        with pytest.raises(ValueError):
            detection_confidence(-1.0, DEFAULT_LOD_SNR)

    def test_nonpositive_lod_raises(self) -> None:
        with pytest.raises(ValueError):
            detection_confidence(1.0, 0.0)


class TestEstimateConcentration:
    def test_value(self) -> None:
        assert estimate_concentration(9.0, 2.0, 1.0) == pytest.approx(4.0)

    def test_signal_below_the_intercept_clamps_to_zero(self) -> None:
        """The clamp is at the calibration intercept, not the LOD."""
        assert estimate_concentration(0.5, 2.0, 1.0) == 0.0
        # Exactly at the intercept the inverted line is 0 and does not clamp.
        assert estimate_concentration(1.0, 2.0, 1.0) == 0.0

    def test_below_lod_but_above_intercept_still_returns_a_concentration(self) -> None:
        """Pin the behaviour the methodology used to misdescribe.

        Both the manuscript and this function's docstring said "sub-LOD signals
        clamp to zero". They do not: the clamp compares the signal against the
        calibration intercept, and ``estimate_concentration`` never sees the
        LOD. With the demonstration's intercept (0.5) and LOD SNR (3.0), a
        signal of 1.0 is far below the limit of detection yet yields a positive
        concentration. If anyone ever makes the clamp LOD-aware, this fails and
        the prose must be revisited with it.
        """
        signal = 1.0
        slope = demo.FORENSIC_SCENARIO["calibration_slope"]
        intercept = demo.FORENSIC_SCENARIO["calibration_intercept"]
        assert signal < DEFAULT_LOD_SNR, "premise: the signal is below the limit of detection"
        assert signal > intercept, "premise: the signal is above the calibration intercept"
        assert estimate_concentration(signal, slope, intercept) == pytest.approx(0.25)
        # ... and the detector, which does know the LOD, calls it unlikely.
        assert detection_confidence(signal, DEFAULT_LOD_SNR) < 0.5

    def test_nonpositive_slope_raises(self) -> None:
        with pytest.raises(ValueError):
            estimate_concentration(9.0, 0.0, 1.0)


class TestRecoveredDose:
    def test_value(self) -> None:
        assert recovered_dose(4.0, 0.5, 0.1) == pytest.approx(0.2)

    def test_negative_concentration_raises(self) -> None:
        with pytest.raises(ValueError):
            recovered_dose(-1.0, 1.0, 0.1)

    def test_zero_volume_raises(self) -> None:
        with pytest.raises(ValueError):
            recovered_dose(1.0, 0.0, 0.1)

    def test_high_transfer_raises(self) -> None:
        with pytest.raises(ValueError):
            recovered_dose(1.0, 1.0, 1.5)


class TestCosineSimilarity:
    def test_identical(self) -> None:
        assert cosine_similarity((1.0, 2.0, 3.0), (1.0, 2.0, 3.0)) == pytest.approx(1.0)

    def test_orthogonal(self) -> None:
        assert cosine_similarity((1.0, 0.0), (0.0, 1.0)) == pytest.approx(0.0)

    def test_length_mismatch_raises(self) -> None:
        with pytest.raises(ValueError):
            cosine_similarity((1.0, 2.0), (1.0,))

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError):
            cosine_similarity((), ())

    def test_zero_vector_raises(self) -> None:
        with pytest.raises(ValueError):
            cosine_similarity((0.0, 0.0), (1.0, 1.0))


class TestMatchUnknown:
    def test_top_match(self) -> None:
        ranks = match_unknown((1.0, 0.2, 0.1, 0.05, 0.02))
        assert ranks[0][0] == "ricin"
        assert ranks[0][1] == pytest.approx(1.0)

    def test_empty_library_empty_result(self) -> None:
        assert match_unknown((1.0, 0.0), library={}) == ()

    def test_ranked_descending(self) -> None:
        ranks = match_unknown((0.98, 0.25, 0.12, 0.06, 0.03))
        sims = [sim for _, sim in ranks]
        assert sims == sorted(sims, reverse=True)

    def test_known_library_respected(self) -> None:
        custom = {"a": (1.0, 0.0)}
        assert match_unknown((1.0, 0.0), library=custom)[0][0] == "a"


class TestVesperTraceReport:
    def test_full_report(self) -> None:
        report = vesper_trace_report(
            signal=9.0,
            noise_rms=1.0,
            volume_ml=0.5,
            transfer_fraction=0.1,
            calibration_slope=2.0,
            calibration_intercept=0.5,
        )
        assert report["snr"] == pytest.approx(9.0)
        assert "recovered_dose" in report
        assert "top_match" not in report

    def test_with_spectrum(self) -> None:
        report = vesper_trace_report(
            signal=9.0,
            noise_rms=1.0,
            volume_ml=0.5,
            transfer_fraction=0.1,
            calibration_slope=2.0,
            calibration_intercept=0.5,
            unknown_spectrum=(1.0, 0.2, 0.1, 0.05, 0.02),
        )
        assert report["top_match"] == "ricin"
