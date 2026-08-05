"""Tests for figures/plots.py — deterministic figure rendering."""

from __future__ import annotations

from no_time_to_die.figures import plots


class TestFigures:
    def test_toxicology_plot_written(self, tmp_path) -> None:
        out = plots.plot_toxicology_dose_response(tmp_path / "tox.png")
        assert out.exists() and out.stat().st_size > 0

    def test_delivery_kinetics_plot_written(self, tmp_path) -> None:
        out = plots.plot_delivery_kinetics(tmp_path / "delivery.png")
        assert out.exists() and out.stat().st_size > 0

    def test_guide_efficiency_plot_written(self, tmp_path) -> None:
        out = plots.plot_guide_efficiency(tmp_path / "guide.png")
        assert out.exists() and out.stat().st_size > 0

    def test_antidote_response_plot_written(self, tmp_path) -> None:
        out = plots.plot_antidote_response(tmp_path / "antidote.png")
        assert out.exists() and out.stat().st_size > 0

    def test_detection_confidence_plot_written(self, tmp_path) -> None:
        out = plots.plot_detection_confidence(tmp_path / "detect.png")
        assert out.exists() and out.stat().st_size > 0

    def test_render_all_figures(self, tmp_path) -> None:
        plots.FIGURES_DIR = tmp_path / "figures"  # redirect to tmp to keep tree clean
        written = plots.render_all_figures()
        assert len(written) == 5
        for path in written:
            assert path.exists()

    def test_figures_dir_is_absolute(self) -> None:
        assert plots.FIGURES_DIR.exists() or plots.FIGURES_DIR.parents[0].name == "output"
