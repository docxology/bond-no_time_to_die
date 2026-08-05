"""Hydrate manuscript tokens and render HERACLES figures (thin orchestrator).

Writes ``output/data/manuscript_variables.json``, resolves the substituted
manuscript tree to ``output/manuscript/``, and renders the five concept
figures under ``output/figures/``. Strict by default: any unresolved
``{{TOKEN}}`` fails the run.

Usage::

    uv run python scripts/z_generate_manuscript_variables.py [--allow-draft]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from no_time_to_die.figures import plots
from no_time_to_die.manuscript_variables import (
    generate_variables,
    resolve_manuscript_tree,
)


def main(argv: list[str] | None = None) -> int:
    """Hydrate tokens, resolve the manuscript, and render figures."""
    argv = list(sys.argv[1:] if argv is None else argv)
    strict = "--allow-draft" not in argv
    variables = generate_variables(require_outputs=strict)

    data_dir = _ROOT / "output" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "manuscript_variables.json").write_text(
        json.dumps(variables, indent=2, sort_keys=True), encoding="utf-8"
    )

    out_dir, resolved = resolve_manuscript_tree(variables, strict=strict)
    figures = plots.render_all_figures()
    print(f"resolved {len(resolved)} manuscript sections under {out_dir}")
    for figure in figures:
        print(f"rendered figure: {figure}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
