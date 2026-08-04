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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from no_time_to_die import delivery_forensics, demo, toxicology

__all__ = [
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
    """Format a scaled number compactly for prose (deterministic)."""
    if isinstance(value, int):
        return str(value)
    return f"{value:.{digits}g}"


def generate_variables(
    *,
    config_path: str | Path | None = None,
    require_outputs: bool = True,
) -> dict[str, str]:
    """Compute the ``{{TOKEN}}`` → value mapping for the manuscript.

    Args:
        config_path: Override for ``manuscript/config.yaml``.
        require_outputs: When True (default), require the deterministic demo to
            expose a non-empty countermeasure result — the strict gate that
            keeps metrics live rather than hand-authored.
    """
    config = load_manuscript_config(config_path)
    paper = config.get("paper", {})
    if not isinstance(paper, dict):
        raise ValueError(  # noqa: TRY004 — ValueError validation is the package convention
            "manuscript config 'paper' section must be a mapping"
        )
    authors = config.get("authors", [])
    author_name = authors[0].get("name", "") if isinstance(authors, list) and authors else ""

    results = demo.run_demo()
    countermeasure = results["countermeasure"]
    if not isinstance(countermeasure, dict) or not countermeasure:
        if require_outputs:
            raise ValueError("countermeasure demo result is empty — cannot hydrate manuscript")
        countermeasure = {}

    cm = countermeasure
    tox_stats = results["toxicology_stats"]
    if not isinstance(tox_stats, dict):
        tox_stats = {}
    forensics = results["forensics"]
    if not isinstance(forensics, dict):
        forensics = {}

    def get_num(mapping: dict[str, Any], key: str, default: float = 0.0) -> float:
        val = mapping.get(key)
        return float(val) if isinstance(val, (int, float)) else default

    return {
        "HERACLES_TITLE": str(paper.get("title", "")),
        "HERACLES_SUBTITLE": str(paper.get("subtitle", "")),
        "HERACLES_VERSION": str(paper.get("version", "")),
        "HERACLES_CODENAME": str(config.get("film", {}).get("codename", "HERACLES")),
        "HERACLES_AUTHOR": author_name,
        "HERACLES_NUM_TOXINS": str(len(toxicology.TOXIN_CATALOG)),
        "HERACLES_NUM_LIBRARY": str(len(delivery_forensics.SPECTRUM_LIBRARY)),
        "HERACLES_MIN_LD50": str(tox_stats.get("min_ld50", 0.0)),
        "HERACLES_MEDIAN_LD50": str(tox_stats.get("median_ld50", 0.0)),
        "HERACLES_SPECIFICITY": _fmt(get_num(cm, "specificity", 100.0) * 100.0),
        "HERACLES_BEST_GUIDE": str(cm.get("best_guide", "n/a")),
        "HERACLES_NEUTRALIZATION": _fmt(get_num(cm, "neutralization_probability", 0.0) * 100.0),
        "HERACLES_LOD_SNR": str(delivery_forensics.DEFAULT_LOD_SNR),
        "HERACLES_RECOVERED_DOSE": _fmt(get_num(forensics, "recovered_dose", 0.0)),
        "PYTHON_VERSION": platform.python_version(),
        "GENERATION_TIMESTAMP": datetime.now(timezone.utc).isoformat(timespec="seconds"),
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
