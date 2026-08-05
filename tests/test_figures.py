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
        # Redirect to tmp to keep the tree clean, then restore: leaving the
        # module global pointing at a torn-down tmp_path would silently corrupt
        # any later test that reads FIGURES_DIR.
        original = plots.FIGURES_DIR
        target = tmp_path / "figures"
        try:
            plots.FIGURES_DIR = target
            written = plots.render_all_figures()
        finally:
            plots.FIGURES_DIR = original
        assert plots.FIGURES_DIR == original
        assert len(written) == len(plots.__all__) - 2  # all plot_* minus FIGURES_DIR/render_all
        assert {path.parent for path in written} == {target}
        assert len({path.name for path in written}) == len(written)
        for path in written:
            assert path.exists() and path.stat().st_size > 0

    def test_figures_dir_points_at_the_package_output_tree(self) -> None:
        # Assert the real invariant: an absolute path at <package>/output/figures.
        assert plots.FIGURES_DIR.is_absolute()
        assert plots.FIGURES_DIR.name == "figures"
        assert plots.FIGURES_DIR.parent.name == "output"
        assert (plots.FIGURES_DIR.parents[1] / "pyproject.toml").is_file()
