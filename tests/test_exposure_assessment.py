"""Tests for exposure_assessment.py — exposure pathway & risk assessment."""

from __future__ import annotations

import math

import pytest

from no_time_to_die import demo
from no_time_to_die.exposure_assessment import (
    absorbed_dose,
    cumulative_exposure,
    exposure_scenario_report,
    margin_of_exposure,
    risk_quotient,
)


class TestAbsorbedDose:
    def test_known(self) -> None:
        assert absorbed_dose(0.02, 0.5, 30.0, 0.2) == pytest.approx(0.06)

    def test_zero_contact_zero(self) -> None:
        assert absorbed_dose(1.0, 0.0, 10.0, 0.5) == 0.0

    def test_negative_concentration_raises(self) -> None:
        with pytest.raises(ValueError):
            absorbed_dose(-1.0, 0.5, 30.0, 0.2)

    def test_negative_rate_raises(self) -> None:
        with pytest.raises(ValueError):
            absorbed_dose(0.02, -0.5, 30.0, 0.2)

    def test_negative_duration_raises(self) -> None:
        with pytest.raises(ValueError):
            absorbed_dose(0.02, 0.5, -1.0, 0.2)

    def test_frac_out_of_range_raises(self) -> None:
        with pytest.raises(ValueError):
            absorbed_dose(0.02, 0.5, 30.0, 1.5)
        with pytest.raises(ValueError):
            absorbed_dose(0.02, 0.5, 30.0, -0.1)


class TestCumulativeExposure:
    def test_known(self) -> None:
        got = cumulative_exposure(0.002, 0.1, 30.0)
        assert got == pytest.approx((0.002 / 0.1) * (1 - math.exp(-3.0)))

    def test_approaches_steady_state(self) -> None:
        assert cumulative_exposure(0.002, 0.1, 1e6) == pytest.approx(0.02)

    def test_zero_duration_zero(self) -> None:
        assert cumulative_exposure(0.002, 0.1, 0.0) == 0.0

    def test_negative_rate_raises(self) -> None:
        with pytest.raises(ValueError):
            cumulative_exposure(-1.0, 0.1, 30.0)

    def test_nonpositive_elimination_raises(self) -> None:
        with pytest.raises(ValueError):
            cumulative_exposure(0.002, 0.0, 30.0)

    def test_negative_duration_raises(self) -> None:
        with pytest.raises(ValueError):
            cumulative_exposure(0.002, 0.1, -1.0)


class TestMarginOfExposure:
    def test_known(self) -> None:
        assert margin_of_exposure(0.06, 0.5) == pytest.approx(8.333333333333334)

    def test_zero_dose_infinite(self) -> None:
        assert margin_of_exposure(0.0, 0.5) == float("inf")

    def test_negative_absorbed_raises(self) -> None:
        with pytest.raises(ValueError):
            margin_of_exposure(-1.0, 0.5)

    def test_nonpositive_noael_raises(self) -> None:
        with pytest.raises(ValueError):
            margin_of_exposure(0.1, 0.0)


class TestRiskQuotient:
    def test_known(self) -> None:
        assert risk_quotient(0.06, 0.001) == pytest.approx(60.0)

    def test_zero_dose_zero(self) -> None:
        assert risk_quotient(0.0, 0.001) == 0.0

    def test_negative_absorbed_raises(self) -> None:
        with pytest.raises(ValueError):
            risk_quotient(-1.0, 0.001)

    def test_nonpositive_reference_raises(self) -> None:
        with pytest.raises(ValueError):
            risk_quotient(0.1, 0.0)


class TestExposureScenarioReport:
    def test_demo_scenario_elevated(self) -> None:
        report = exposure_scenario_report(**demo.EXPOSURE_SCENARIO)
        assert report["absorbed_dose"] == pytest.approx(0.06)
        assert report["risk_quotient"] == pytest.approx(60.0)
        assert report["verdict"] == "elevated risk"

    def test_low_dose_acceptable(self) -> None:
        report = exposure_scenario_report(
            concentration=0.0001,
            contact_rate=0.1,
            duration=1.0,
            absorption_fraction=0.1,
            elimination_rate=0.2,
            noael=0.5,
            reference_dose=0.001,
        )
        assert report["verdict"] == "acceptable"
        moe = report["margin_of_exposure"]
        assert isinstance(moe, float)
        assert moe >= 1.0

    def test_invalid_param_propagates(self) -> None:
        with pytest.raises(ValueError):
            exposure_scenario_report(
                concentration=0.02,
                contact_rate=0.5,
                duration=30.0,
                absorption_fraction=2.0,  # out of range
                elimination_rate=0.1,
                noael=0.5,
                reference_dose=0.001,
            )
