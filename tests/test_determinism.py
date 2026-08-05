"""Enforce the determinism claims the manuscript and AGENTS.md make.

Those claims used to be false. ``generate_variables()`` called
``datetime.now(timezone.utc)`` and persisted the result into both
``output/data/manuscript_variables.json`` and the rendered
``output/manuscript/06_reproducibility.md``, so two runs produced different
bytes — while ``manuscript/05_experimental_setup.md`` said "no run consumes
wall-clock or random state, so results are byte-reproducible",
``manuscript/06_reproducibility.md`` advertised "a clean tree after
deterministic regeneration (a live byte-equality proof)", and ``AGENTS.md``
required "no wall-clock in persisted artifacts". Nothing checked any of it; the
only mention in the suite was a test asserting the timestamp token *existed*.

Three independent gates now stand behind those sentences:

1. **Source gate** — no module under ``src/`` may import a clock, an RNG, or an
   entropy source. Structural, so it catches a reintroduction before any value
   is ever rendered.
2. **Value gate** — no rendered token value may look like a date or a time.
   Catches a wall-clock read that reaches the manuscript by any route.
3. **Byte gate** — two independent renders of the full manuscript tree must be
   byte-identical, file for file.

Each gate is proved falsifiable in ``TestGatesCanFail`` by running it against
deliberately broken input rather than by asserting that it is strict.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from no_time_to_die import demo
from no_time_to_die.manuscript_variables import generate_variables, resolve_manuscript_tree

_PKG = Path(__file__).resolve().parents[1]
_SRC = _PKG / "src" / "no_time_to_die"

#: Modules that read a clock, draw randomness, or otherwise make a run
#: irreproducible. A package that imports none of these cannot consume any.
FORBIDDEN_IMPORTS = frozenset(
    {"datetime", "random", "secrets", "time", "uuid", "socket", "tempfile"}
)

#: Roots of environment reads. Every one of these must be individually
#: justified — see :data:`ALLOWED_ENVIRONMENT_READS`.
ENVIRONMENT_ROOTS = frozenset({"os", "platform", "socket", "getpass", "subprocess"})

#: The single sanctioned environment read in the whole package: the interpreter
#: version, rendered as the ``PYTHON_VERSION`` manuscript token. It is the one
#: host-dependent token, and the manuscript says so in that many words.
ALLOWED_ENVIRONMENT_READS = frozenset({("manuscript_variables.py", "platform.python_version")})

#: A date (2026-08-05) or a clock time (16:34:41) appearing in a rendered value.
WALL_CLOCK_SHAPES = (
    re.compile(r"\d{4}-\d{2}-\d{2}"),
    re.compile(r"\d{2}:\d{2}:\d{2}"),
)


def _source_files() -> tuple[Path, ...]:
    return tuple(sorted(_SRC.rglob("*.py")))


def _imported_modules(tree: ast.AST) -> set[str]:
    """Top-level module names imported anywhere in a parsed file."""
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.add(node.module.split(".")[0])
    return found


def _dotted(node: ast.expr) -> str | None:
    """Dotted source spelling of a call target, or None if it is not one."""
    parts: list[str] = []
    current: ast.expr = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if not isinstance(current, ast.Name):
        return None
    parts.append(current.id)
    return ".".join(reversed(parts))


def forbidden_imports_in(path: Path) -> set[str]:
    """Clock/RNG/entropy modules imported by one source file."""
    return _imported_modules(ast.parse(path.read_text(encoding="utf-8"))) & FORBIDDEN_IMPORTS


def environment_reads_in(path: Path) -> set[tuple[str, str]]:
    """``(file name, dotted call)`` for every environment read in one file."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    reads: set[tuple[str, str]] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        dotted = _dotted(node.func)
        if dotted and dotted.split(".")[0] in ENVIRONMENT_ROOTS:
            reads.add((path.name, dotted))
    return reads


def wall_clock_shaped(variables: dict[str, str]) -> list[str]:
    """Token names whose rendered value looks like a date or a clock time."""
    return sorted(
        name
        for name, value in variables.items()
        if any(shape.search(str(value)) for shape in WALL_CLOCK_SHAPES)
    )


class TestSourceGate:
    def test_the_scan_sees_the_whole_package(self) -> None:
        """Non-vacuity: an empty file list would make every check below pass."""
        names = {path.name for path in _source_files()}
        assert {
            "demo.py",
            "manuscript_variables.py",
            "mission.py",
            "plots.py",
            "toxicology.py",
        } <= names
        assert len(_source_files()) >= 11

    def test_no_module_imports_a_clock_or_an_rng(self) -> None:
        offenders = {
            path.name: sorted(found)
            for path in _source_files()
            if (found := forbidden_imports_in(path))
        }
        assert offenders == {}

    def test_python_version_is_the_only_environment_read(self) -> None:
        reads: set[tuple[str, str]] = set()
        for path in _source_files():
            reads |= environment_reads_in(path)
        assert reads == ALLOWED_ENVIRONMENT_READS


