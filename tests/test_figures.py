"""Tests for figures/plots.py — bind what is drawn to the demo constants.

Five of the seven tests in this file previously asserted only
``out.exists() and out.stat().st_size > 0``. A blank PNG passes that. A PNG of
the wrong curve passes that. A figure whose exposure-window marker disagreed
with ``DEMO_EXPOSURE_TIME`` — the exact bug ``demo.DELIVERY_PLOT_*`` was
introduced to prevent — passes that too. So
``manuscript/06_reproducibility.md``'s claim that "a plotted curve and its
caption cannot disagree about a parameter" rested on nothing.

Each ``plot_*`` now delegates to a ``build_*_figure()`` that returns the
composed Figure, and the tests read the artists back out: the plotted series,
the annotation positions, the axis labels, the legend entries. Those are
compared against the constants the manuscript captions quote.
``TestFigureBindingCanFail`` shows the readback distinguishes a correct figure
from a wrong one, so the assertions are not passing on shape alone.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.figure import Figure

from no_time_to_die import demo
from no_time_to_die.antidote_screening import ANTIDOTE_LIBRARY
from no_time_to_die.bioweapon_counter import plasma_concentration
from no_time_to_die.delivery_forensics import DEFAULT_LOD_SNR, detection_confidence
from no_time_to_die.figures import plots
from no_time_to_die.targeting_design import guide_efficiency
from no_time_to_die.toxicology import TOXIN_CATALOG


def _axes(figure: Figure):
    assert len(figure.axes) == 1
    return figure.axes[0]


def _vertical_markers(axis) -> list[float]:
    """x positions of the dashed/dotted vertical annotation lines."""
    positions = []
    for line in axis.lines:
        xdata = np.asarray(line.get_xdata(), dtype=float)
        ydata = np.asarray(line.get_ydata(), dtype=float)
        if len(xdata) == 2 and xdata[0] == xdata[1] and len(ydata) == 2:
            positions.append(float(xdata[0]))
    return positions


def _series(axis) -> list[tuple[np.ndarray, np.ndarray]]:
    """Plotted (x, y) series, excluding the two-point annotation lines."""
    out = []
    for line in axis.lines:
        xdata = np.asarray(line.get_xdata(), dtype=float)
        if len(xdata) > 2:
            out.append((xdata, np.asarray(line.get_ydata(), dtype=float)))
    return out


class TestDeliveryKineticsBinding:
    """The figure the manuscript captions with a horizon, two rates, and a window."""

    def test_curve_spans_the_demo_horizon_and_matches_the_model(self) -> None:
        figure = plots.build_delivery_kinetics_figure()
        try:
            axis = _axes(figure)
            ((times, conc),) = _series(axis)
            assert times[0] == 0.0
            assert times[-1] == pytest.approx(demo.DELIVERY_PLOT_HORIZON_H)
            # Every plotted point must be the model's own value at that time.
            for t, c in zip(times[::37], conc[::37]):
                assert c == pytest.approx(
                    plasma_concentration(
                        demo.DELIVERY_PLOT_DOSE,
                        absorption_rate=demo.DEMO_ABSORPTION_RATE,
                        elimination_rate=demo.DELIVERY_PLOT_ELIMINATION_RATE,
                        time=float(t),
                    )
                )
        finally:
            plt.close(figure)

    def test_exposure_window_marker_sits_on_the_demo_constant(self) -> None:
        figure = plots.build_delivery_kinetics_figure()
        try:
            axis = _axes(figure)
            assert _vertical_markers(axis) == [pytest.approx(demo.DEMO_EXPOSURE_TIME)]
            labels = [text.get_text() for text in axis.get_legend().get_texts()]
            assert f"exposure window ({demo.DEMO_EXPOSURE_TIME} h)" in labels
        finally:
            plt.close(figure)

    def test_a_wrong_rate_would_change_the_curve(self) -> None:
        """Negative control: the readback is sensitive to the parameter."""
        figure = plots.build_delivery_kinetics_figure()
        try:
            ((times, conc),) = _series(_axes(figure))
            wrong = np.array(
                [
                    plasma_concentration(
                        demo.DELIVERY_PLOT_DOSE,
                        absorption_rate=demo.DEMO_ABSORPTION_RATE,
                        elimination_rate=demo.DELIVERY_PLOT_ELIMINATION_RATE * 2.0,
                        time=float(t),
                    )
                    for t in times
                ]
            )
            assert not np.allclose(conc, wrong)
        finally:
            plt.close(figure)


class TestDetectionConfidenceBinding:
    def test_lod_marker_and_curve_match_the_module_constant(self) -> None:
        figure = plots.build_detection_confidence_figure()
        try:
            axis = _axes(figure)
            ((snrs, conf),) = _series(axis)
            assert _vertical_markers(axis) == [pytest.approx(DEFAULT_LOD_SNR)]
            for snr, value in zip(snrs[::41], conf[::41]):
                assert value == pytest.approx(detection_confidence(float(snr), DEFAULT_LOD_SNR))
            # The curve must cross 0.5 exactly at the LOD, which is the claim.
            assert detection_confidence(DEFAULT_LOD_SNR, DEFAULT_LOD_SNR) == pytest.approx(0.5)
        finally:
            plt.close(figure)


class TestToxicologyBinding:
    def test_one_curve_per_catalog_toxin_labelled_with_its_ld50(self) -> None:
        figure = plots.build_toxicology_dose_response_figure()
        try:
            axis = _axes(figure)
            assert len(_series(axis)) == len(TOXIN_CATALOG)
            labels = {text.get_text() for text in axis.get_legend().get_texts()}
            assert labels == {
                f"{toxin.name} (LD50 {toxin.ld50_mg_kg:g})" for toxin in TOXIN_CATALOG
            }
        finally:
            plt.close(figure)


class TestAntidoteBinding:
    def test_demo_dose_marker_and_one_curve_per_library_entry(self) -> None:
        figure = plots.build_antidote_response_figure()
        try:
            axis = _axes(figure)
            assert len(_series(axis)) == len(ANTIDOTE_LIBRARY)
            assert _vertical_markers(axis) == [pytest.approx(demo.ANTAGONIST_CONC)]
            labels = {text.get_text() for text in axis.get_legend().get_texts()}
            assert {f"{a.name} (Ki {a.ki:g})" for a in ANTIDOTE_LIBRARY} <= labels
        finally:
            plt.close(figure)


class TestGuideEfficiencyBinding:
    def test_one_bar_per_candidate_at_its_computed_efficiency(self) -> None:
        figure = plots.build_guide_efficiency_figure()
        try:
            axis = _axes(figure)
            heights = [patch.get_height() for patch in axis.patches]
            assert heights == [
                pytest.approx(guide_efficiency(guide)) for guide in demo.DEMO_CANDIDATES
            ]
            annotations = "\n".join(text.get_text() for text in axis.texts)
            for guide in demo.DEMO_CANDIDATES:
                assert guide in annotations
        finally:
            plt.close(figure)


class TestFigureBindingCanFail:
    """The readback helpers must distinguish right from wrong, not just parse."""

    def test_marker_readback_reports_a_wrong_annotation(self) -> None:
        figure, axis = plt.subplots()
        try:
            axis.plot(np.linspace(0, 10, 50), np.linspace(0, 1, 50))
            axis.axvline(2.0)  # the historic wrong exposure window
            assert _vertical_markers(axis) == [2.0]
            assert _vertical_markers(axis) != [demo.DEMO_EXPOSURE_TIME]
        finally:
            plt.close(figure)

    def test_series_readback_reports_a_blank_figure(self) -> None:
        figure, axis = plt.subplots()
        try:
            assert _series(axis) == []
        finally:
            plt.close(figure)


class TestWrittenFiles:
    def test_every_plot_function_writes_a_non_empty_file(self, tmp_path) -> None:
        for index, plot in enumerate(plots.PLOT_FUNCTIONS):
            out = plot(tmp_path / f"{index}.png")
            assert out.exists() and out.stat().st_size > 0

    def test_render_all_figures_covers_every_plot_function(self, tmp_path) -> None:
        original = plots.FIGURES_DIR
        target = tmp_path / "figures"
        try:
            plots.FIGURES_DIR = target
            written = plots.render_all_figures()
        finally:
            plots.FIGURES_DIR = original
        assert plots.FIGURES_DIR == original
        assert len(written) == len(plots.PLOT_FUNCTIONS)
        assert {path.parent for path in written} == {target}
        assert len({path.name for path in written}) == len(written)
        for path in written:
            assert path.exists() and path.stat().st_size > 0

    def test_plot_functions_tuple_lists_every_public_plot_entry_point(self) -> None:
        """A new figure cannot be added and silently left out of the batch."""
        exported = {name for name in plots.__all__ if name.startswith("plot_")}
        assert {plot.__name__ for plot in plots.PLOT_FUNCTIONS} == exported

    def test_every_builder_has_a_matching_plot_function(self) -> None:
        builders = {name for name in plots.__all__ if name.startswith("build_")}
        expected = {
            plot.__name__.replace("plot_", "build_") + "_figure" for plot in plots.PLOT_FUNCTIONS
        }
        assert builders == expected

    def test_figures_dir_points_at_the_package_output_tree(self) -> None:
        assert plots.FIGURES_DIR.is_absolute()
        assert plots.FIGURES_DIR.name == "figures"
        assert plots.FIGURES_DIR.parent.name == "output"
        assert (plots.FIGURES_DIR.parents[1] / "pyproject.toml").is_file()
