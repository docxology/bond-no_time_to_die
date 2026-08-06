"""Manuscript variable hydration for the HERACLES film.

Every ``{{TOKEN}}`` in ``manuscript/[0-9]*.md`` resolves through
:func:`generate_variables`, which reads ``manuscript/config.yaml`` plus the
deterministic domain/demo results. Metrics are never hand-authored in prose:
they flow through this module (and the shared :mod:`no_time_to_die.demo`
result) so the manuscript cannot drift from the code.

:func:`resolve_manuscript_tree` writes substituted section copies to
``output/manuscript/`` and, in strict mode, fails on any leftover token.
"""

from __future__ import annotations

import platform
import re
from pathlib import Path
from typing import Any

import yaml

from no_time_to_die import (
    antidote_screening,
    delivery_forensics,
    demo,
    toxicology,
)

__all__ = [
    "REQUIRED_DEMO_KEYS",
    "REQUIRED_TOP_LEVEL_KEYS",
    "check_demo_completeness",
    "generate_variables",
    "load_manuscript_config",
    "resolve_manuscript_tree",
]

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PACKAGE_ROOT / "manuscript" / "config.yaml"

_TOKEN_RE = re.compile(r"\{\{[A-Z0-9_]+\}\}")


def load_manuscript_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load and validate ``manuscript/config.yaml`` (or an explicit path)."""
    path = Path(config_path) if config_path is not None else DEFAULT_CONFIG_PATH
    if not path.is_file():
        raise FileNotFoundError(f"manuscript config not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(  # noqa: TRY004 — ValueError validation is the package convention
            f"manuscript config must be a top-level mapping, got {type(data).__name__}"
        )
    return data


def _fmt(value: float, digits: int = 4) -> str:
    """Format a computed float compactly for prose (deterministic).

    Integral counts are stringified directly at their call sites; everything
    routed through here is a computed float, so ``%g`` is the only formatting
    branch (it renders an integral float as ``3`` rather than ``3.0`` anyway).
    """
    return f"{value:.{digits}g}"


def _mix_primary(mixture: object) -> str:
    """Primary component name from a ``forensics['mixture']`` dict (or ``n/a``)."""
    if isinstance(mixture, dict):
        return str(mixture.get("primary") or "n/a")
    return "n/a"


def _mix_secondary(mixture: object) -> str:
    """Secondary component name; ``none`` for a pure single-poison fit."""
    if isinstance(mixture, dict):
        secondary = mixture.get("secondary")
        return "none" if secondary is None else str(secondary)
    return "n/a"


def _mix_weight(mixture: object, key: str) -> str:
    """A component mixing weight as a percentage, guarded against a missing
    result or a non-numeric value."""
    if isinstance(mixture, dict):
        value = mixture.get(key)
        if isinstance(value, (int, float)):
            return _fmt(value * 100.0)
    return "0"


def _mix_residual(mixture: object) -> str:
    """The fit's squared residual, guarded like :func:`_mix_weight`."""
    if isinstance(mixture, dict):
        value = mixture.get("residual")
        if isinstance(value, (int, float)):
            return _fmt(value)
    return "0"


#: Demo-result keys every numeric token depends on, grouped by result section.
#: :func:`check_demo_completeness` enforces this list, so a domain refactor that
#: renames or drops a result key fails loudly instead of silently hydrating the
#: manuscript with the ``0.0`` fallbacks in :func:`generate_variables`.
REQUIRED_DEMO_KEYS: dict[str, tuple[str, ...]] = {
    "countermeasure": (
        "best_guide",
        "on_target",
        "off_target",
        "specificity",
        "delivered_fraction",
        "neutralization_probability",
    ),
    "targeting": ("best_guide", "best_efficiency", "best_off_target_risk", "best_composite"),
    "toxicology_stats": ("min_ld50", "max_ld50", "median_ld50"),
    "antidote": (
        "best_antidote",
        "best_antagonized_fraction",
        "best_survival_probability",
        "challenge_therapeutic_window",
        "challenge_margin_of_safety",
    ),
    "exposure": (
        "absorbed_dose",
        "cumulative_exposure",
        "margin_of_exposure",
        "risk_quotient",
        "verdict",
    ),
    "forensics": (
        "snr",
        "detection_confidence",
        "concentration",
        "recovered_dose",
        "top_match",
        "mixture",
    ),
}


