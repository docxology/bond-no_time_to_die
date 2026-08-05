"""Figure generation for the HERACLES mission (No Time to Die, 2021).

Renders deterministic, publication-style plots across the domain concepts:

* :func:`plot_toxicology_dose_response` — Hill dose–response curves across the
  poison-garden flora catalog.
* :func:`plot_delivery_kinetics` — one-compartment plasma concentration over
  time for the bioweapon delivery model.
* :func:`plot_guide_efficiency` — guide-efficiency landscape across the design
  candidates vs GC content.
* :func:`plot_antidote_response` — antagonized-fraction dose–response of the
  competitive-antagonist library.
* :func:`plot_detection_confidence` — forensic detection confidence vs
  signal-to-noise ratio against the limit of detection.

Each ``plot_*`` function is a thin wrapper over a matching ``build_*_figure``
that composes the :class:`~matplotlib.figure.Figure` without touching the
filesystem. That split exists so the tests can assert on what is actually
*drawn* — the plotted series, the axis labels, the annotation positions — and
bind them to the ``demo.py`` constants the manuscript captions quote. Asserting
only that a PNG is non-empty passes just as happily on a blank or wrong-data
figure, which is not the gate the reproducibility section claims.

All figures are pure matplotlib renders over fixed, deterministic data; they
only touch the output directory, write nothing random, and are safe under a
headless (``MPLBACKEND=Agg``) backend.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless-safe; figures never open a window

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from no_time_to_die import demo
from no_time_to_die.antidote_screening import (
    ANTIDOTE_LIBRARY,
    cheng_prusoff_ic50,
    fraction_antagonized,
)
from no_time_to_die.bioweapon_counter import plasma_concentration
from no_time_to_die.delivery_forensics import (
    DEFAULT_LOD_SNR,
    detection_confidence,
)
from no_time_to_die.targeting_design import gc_content, guide_efficiency
from no_time_to_die.toxicology import TOXIN_CATALOG, catalog_by_name, fraction_affected

__all__ = [
    "FIGURES_DIR",
    "FIGURE_DPI",
    "PLOT_FUNCTIONS",
    "build_antidote_response_figure",
    "build_delivery_kinetics_figure",
    "build_detection_confidence_figure",
    "build_guide_efficiency_figure",
    "build_toxicology_dose_response_figure",
    "plot_antidote_response",
    "plot_delivery_kinetics",
    "plot_detection_confidence",
    "plot_guide_efficiency",
    "plot_toxicology_dose_response",
    "render_all_figures",
]

#: Output directory for rendered figures (package-root ``output/figures``).
FIGURES_DIR = Path(__file__).resolve().parents[3] / "output" / "figures"

#: Dots per inch every figure is written at (single source of truth).
FIGURE_DPI = 150


def _save(figure: Figure, path: Path | None, default_name: str) -> Path:
    """Write ``figure`` to ``path`` (or the default under :data:`FIGURES_DIR`)."""
    out = path or (FIGURES_DIR / default_name)
    out.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(out, dpi=FIGURE_DPI)
    plt.close(figure)
    return out


def build_toxicology_dose_response_figure() -> Figure:
    """Compose Hill dose–response curves for every catalog toxin."""
    doses = np.logspace(-1.0, 2.0, 200)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for toxin in TOXIN_CATALOG:
        curve = np.array(
            [fraction_affected(float(d), toxin.ld50_mg_kg, toxin.hill_coefficient) for d in doses]
        )
        ax.plot(doses, curve, label=f"{toxin.name} (LD50 {toxin.ld50_mg_kg:g})")
    ax.set_xscale("log")
    ax.set_xlabel("Dose (mg/kg)")
    ax.set_ylabel("Fraction affected")
    ax.set_title("Poison-garden dose–response (Hill model)")
    ax.legend(fontsize=7, loc="upper left")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig


def plot_toxicology_dose_response(path: Path | None = None) -> Path:
    """Render Hill dose–response curves for every catalog toxin."""
    return _save(build_toxicology_dose_response_figure(), path, "toxicology_dose_response.png")


def build_delivery_kinetics_figure() -> Figure:
    """Compose the one-compartment plasma-concentration curve over time.

    Every parameter is read from ``demo.py``: the horizon, the dose, the
    absorption and elimination rates, and the exposure-window marker.
    """
    times = np.linspace(0.0, demo.DELIVERY_PLOT_HORIZON_H, 300)
    conc = np.array(
        [
            plasma_concentration(
                demo.DELIVERY_PLOT_DOSE,
                absorption_rate=demo.DEMO_ABSORPTION_RATE,
                elimination_rate=demo.DELIVERY_PLOT_ELIMINATION_RATE,
                time=float(t),
            )
            for t in times
        ]
    )
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(times, conc)
    ax.axvline(
        demo.DEMO_EXPOSURE_TIME,
        color="grey",
        linestyle="--",
        alpha=0.6,
        label=f"exposure window ({demo.DEMO_EXPOSURE_TIME} h)",
    )
    ax.set_xlabel("Time (h)")
    ax.set_ylabel("Concentration (arb. units)")
    ax.set_title("HERACLES delivery kinetics (one-compartment bateman model)")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig


def plot_delivery_kinetics(path: Path | None = None) -> Path:
    """Render one-compartment plasma concentration over time."""
    return _save(build_delivery_kinetics_figure(), path, "delivery_kinetics.png")


def build_detection_confidence_figure() -> Figure:
    """Compose forensic detection confidence vs signal-to-noise ratio."""
    snrs = np.linspace(0.0, 10.0, 300)
    conf = np.array([detection_confidence(float(s), DEFAULT_LOD_SNR) for s in snrs])
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(snrs, conf)
    ax.axvline(DEFAULT_LOD_SNR, color="red", linestyle="--", alpha=0.7, label="LOD SNR")
    ax.axhline(0.5, color="grey", linestyle=":", alpha=0.6)
    ax.set_xlabel("Signal-to-noise ratio")
    ax.set_ylabel("Detection confidence")
    ax.set_title("Vesper trace detection confidence")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig


def plot_detection_confidence(path: Path | None = None) -> Path:
    """Render forensic detection confidence vs signal-to-noise ratio."""
    return _save(build_detection_confidence_figure(), path, "detection_confidence.png")


def build_guide_efficiency_figure() -> Figure:
    """Compose guide-efficiency bars across the demo candidate guides."""
    guides = demo.DEMO_CANDIDATES
    efficiencies = [guide_efficiency(g) for g in guides]
    gcs = [gc_content(g) for g in guides]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(range(len(guides)), efficiencies, color="steelblue")
    for i, (value, gc, guide) in enumerate(zip(efficiencies, gcs, guides)):
        ax.text(
            i, float(value) + 0.02, f"GC {gc:.2f}\n{guide}", ha="center", va="bottom", fontsize=6
        )
    ax.set_xticks(range(len(guides)))
    ax.set_xticklabels([f"g{i}" for i in range(len(guides))])
    ax.set_xlabel("Guide candidate")
    ax.set_ylabel("Guide efficiency")
    ax.set_ylim(0.0, 1.15)
    ax.set_title("HERACLES guide-design efficiency (Doench-style score)")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig


def plot_guide_efficiency(path: Path | None = None) -> Path:
    """Render guide-efficiency vs GC content across the demo candidate guides."""
    return _save(build_guide_efficiency_figure(), path, "guide_efficiency.png")


def build_antidote_response_figure() -> Figure:
    """Compose the antagonized-fraction dose–response across the antidote library.

    The substrate concentration is ``demo.ANTIDOTE_SCREEN_DOSE`` — the same
    dose the screen in :func:`no_time_to_die.demo.run_demo` uses — so the curve
    and the reported screen cannot describe different experiments.
    """
    toxin = catalog_by_name("ricin")
    concs = np.logspace(-1.0, 2.0, 200)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for antidote in ANTIDOTE_LIBRARY:
        ic50 = cheng_prusoff_ic50(
            antidote.ki,
            substrate_conc=demo.ANTIDOTE_SCREEN_DOSE,
            km=toxin.ld50_mg_kg,
        )
        curve = np.array([fraction_antagonized(float(c), ic50) for c in concs])
        ax.plot(concs, curve, label=f"{antidote.name} (Ki {antidote.ki:g})")
    ax.axvline(demo.ANTAGONIST_CONC, color="red", linestyle="--", alpha=0.7, label="demo dose")
    ax.set_xscale("log")
    ax.set_xlabel("Antagonist concentration (mg/L)")
    ax.set_ylabel("Fraction antagonized")
    ax.set_title("Competitive-antagonist antidote response (Cheng–Prusoff)")
    ax.legend(fontsize=7)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig


def plot_antidote_response(path: Path | None = None) -> Path:
    """Render antagonized-fraction dose–response across the antidote library."""
    return _save(build_antidote_response_figure(), path, "antidote_response.png")


#: Every ``plot_*`` entry point, in render order. :func:`render_all_figures`
#: iterates this rather than repeating the call list, so a new figure cannot be
#: added to the module and silently skipped by the batch renderer.
PLOT_FUNCTIONS = (
    plot_toxicology_dose_response,
    plot_delivery_kinetics,
    plot_guide_efficiency,
    plot_antidote_response,
    plot_detection_confidence,
)


def render_all_figures() -> tuple[Path, ...]:
    """Render every figure and return the written paths in deterministic order."""
    return tuple(plot(None) for plot in PLOT_FUNCTIONS)
