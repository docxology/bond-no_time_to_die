"""Tests for antidote_screening.py — competitive-antagonist pharmacology."""

from __future__ import annotations

import pytest

from no_time_to_die.antidote_screening import (
    ANTIDOTE_LIBRARY,
    Antidote,
    AntidoteResult,
    antagonist_at_fraction,
    cheng_prusoff_ic50,
    fraction_antagonized,
    margin_of_safety,
    screen_antidotes,
    screen_report,
    therapeutic_window,
)
from no_time_to_die.toxicology import catalog_by_name


class TestChengPrusoff:
    def test_known(self) -> None:
        # Ki=1, S=1, Km=1 -> 1*(1+1)=2
        assert cheng_prusoff_ic50(1.0, 1.0, 1.0) == pytest.approx(2.0)

    def test_high_substrate_raises_ic50(self) -> None:
        low = cheng_prusoff_ic50(1.0, 0.0, 1.0)
        high = cheng_prusoff_ic50(1.0, 10.0, 1.0)
        assert high > low

    def test_nonpositive_ki_raises(self) -> None:
        with pytest.raises(ValueError):
            cheng_prusoff_ic50(0.0, 1.0, 1.0)

    def test_negative_substrate_raises(self) -> None:
        with pytest.raises(ValueError):
            cheng_prusoff_ic50(1.0, -1.0, 1.0)

    def test_nonpositive_km_raises(self) -> None:
        with pytest.raises(ValueError):
            cheng_prusoff_ic50(1.0, 1.0, 0.0)


class TestFractionAntagonized:
    def test_half_at_ic50(self) -> None:
        assert fraction_antagonized(2.0, 2.0) == pytest.approx(0.5)

    def test_zero_conc_zero(self) -> None:
        assert fraction_antagonized(0.0, 2.0) == 0.0

    def test_saturates(self) -> None:
        assert fraction_antagonized(1000.0, 2.0) > 0.99

    def test_negative_conc_raises(self) -> None:
        with pytest.raises(ValueError):
            fraction_antagonized(-1.0, 2.0)

    def test_nonpositive_ic50_raises(self) -> None:
        with pytest.raises(ValueError):
            fraction_antagonized(1.0, 0.0)


class TestAntagonistAtFraction:
    def test_half_is_ic50(self) -> None:
        assert antagonist_at_fraction(0.5, 2.0) == pytest.approx(2.0)

    def test_fraction_zero_raises(self) -> None:
        with pytest.raises(ValueError):
            antagonist_at_fraction(0.0, 2.0)

    def test_fraction_one_raises(self) -> None:
        with pytest.raises(ValueError):
            antagonist_at_fraction(1.0, 2.0)

    def test_nonpositive_ic50_raises(self) -> None:
        with pytest.raises(ValueError):
            antagonist_at_fraction(0.5, 0.0)


class TestWindows:
    def test_therapeutic_window(self) -> None:
        assert therapeutic_window(100.0, 10.0) == pytest.approx(10.0)

    def test_therapeutic_window_errors(self) -> None:
        with pytest.raises(ValueError):
            therapeutic_window(0.0, 1.0)
        with pytest.raises(ValueError):
            therapeutic_window(1.0, 0.0)

    def test_margin_of_safety(self) -> None:
        assert margin_of_safety(10.0, 5.0) == pytest.approx(1.0)

    def test_margin_negative_when_hazard_precedes_cure(self) -> None:
        assert margin_of_safety(5.0, 10.0) < 0.0


class TestAntidote:
    def test_valid(self) -> None:
        a = Antidote(name="naloxone", ki=0.4, source="opioid antagonist")
        assert a.ki == 0.4

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValueError):
            Antidote(name=" ", ki=1.0, source="s")

    def test_empty_source_raises(self) -> None:
        with pytest.raises(ValueError):
            Antidote(name="n", ki=1.0, source="  ")

    def test_nonpositive_ki_raises(self) -> None:
        with pytest.raises(ValueError):
            Antidote(name="n", ki=0.0, source="s")


class TestScreen:
    def test_library_nonempty(self) -> None:
        assert len(ANTIDOTE_LIBRARY) >= 5
        names = {a.name for a in ANTIDOTE_LIBRARY}
        assert "naloxone" in names

    def test_ranks_lowest_ki_first(self) -> None:
        ricin = catalog_by_name("ricin")
        ranked = screen_antidotes(ricin, dose=0.5, antagonist_conc=10.0)
        assert ranked[0].name == "naloxone"
        assert isinstance(ranked[0], AntidoteResult)
        assert 0.0 <= ranked[0].survival_probability <= 1.0

    def test_survival_increases_with_antagonist(self) -> None:
        ricin = catalog_by_name("ricin")
        low = screen_antidotes(ricin, dose=0.5, antagonist_conc=1.0)
        high = screen_antidotes(ricin, dose=0.5, antagonist_conc=100.0)
        assert high[0].survival_probability > low[0].survival_probability

    def test_negative_dose_raises(self) -> None:
        ricin = catalog_by_name("ricin")
        with pytest.raises(ValueError):
            screen_antidotes(ricin, dose=-1.0, antagonist_conc=10.0)

    def test_negative_conc_raises(self) -> None:
        ricin = catalog_by_name("ricin")
        with pytest.raises(ValueError):
            screen_antidotes(ricin, dose=0.5, antagonist_conc=-1.0)

    def test_empty_library_raises(self) -> None:
        ricin = catalog_by_name("ricin")
        with pytest.raises(ValueError):
            screen_antidotes(ricin, dose=0.5, antagonist_conc=10.0, library=())


class TestScreenReport:
    def test_report_shape(self) -> None:
        ricin = catalog_by_name("ricin")
        report = screen_report(ricin, dose=0.5, antagonist_conc=10.0)
        assert report["antidote_count"] == len(ANTIDOTE_LIBRARY)
        assert report["best_antidote"] == "naloxone"
        survival = report["best_survival_probability"]
        assert isinstance(survival, float)
        assert 0.0 <= survival <= 1.0
        ranked = report["ranked"]
        assert isinstance(ranked, tuple)
