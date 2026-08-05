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

    def test_strict_mode_resolves_the_whole_manuscript(self) -> None:
        """The default (strict) path must succeed, not just ``--allow-draft``."""
        proc = _run(str(SCRIPTS / "z_generate_manuscript_variables.py"))
        assert proc.returncode == 0, proc.stderr
        assert "resolved" in proc.stdout

    def test_two_full_runs_write_identical_persisted_artifacts(self) -> None:
        """End-to-end byte-equality, through the real script and the real tree.

        This is the "clean tree after deterministic regeneration" the
        reproducibility section advertises. It was false: the persisted JSON and
        the rendered ``06_reproducibility.md`` both carried a wall-clock stamp,
        so consecutive runs differed. Note that a second-resolution timestamp
        only *sometimes* differs between two fast runs — which is why the
        structural import gate in ``tests/test_determinism.py``, not this test,
        is the primary defence. This one confirms the end-to-end result.
        """
        data = PROJECT_ROOT / "output" / "data" / "manuscript_variables.json"
        rendered = PROJECT_ROOT / "output" / "manuscript"

        assert _run(str(SCRIPTS / "z_generate_manuscript_variables.py")).returncode == 0
        first_json = data.read_bytes()
        first_tree = {path.name: path.read_bytes() for path in sorted(rendered.glob("*.md"))}
        assert first_tree, "nothing was rendered; the comparison would be vacuous"

        assert _run(str(SCRIPTS / "z_generate_manuscript_variables.py")).returncode == 0
        assert data.read_bytes() == first_json
        second_tree = {path.name: path.read_bytes() for path in sorted(rendered.glob("*.md"))}
        assert second_tree == first_tree
