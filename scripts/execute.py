"""Phase CLI: execute — run the mission and persist a provenance record.

Thin orchestrator: boots ``src/``, runs the deterministic HERACLES execution
through the frozen bond-api provider, and writes a machine-readable mission
record via ``bond_utilities.mission_io.record_provenance_outcome`` into
``output/data/mission_record.json``. The ``started_at``/``now`` stamps are
**pinned** (not ``datetime.now()``), so the record is byte-identical across two
runs on one interpreter — the package's determinism contract holds end to end.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

# Bootstrap src/ so the film package imports from anywhere.
_ROOT = Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from bond_utilities.mission_io import record_provenance_outcome  # type: ignore[import-untyped]

from no_time_to_die import __version__, demo
from no_time_to_die.mission import CODENAME, PROVIDER


def _main() -> int:
    """Execute the mission, persist its provenance, and report."""
    outcome = PROVIDER.execute(PROVIDER.plan(PROVIDER.brief()))
    print(outcome)

    record_path = _ROOT / "output" / "data" / "mission_record.json"
    # Deterministic provenance: pin the clock. record_provenance_outcome calls
    # datetime.now(timezone.utc) *unless* BOTH started_at and now are supplied;
    # a real wall-clock read here would break byte-identity across runs.
    pinned_now = datetime(2026, 8, 6, tzinfo=timezone.utc)
    started_at = "2026-08-06T00:00:00+00:00"
    record_provenance_outcome(
        mission_id="no_time_to_die",
        seed=demo.DEMO_SEED,
        version=__version__,
        input_payload={
            "canonical_input": demo.input_payload(),
            "input_hash": demo.input_hash(),
        },
        outcome=dict(outcome.results),
        path=record_path,
        codename=CODENAME,
        started_at=started_at,
        now=pinned_now,
    )
    print(f"provenance record written: {record_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
