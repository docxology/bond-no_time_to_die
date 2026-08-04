"""HERACLES mission CLI — thin per-phase orchestrator.

Dispatches the five mission phases (brief / recon / plan / execute / debrief)
against the frozen bond-api provider. Business logic lives in
:mod:`no_time_to_die.mission` and the pure domain core; this module only
bootstraps ``src/`` onto ``sys.path`` and forwards phase subcommands.

Usage::

    uv run python scripts/run_mission.py [brief|recon|plan|execute|debrief|all]

``all`` (the default) runs the full deterministic mission flow via
``bond_api.protocol.run_mission``.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Bootstrap src/ so the film package imports from anywhere (scripts run via
# `python scripts/run_mission.py` too).
_ROOT = Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from bond_api.protocol import (  # type: ignore[import-untyped]
    ReconRequest,
    run_mission,
)

from no_time_to_die.mission import CODENAME, PROVIDER

PHASES = ("brief", "recon", "plan", "execute", "debrief", "all")


def _show(title: str, payload: object) -> None:
    print(f"\n===== {title} =====")
    print(payload)


def run_phase(phase: str) -> object:
    """Run a single mission phase and return its protocol payload."""
    if phase == "brief":
        return PROVIDER.brief()
    if phase == "recon":
        request = ReconRequest(
            goal="assess HERACLES countermeasure, poison-garden toxicology, "
            "and vesper trace forensics"
        )
        return PROVIDER.recon(request)
    if phase == "plan":
        return PROVIDER.plan(PROVIDER.brief())
    if phase == "execute":
        return PROVIDER.execute(PROVIDER.plan(PROVIDER.brief()))
    if phase == "debrief":
        return run_mission(PROVIDER, ReconRequest(goal=CODENAME))
    raise ValueError(f"unknown phase {phase!r}")


def main(argv: list[str] | None = None) -> int:
    """Entry point returning a process exit code (0 on success)."""
    argv = list(sys.argv[1:] if argv is None else argv)
    phase = argv[0] if argv else "all"
    if phase not in PHASES:
        print(f"unknown phase {phase!r}; expected one of {', '.join(PHASES)}", file=sys.stderr)
        return 2

    if phase == "all":
        brief = PROVIDER.brief()
        _show("BRIEF", brief)
        _show("RECON", PROVIDER.recon(ReconRequest(goal=CODENAME)))
        plan = PROVIDER.plan(brief)
        _show("PLAN", plan)
        outcome = PROVIDER.execute(plan)
        _show("EXECUTE", outcome)
        _show("DEBRIEF", PROVIDER.debrief(outcome))
    else:
        _show(phase.upper(), run_phase(phase))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
