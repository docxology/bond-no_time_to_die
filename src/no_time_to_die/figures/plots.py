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
from no_time_to_die.toxicology import TOXIN_CATALOG, fraction_affected

__all__ = [
    "FIGURES_DIR",
    "plot_antidote_response",
    "plot_delivery_kinetics",
    "plot_detection_confidence",
    "plot_guide_efficiency",
    "plot_toxicology_dose_response",
    "render_all_figures",
]

#: Output directory for rendered figures (package-root ``output/figures``).
FIGURES_DIR = Path(__file__).resolve().parents[3] / "output" / "figures"


def plot_toxicology_dose_response(path: Path | None = None) -> Path:
    """Render Hill dose–response curves for every catalog toxin."""
    doses = np.logspace(-1.0, 2.0, 200)
    out = path or (FIGURES_DIR / "toxicology_dose_response.png")
    out.parent.mkdir(parents=True, exist_ok=True)
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
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def plot_delivery_kinetics(path: Path | None = None) -> Path:
    """Render one-compartment plasma concentration over time."""
    out = path or (FIGURES_DIR / "delivery_kinetics.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    times = np.linspace(0.0, 12.0, 300)
    conc = np.array(
        [
            plasma_concentration(100.0, absorption_rate=1.2, elimination_rate=0.4, time=float(t))
            for t in times
        ]
    )
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(times, conc)
    ax.axvline(2.0, color="grey", linestyle="--", alpha=0.6, label="exposure window")
    ax.set_xlabel("Time (h)")
    ax.set_ylabel("Concentration (arb. units)")
    ax.set_title("HERACLES delivery kinetics (one-compartment bateman model)")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def plot_detection_confidence(path: Path | None = None) -> Path:
    """Render forensic detection confidence vs signal-to-noise ratio."""
    out = path or (FIGURES_DIR / "detection_confidence.png")
    out.parent.mkdir(parents=True, exist_ok=True)
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
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def plot_guide_efficiency(path: Path | None = None) -> Path:
    """Render guide-efficiency vs GC content across the demo candidate guides."""
    from no_time_to_die import demo

    out = path or (FIGURES_DIR / "guide_efficiency.png")
    out.parent.mkdir(parents=True, exist_ok=True)
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
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def plot_antidote_response(path: Path | None = None) -> Path:
    """Render antagonized-fraction dose–response across the antidote library."""
    from no_time_to_die import demo, toxicology

    toxin = toxicology.catalog_by_name("ricin")
    concs = np.logspace(-1.0, 2.0, 200)
    out = path or (FIGURES_DIR / "antidote_response.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for antidote in ANTIDOTE_LIBRARY:
        ic50 = cheng_prusoff_ic50(antidote.ki, substrate_conc=0.5, km=toxin.ld50_mg_kg)
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
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def render_all_figures() -> tuple[Path, ...]:
    """Render every figure and return the written paths in deterministic order."""
    return (
        plot_toxicology_dose_response(),
        plot_delivery_kinetics(),
        plot_guide_efficiency(),
        plot_antidote_response(),
        plot_detection_confidence(),
    )
