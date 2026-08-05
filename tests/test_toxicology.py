"""Tests for toxicology.py — poison-garden dose–response modelling."""

from __future__ import annotations

import pytest

from no_time_to_die.toxicology import (
    TOXIN_CATALOG,
    PlantToxin,
    catalog_by_name,
    catalog_stats,
    combined_fraction_affected,
    dose_for_fraction,
    fraction_affected,
    garden_risk_profile,
    toxin_names,
)


class TestFractionAffected:
    def test_at_ld50_half(self) -> None:
        assert fraction_affected(10.0, 10.0, 2.0) == pytest.approx(0.5)

    def test_zero_dose_zero(self) -> None:
        assert fraction_affected(0.0, 10.0, 2.0) == 0.0

    def test_high_dose_saturates(self) -> None:
        assert fraction_affected(1e6, 10.0, 2.0) > 0.999

    def test_negative_dose_raises(self) -> None:
        with pytest.raises(ValueError):
            fraction_affected(-1.0, 10.0, 2.0)

    def test_nonpositive_ld50_raises(self) -> None:
        with pytest.raises(ValueError):
            fraction_affected(1.0, 0.0, 2.0)

    def test_nonpositive_hill_raises(self) -> None:
        with pytest.raises(ValueError):
            fraction_affected(1.0, 10.0, 0.0)


class TestDoseForFraction:
    def test_half_is_ld50(self) -> None:
        assert dose_for_fraction(0.5, 10.0, 2.0) == pytest.approx(10.0)

    def test_inverse(self) -> None:
        frac = 0.3
        dose = dose_for_fraction(frac, 10.0, 2.0)
        assert fraction_affected(dose, 10.0, 2.0) == pytest.approx(frac)

    def test_fraction_zero_raises(self) -> None:
        with pytest.raises(ValueError):
            dose_for_fraction(0.0, 10.0, 2.0)

    def test_fraction_one_raises(self) -> None:
        with pytest.raises(ValueError):
            dose_for_fraction(1.0, 10.0, 2.0)

    def test_fraction_out_of_range_raises(self) -> None:
        with pytest.raises(ValueError):
            dose_for_fraction(-0.1, 10.0, 2.0)

    def test_invalid_ld50_raises(self) -> None:
        with pytest.raises(ValueError):
            dose_for_fraction(0.5, 0.0, 2.0)

    def test_invalid_hill_raises(self) -> None:
        with pytest.raises(ValueError):
            dose_for_fraction(0.5, 10.0, -1.0)


class TestPlantToxin:
    def test_valid(self) -> None:
        t = PlantToxin(name="ricin", source="castor bean", ld50_mg_kg=1.0, hill_coefficient=2.0)
        assert t.name == "ricin"

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValueError):
            PlantToxin(name=" ", source="x", ld50_mg_kg=1.0, hill_coefficient=2.0)

    def test_empty_source_raises(self) -> None:
        with pytest.raises(ValueError):
            PlantToxin(name="x", source="  ", ld50_mg_kg=1.0, hill_coefficient=2.0)

    def test_nonpositive_ld50_raises(self) -> None:
        with pytest.raises(ValueError):
            PlantToxin(name="x", source="s", ld50_mg_kg=0.0, hill_coefficient=2.0)

    def test_nonpositive_hill_raises(self) -> None:
        with pytest.raises(ValueError):
            PlantToxin(name="x", source="s", ld50_mg_kg=1.0, hill_coefficient=0.0)


class TestCatalog:
    def test_catalog_nonempty(self) -> None:
        assert len(TOXIN_CATALOG) >= 7

    def test_toxin_names(self) -> None:
        names = toxin_names()
        assert "ricin" in names
        assert "cyanide" in names
        assert len(names) == len(TOXIN_CATALOG)

    def test_catalog_by_name_found(self) -> None:
        assert catalog_by_name("ricin").source == "castor bean (Ricinus communis)"

    def test_catalog_by_name_unknown_raises(self) -> None:
        with pytest.raises(ValueError, match="unknown toxin"):
            catalog_by_name("garlic")

    def test_catalog_stats_shapes(self) -> None:
        stats = catalog_stats()
        assert stats["count"] == len(TOXIN_CATALOG)
        assert stats["min_ld50"] <= stats["median_ld50"] <= stats["max_ld50"]

    def test_catalog_stats_odd_median_is_a_catalog_value(self) -> None:
        # The shipped catalog is odd-length (7), so the median is a member value.
        stats = catalog_stats()
        assert len(TOXIN_CATALOG) % 2 == 1
        assert stats["median_ld50"] in [t.ld50_mg_kg for t in TOXIN_CATALOG]

    def test_catalog_stats_even_median_averages_the_middle_pair(self) -> None:
        # Real two-toxin catalog: ricin 1.0, atropine 10.0 -> median 5.5.
        pair = (catalog_by_name("ricin"), catalog_by_name("atropine"))
        stats = catalog_stats(pair)
        assert stats["count"] == 2.0
        assert stats["min_ld50"] == 1.0
        assert stats["max_ld50"] == 10.0
        assert stats["median_ld50"] == pytest.approx(5.5)

    def test_catalog_stats_even_median_four_toxins(self) -> None:
        # Sorted LD50s 0.8, 1.0, 1.5, 10.0 -> median (1.0 + 1.5) / 2 = 1.25.
        quad = tuple(
            catalog_by_name(name) for name in ("ricin", "nicotine", "aconitine", "atropine")
        )
        stats = catalog_stats(quad)
        assert stats["median_ld50"] == pytest.approx(1.25)

    def test_catalog_stats_empty_catalog_raises(self) -> None:
        with pytest.raises(ValueError, match="catalog must not be empty"):
            catalog_stats(())


class TestCombined:
    def test_single_agent(self) -> None:
        ricin = catalog_by_name("ricin")
        f = combined_fraction_affected(((ricin, 1.0),))  # dose == LD50 -> 0.5
        assert f == pytest.approx(0.5)

    def test_independent_agents_combine(self) -> None:
        ricin = catalog_by_name("ricin")
        coniine = catalog_by_name("coniine")
        # Each alone at LD50 -> 0.5; combined -> 1 - 0.25 = 0.75
        f = combined_fraction_affected(((ricin, 1.0), (coniine, 6.0)))
        assert f == pytest.approx(0.75)

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError):
            combined_fraction_affected(())


class TestGardenRiskProfile:
    def test_profile(self) -> None:
        report = garden_risk_profile({"ricin": 0.5, "nicotine": 0.4})
        assert "per_agent_fraction" in report
        assert "combined_fraction" in report
        assert isinstance(report["per_agent_fraction"], dict)
        assert isinstance(report["combined_fraction"], float)

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError):
            garden_risk_profile({})

    def test_unknown_toxin_raises(self) -> None:
        with pytest.raises(ValueError):
            garden_risk_profile({"not_a_poison": 1.0})