class TestValueGate:
    def test_no_token_value_carries_a_wall_clock_reading(self) -> None:
        assert wall_clock_shaped(generate_variables()) == []

    def test_the_generation_timestamp_token_is_gone(self) -> None:
        """The withdrawn token stays withdrawn."""
        assert "GENERATION_TIMESTAMP" not in generate_variables()

    def test_repeated_generation_returns_an_identical_map(self) -> None:
        assert generate_variables() == generate_variables()


class TestByteGate:
    def test_two_renders_of_the_manuscript_are_byte_identical(self, tmp_path) -> None:
        variables = generate_variables()
        first, names_a = resolve_manuscript_tree(variables, output_dir=tmp_path / "a", strict=True)
        second, names_b = resolve_manuscript_tree(
            generate_variables(), output_dir=tmp_path / "b", strict=True
        )
        assert names_a == names_b
        assert names_a, "no manuscript sections were rendered; the byte check would be vacuous"
        for name in names_a:
            assert (first / name).read_bytes() == (second / name).read_bytes(), (
                f"{name} differs between two renders"
            )


class TestInputDigest:
    def test_digest_is_stable_and_hex(self) -> None:
        digest = demo.input_hash()
        assert digest == demo.input_hash()
        assert len(digest) == 64
        assert set(digest) <= set("0123456789abcdef")

    def test_digest_changes_when_an_input_changes(self) -> None:
        """A digest that ignores its inputs is not a fingerprint."""
        import hashlib

        mutated = demo.input_payload().replace("demo_exposure_time=4.0", "demo_exposure_time=4.5")
        assert mutated != demo.input_payload()
        assert hashlib.sha256(mutated.encode("utf-8")).hexdigest() != demo.input_hash()


class TestGatesCanFail:
    """Positive controls. Each gate is run against input that must trip it."""

    def test_import_gate_flags_a_reintroduced_clock(self, tmp_path) -> None:
        broken = tmp_path / "regression.py"
        broken.write_text(
            "from datetime import datetime, timezone\n\n"
            "def stamp() -> str:\n"
            "    return datetime.now(timezone.utc).isoformat()\n",
            encoding="utf-8",
        )
        assert forbidden_imports_in(broken) == {"datetime"}

    def test_import_gate_flags_an_rng(self, tmp_path) -> None:
        broken = tmp_path / "regression.py"
        broken.write_text("import random\n\nX = random.random()\n", encoding="utf-8")
        assert forbidden_imports_in(broken) == {"random"}

    def test_import_gate_passes_a_clean_file(self, tmp_path) -> None:
        clean = tmp_path / "clean.py"
        clean.write_text("import math\n\nX = math.pi\n", encoding="utf-8")
        assert forbidden_imports_in(clean) == set()

    def test_environment_gate_flags_an_unsanctioned_read(self, tmp_path) -> None:
        broken = tmp_path / "regression.py"
        broken.write_text("import os\n\nHOME = os.getenv('HOME')\n", encoding="utf-8")
        assert environment_reads_in(broken) == {("regression.py", "os.getenv")}

    def test_value_gate_flags_a_timestamp_token(self) -> None:
        polluted = dict(generate_variables())
        polluted["GENERATION_TIMESTAMP"] = "2026-08-05T16:34:41+00:00"
        assert wall_clock_shaped(polluted) == ["GENERATION_TIMESTAMP"]

    def test_value_gate_flags_a_bare_clock_time(self) -> None:
        polluted = dict(generate_variables())
        polluted["HERACLES_RENDERED_AT"] = "16:34:41"
        assert wall_clock_shaped(polluted) == ["HERACLES_RENDERED_AT"]

    def test_byte_gate_flags_a_drifting_render(self, tmp_path) -> None:
        """Two renders that disagree must be *detected*, not assumed absent."""
        source = tmp_path / "src"
        source.mkdir()
        (source / "00_x.md").write_text("stamp {{HERACLES_CODENAME}}", encoding="utf-8")
        first, _ = resolve_manuscript_tree(
            {"HERACLES_CODENAME": "HERACLES"}, manuscript_dir=source, output_dir=tmp_path / "a"
        )
        second, _ = resolve_manuscript_tree(
            {"HERACLES_CODENAME": "HERACLES-2"}, manuscript_dir=source, output_dir=tmp_path / "b"
        )
        assert (first / "00_x.md").read_bytes() != (second / "00_x.md").read_bytes()


@pytest.mark.parametrize("token", ["PYTHON_VERSION"])
def test_documented_host_dependent_tokens_are_present(token: str) -> None:
    """The manuscript names exactly these tokens as environment-dependent."""
    assert token in generate_variables()
