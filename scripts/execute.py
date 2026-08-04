"""Phase CLI: execute. Thin wrapper over scripts/run_mission.py."""

from __future__ import annotations

from run_mission import main  # type: ignore[import-not-found]

if __name__ == "__main__":
    raise SystemExit(main(["execute"]))