#: Demo-result keys that live at the *top* level of the result rather than
#: inside a section dict. ``garden_risk_combined`` is a bare float, so the
#: section-keyed scan below is structurally blind to it: deleting it used to
#: sail through this gate and then blow up as a raw ``KeyError`` inside
#: :func:`generate_variables`, which is exactly the failure mode the gate
#: advertises catching.
REQUIRED_TOP_LEVEL_KEYS: tuple[str, ...] = ("garden_risk_combined",)


def check_demo_completeness(results: demo.DemoResult) -> None:
    """Assert a demo result carries every key the manuscript tokens read.

    Covers three structural regressions: a missing top-level key, a missing or
    non-mapping section (reported as ``section.*``), and a missing key inside a
    section.

    Args:
        results: A :func:`no_time_to_die.demo.run_demo` result to validate.

    Raises:
        ValueError: naming every missing key path. This is the strict gate
            behind ``require_outputs``: it fails on a real structural
            regression, not merely on an empty dict.
    """
    raw: dict[str, Any] = dict(results)
    missing = [key for key in REQUIRED_TOP_LEVEL_KEYS if key not in raw]
    for section, keys in REQUIRED_DEMO_KEYS.items():
        bucket = raw.get(section)
        if not isinstance(bucket, dict):
            missing.append(f"{section}.*")
            continue
        missing.extend(f"{section}.{key}" for key in keys if key not in bucket)
    if missing:
        raise ValueError(
            "demo result is missing manuscript-critical keys: " + ", ".join(sorted(missing))
        )


