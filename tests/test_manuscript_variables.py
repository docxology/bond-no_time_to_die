"""Tests for manuscript_variables.py — token hydration and live cross-reference."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from no_time_to_die.manuscript_variables import (
    generate_variables,
    load_manuscript_config,
    resolve_manuscript_tree,
)

_PKG = Path(__file__).resolve().parents[1]
_MANUSCRIPT = _PKG / "manuscript"

_TOKEN_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")

#: Tokens reserved for guide/sidecar files, excluded from the prose cross-ref.
_GUIDE_TOKENS = {"HERACLES_TITLE", "HERACLES_SUBTITLE", "HERACLES_CODENAME"}


class TestLoadConfig:
    def test_loads_dict(self) -> None:
        config = load_manuscript_config()
        assert isinstance(config, dict)
        assert config["film"]["codename"] == "HERACLES"

    def test_missing_file_raises(self, tmp_path) -> None:
        with pytest.raises(FileNotFoundError):
            load_manuscript_config(tmp_path / "nope.yaml")

    def test_non_mapping_raises(self, tmp_path) -> None:
        bad = tmp_path / "bad.yaml"
        bad.write_text("- just\n- a\n- list\n", encoding="utf-8")
        with pytest.raises(ValueError):
            load_manuscript_config(bad)


class TestGenerateVariables:
    def test_expected_keys_present(self) -> None:
        variables = generate_variables()
        for key in (
            "HERACLES_TITLE",
            "HERACLES_CODENAME",
            "HERACLES_NUM_TOXINS",
            "HERACLES_SPECIFICITY",
            "HERACLES_NEUTRALIZATION",
            "HERACLES_LOD_SNR",
            "PYTHON_VERSION",
            "GENERATION_TIMESTAMP",
        ):
            assert key in variables

    def test_numeric_tokens_consistent_with_domain(self) -> None:
        variables = generate_variables()
        from no_time_to_die import toxicology

        assert variables["HERACLES_NUM_TOXINS"] == str(len(toxicology.TOXIN_CATALOG))
        assert variables["HERACLES_LOD_SNR"] == "3.0"

    def test_specificity_token_format(self) -> None:
        variables = generate_variables()
        spec = float(variables["HERACLES_SPECIFICITY"])
        assert 0.0 <= spec <= 100.0


class TestProseCrossReference:
    def test_every_prose_token_is_generated(self) -> None:
        variables = generate_variables()
        generated = set(variables)
        for section in sorted(_MANUSCRIPT.glob("[0-9][0-9]_*.md")):
            text = section.read_text(encoding="utf-8")
            tokens = set(_TOKEN_RE.findall(text))
            missing = tokens - generated
            assert not missing, f"{section.name} references undefined tokens {sorted(missing)}"

    def test_guide_tokens_appear_nowhere_unresolved(self) -> None:
        # The strict resolver must leave no literal {{TOKEN}} in rendered prose.
        variables = generate_variables()
        out_dir = _PKG / "output" / "manuscript"
        resolve_manuscript_tree(variables, output_dir=out_dir, strict=True)
        for resolved in out_dir.glob("[0-9][0-9]_*.md"):
            leftover = _TOKEN_RE.findall(resolved.read_text(encoding="utf-8"))
            assert not leftover, f"{resolved.name} has leftover tokens {leftover}"


class TestResolveTree:
    def test_resolves_and_writes(self, tmp_path) -> None:
        src = tmp_path / "src"
        out = tmp_path / "out"
        src.mkdir()
        (src / "00_hello.md").write_text(
            "Hello {{HERACLES_CODENAME}} count {{HERACLES_NUM_TOXINS}}", encoding="utf-8"
        )
        variables = generate_variables()
        out_dir, names = resolve_manuscript_tree(
            variables, manuscript_dir=src, output_dir=out, strict=True
        )
        assert names == ["00_hello.md"]
        text = (out_dir / "00_hello.md").read_text(encoding="utf-8")
        assert "HERACLES" in text
        assert "{{" not in text

    def test_only_numbered_sections_copied(self, tmp_path) -> None:
        src = tmp_path / "src"
        out = tmp_path / "out"
        src.mkdir()
        (src / "00_a.md").write_text("{{HERACLES_CODENAME}}", encoding="utf-8")
        (src / "SYNTAX.md").write_text("{{LITERAL_PLACEHOLDER}}", encoding="utf-8")
        variables = generate_variables()
        _, names = resolve_manuscript_tree(variables, manuscript_dir=src, output_dir=out)
        assert names == ["00_a.md"]

    def test_strict_rejects_unresolved(self, tmp_path) -> None:
        src = tmp_path / "src"
        out = tmp_path / "out"
        src.mkdir()
        (src / "00_b.md").write_text("{{NOT_A_REAL_TOKEN}}", encoding="utf-8")
        variables = generate_variables()
        with pytest.raises(ValueError, match="unresolved manuscript tokens"):
            resolve_manuscript_tree(variables, manuscript_dir=src, output_dir=out, strict=True)

    def test_non_strict_allows_unresolved(self, tmp_path) -> None:
        src = tmp_path / "src"
        out = tmp_path / "out"
        src.mkdir()
        (src / "00_c.md").write_text("{{NOT_A_REAL_TOKEN}}", encoding="utf-8")
        variables = generate_variables()
        _, names = resolve_manuscript_tree(
            variables, manuscript_dir=src, output_dir=out, strict=False
        )
        assert names == ["00_c.md"]
