"""Subprocess smoke tests for the thin phase CLIs."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = PROJECT_ROOT / "scripts"


def _run(*args: str, cwd: Path = PROJECT_ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )


class TestRunMissionCLI:
    def test_all_flow_exit_zero(self) -> None:
        proc = _run(str(SCRIPTS / "run_mission.py"), "all")
        assert proc.returncode == 0, proc.stderr
        assert "BRIEF" in proc.stdout
        assert "DEBRIEF" in proc.stdout
        assert "HERACLES" in proc.stdout

    def test_default_phase_is_all(self) -> None:
        proc = _run(str(SCRIPTS / "run_mission.py"))
        assert proc.returncode == 0
        assert "DEBRIEF" in proc.stdout

    def test_brief_phase(self) -> None:
        proc = _run(str(SCRIPTS / "run_mission.py"), "brief")
        assert proc.returncode == 0
        assert "no_time_to_die" in proc.stdout
        assert "DEBRIEF" not in proc.stdout

    def test_unknown_phase_exit_2(self) -> None:
        proc = _run(str(SCRIPTS / "run_mission.py"), "bogus")
        assert proc.returncode == 2
        assert "unknown phase" in proc.stderr


class TestPhaseWrappers:
    def test_brief_wrapper(self) -> None:
        proc = _run(str(SCRIPTS / "brief.py"))
        assert proc.returncode == 0

    def test_execute_wrapper(self) -> None:
        proc = _run(str(SCRIPTS / "execute.py"))
        assert proc.returncode == 0
        assert "MissionOutcome" in proc.stdout


class TestManuscriptGeneratorScript:
    def test_generates_variables_and_figures(self) -> None:
        proc = _run(str(SCRIPTS / "z_generate_manuscript_variables.py"), "--allow-draft")
        assert proc.returncode == 0, proc.stderr
        assert "rendered figure" in proc.stdout
        json_path = PROJECT_ROOT / "output" / "data" / "manuscript_variables.json"
        assert json_path.is_file()