def generate_variables(
    *,
    config_path: str | Path | None = None,
    require_outputs: bool = True,
    results: demo.DemoResult | None = None,
) -> dict[str, str]:
    """Compute the ``{{TOKEN}}`` → value mapping for the manuscript.

    Args:
        config_path: Override for ``manuscript/config.yaml``.
        require_outputs: When True (default), run :func:`check_demo_completeness`
            over the demo result — the strict gate that keeps metrics live
            rather than silently falling back to zeros.
        results: Override for the demo result, so the completeness gate can be
            exercised against a real but deliberately incomplete result.

    Raises:
        ValueError: if the config is malformed or, under ``require_outputs``,
            the demo result is missing a manuscript-critical key.
    """
    config = load_manuscript_config(config_path)
    paper = config.get("paper", {})
    if not isinstance(paper, dict):
        raise ValueError(  # noqa: TRY004 — ValueError validation is the package convention
            "manuscript config 'paper' section must be a mapping"
        )
    authors = config.get("authors", [])
    author_name = authors[0].get("name", "") if isinstance(authors, list) and authors else ""

    results = demo.run_demo() if results is None else results
    if require_outputs:
        check_demo_completeness(results)
    raw: dict[str, Any] = dict(results)
    cm = results["countermeasure"]

    tox_stats = results["toxicology_stats"]
    targeting = results["targeting"]
    antidote = results["antidote"]
    exposure = results["exposure"]
    forensics = results["forensics"]

    def get_num(mapping: dict[str, Any], key: str, default: float = 0.0) -> float:
        val = mapping.get(key)
        return float(val) if isinstance(val, (int, float)) else default

    # The specificity selector and the design ranking are different models and
    # may legitimately disagree. Each prose section cites its own token; the
    # cross-reference test fails if a section quotes the other one's answer.
    cm_best_guide = str(cm.get("best_guide") or "n/a")
    design_best_guide = str(targeting.get("best_guide") or "n/a")
    best_guide = design_best_guide if design_best_guide != "n/a" else cm_best_guide
    planted = demo.planted_segment_counts()
    exposure_params = demo.EXPOSURE_SCENARIO
    forensic_params = demo.FORENSIC_SCENARIO
    return {
        "HERACLES_TITLE": str(paper.get("title", "")),
        "HERACLES_SUBTITLE": str(paper.get("subtitle", "")),
        "HERACLES_VERSION": str(paper.get("version", "")),
        "HERACLES_CODENAME": str(config.get("film", {}).get("codename", "HERACLES")),
        "HERACLES_AUTHOR": author_name,
        "HERACLES_NUM_MODULES": str(len(demo.DOMAIN_MODULES)),
        "HERACLES_NUM_TOXINS": str(len(toxicology.TOXIN_CATALOG)),
        "HERACLES_NUM_LIBRARY": str(len(delivery_forensics.SPECTRUM_LIBRARY)),
        "HERACLES_MIN_LD50": str(tox_stats.get("min_ld50", 0.0)),
        "HERACLES_MAX_LD50": str(tox_stats.get("max_ld50", 0.0)),
        "HERACLES_MEDIAN_LD50": str(tox_stats.get("median_ld50", 0.0)),
        "HERACLES_GARDEN_RISK_PCT": _fmt(get_num(raw, "garden_risk_combined") * 100.0),
        "HERACLES_SPECIFICITY": _fmt(get_num(cm, "specificity") * 100.0),
        "HERACLES_ON_TARGET": _fmt(get_num(cm, "on_target")),
        "HERACLES_OFF_TARGET": _fmt(get_num(cm, "off_target")),
        "HERACLES_DELIVERED_PCT": _fmt(get_num(cm, "delivered_fraction") * 100.0),
        "HERACLES_BEST_GUIDE": best_guide,
        "HERACLES_CM_BEST_GUIDE": cm_best_guide,
        "HERACLES_DESIGN_BEST_GUIDE": design_best_guide,
        "HERACLES_NUM_GUIDES": str(len(demo.DEMO_CANDIDATES)),
        "HERACLES_GUIDE_LENGTH": str(len(best_guide)),
        "HERACLES_REFERENCE_LENGTH": str(len(demo.DEMO_REFERENCE)),
        "HERACLES_REFERENCE_SEGMENTS": str(len(demo.DEMO_REFERENCE_SEGMENTS)),
        "HERACLES_PLANTED_ON_TARGET": str(planted["on_target"]),
        "HERACLES_PLANTED_NEAR_MISS": str(planted["near_miss"]),
        "HERACLES_BEST_GUIDE_RISK": _fmt(get_num(targeting, "best_off_target_risk", 0.0)),
        "HERACLES_BEST_COMPOSITE": _fmt(get_num(targeting, "best_composite", 0.0) * 100.0),
        "HERACLES_MAX_MISMATCHES": str(demo.DEMO_MAX_MISMATCHES),
        "HERACLES_ABSORPTION_RATE": str(demo.DEMO_ABSORPTION_RATE),
        "HERACLES_EXPOSURE_TIME": str(demo.DEMO_EXPOSURE_TIME),
        "HERACLES_AVIDITY": str(demo.DEMO_AVIDITY),
        "HERACLES_DELIVERY_HORIZON_H": str(demo.DELIVERY_PLOT_HORIZON_H),
        "HERACLES_DELIVERY_ELIM_RATE": str(demo.DELIVERY_PLOT_ELIMINATION_RATE),
        "HERACLES_ANTAGONIST_CONC": str(demo.ANTAGONIST_CONC),
        "HERACLES_SEED": str(demo.DEMO_SEED),
        "HERACLES_INPUT_HASH": demo.input_hash()[:12],
        "HERACLES_BEST_GUIDE_SCORE": _fmt(get_num(targeting, "best_efficiency", 0.0) * 100.0),
        "HERACLES_POP_OFFTARGET": _fmt(get_num(targeting, "best_off_target_risk", 0.0)),
        "HERACLES_NEUTRALIZATION": _fmt(get_num(cm, "neutralization_probability", 0.0) * 100.0),
        "HERACLES_ANTIDOTE_COUNT": str(len(antidote_screening.ANTIDOTE_LIBRARY)),
        "HERACLES_BEST_ANTIDOTE": str(antidote.get("best_antidote", "n/a")),
        "HERACLES_ANTAGONIZED_PCT": _fmt(
            get_num(antidote, "best_antagonized_fraction", 0.0) * 100.0
        ),
        "HERACLES_SURVIVAL_PCT": _fmt(get_num(antidote, "best_survival_probability", 0.0) * 100.0),
        "HERACLES_WINDOW": _fmt(get_num(antidote, "challenge_therapeutic_window", 0.0)),
        "HERACLES_MARGIN": _fmt(get_num(antidote, "challenge_margin_of_safety", 0.0)),
        "HERACLES_ABSORBED_DOSE": _fmt(get_num(exposure, "absorbed_dose", 0.0)),
        "HERACLES_MOE": _fmt(get_num(exposure, "margin_of_exposure", 0.0)),
        "HERACLES_RQ": _fmt(get_num(exposure, "risk_quotient", 0.0)),
        "HERACLES_CUMULATIVE": _fmt(get_num(exposure, "cumulative_exposure", 0.0)),
        "HERACLES_EXPOSURE_VERDICT": str(exposure.get("verdict", "n/a")),
        "HERACLES_EXP_CONCENTRATION": str(exposure_params["concentration"]),
        "HERACLES_EXP_CONTACT_RATE": str(exposure_params["contact_rate"]),
        "HERACLES_EXP_DURATION": str(exposure_params["duration"]),
        "HERACLES_EXP_ABSORBED_FRACTION": str(exposure_params["absorption_fraction"]),
        "HERACLES_EXP_ELIMINATION_RATE": str(exposure_params["elimination_rate"]),
        "HERACLES_EXP_NOAEL": str(exposure_params["noael"]),
        "HERACLES_EXP_RFD": str(exposure_params["reference_dose"]),
        "HERACLES_LOD_SNR": str(delivery_forensics.DEFAULT_LOD_SNR),
        "HERACLES_SNR": _fmt(get_num(forensics, "snr")),
        "HERACLES_DETECTION_CONFIDENCE_PCT": _fmt(
            get_num(forensics, "detection_confidence") * 100.0
        ),
        "HERACLES_CONCENTRATION": _fmt(get_num(forensics, "concentration")),
        "HERACLES_TOP_MATCH": str(forensics.get("top_match", "n/a")),
        "HERACLES_MIX": _mix_primary(forensics.get("mixture")),
        "HERACLES_MIX_PRIMARY_PCT": _mix_weight(forensics.get("mixture"), "primary_weight"),
        "HERACLES_MIX_SECONDARY": _mix_secondary(forensics.get("mixture")),
        "HERACLES_MIX_SECONDARY_PCT": _mix_weight(forensics.get("mixture"), "secondary_weight"),
        "HERACLES_MIX_RESIDUAL": _mix_residual(forensics.get("mixture")),
        "HERACLES_RECOVERED_DOSE": _fmt(get_num(forensics, "recovered_dose", 0.0)),
        "HERACLES_FOR_SIGNAL": str(forensic_params["signal"]),
        "HERACLES_FOR_NOISE": str(forensic_params["noise_rms"]),
        "HERACLES_FOR_VOLUME": str(forensic_params["volume_ml"]),
        "HERACLES_FOR_TRANSFER": str(forensic_params["transfer_fraction"]),
        "HERACLES_FOR_SLOPE": str(forensic_params["calibration_slope"]),
        "HERACLES_FOR_INTERCEPT": str(forensic_params["calibration_intercept"]),
        # The single environment-dependent token. It is a property of the host
        # interpreter, not a wall-clock or random read: two runs on one
        # interpreter render byte-identical artifacts, two runs on different
        # Python patch releases differ in exactly this one substring.
        # ``tests/test_determinism.py`` pins that it is the only such token.
        "PYTHON_VERSION": platform.python_version(),
    }


def resolve_manuscript_tree(
    variables: dict[str, str],
    *,
    manuscript_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    strict: bool = True,
) -> tuple[Path, list[str]]:
    """Copy each numbered manuscript section to ``output/manuscript/``, substituting tokens.

    Only ``NN_*.md`` section files are copied (not sidecars such as
    ``SYNTAX.md`` or ``AGENTS.md``). In strict mode any leftover ``{{TOKEN}}``
    raises, so the manuscript can never render with raw braces.

    Returns the output directory and the sorted list of resolved file names.
    """
    manuscript_dir = (
        Path(manuscript_dir) if manuscript_dir is not None else PACKAGE_ROOT / "manuscript"
    )
    output_dir = (
        Path(output_dir) if output_dir is not None else PACKAGE_ROOT / "output" / "manuscript"
    )
    resolved: list[str] = []
    for source in sorted(manuscript_dir.glob("[0-9][0-9]_*.md")):
        text = source.read_text(encoding="utf-8")
        for token, value in variables.items():
            text = text.replace("{{" + token + "}}", value)
        unresolved = sorted(set(_TOKEN_RE.findall(text)))
        if unresolved and strict:
            raise ValueError(f"unresolved manuscript tokens in {source.name}: {unresolved}")
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / source.name).write_text(text, encoding="utf-8")
        resolved.append(source.name)
    return output_dir, resolved
