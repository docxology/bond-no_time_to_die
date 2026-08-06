"""Tests for manuscript_variables.py — token hydration and live cross-reference."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

from no_time_to_die import demo
from no_time_to_die.manuscript_variables import (
    REQUIRED_DEMO_KEYS,
    REQUIRED_TOP_LEVEL_KEYS,
    check_demo_completeness,
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
            "HERACLES_NUM_GUIDES",
            "HERACLES_BEST_GUIDE_SCORE",
            "HERACLES_POP_OFFTARGET",
            "HERACLES_ANTIDOTE_COUNT",
            "HERACLES_BEST_ANTIDOTE",
            "HERACLES_SURVIVAL_PCT",
            "HERACLES_MOE",
            "HERACLES_EXPOSURE_VERDICT",
            "PYTHON_VERSION",
            "HERACLES_CM_BEST_GUIDE",
            "HERACLES_DESIGN_BEST_GUIDE",
            "HERACLES_PLANTED_ON_TARGET",
            "HERACLES_PLANTED_NEAR_MISS",
            "HERACLES_FOR_INTERCEPT",
        ):
            assert key in variables

    def test_numeric_tokens_consistent_with_domain(self) -> None:
        variables = generate_variables()
        from no_time_to_die import antidote_screening, toxicology

        assert variables["HERACLES_NUM_TOXINS"] == str(len(toxicology.TOXIN_CATALOG))
        assert variables["HERACLES_LOD_SNR"] == "3.0"
        assert variables["HERACLES_ANTIDOTE_COUNT"] == str(len(antidote_screening.ANTIDOTE_LIBRARY))

    def test_specificity_token_format(self) -> None:
        variables = generate_variables()
        spec = float(variables["HERACLES_SPECIFICITY"])
        assert 0.0 <= spec <= 100.0

    def test_missing_mixture_yields_fallback_tokens(self) -> None:
        """If the demo result has no mixture decomposition (or a future one
        drops it), the mix tokens degrade to their documented fallbacks rather
        than crashing -- and the gate names the dropped key when on."""
        results = demo.run_demo()
        del results["forensics"]["mixture"]  # type: ignore[literal-required]
        variables = generate_variables(results=results, require_outputs=False)
        assert variables["HERACLES_MIX"] == "n/a"
        assert variables["HERACLES_MIX_PRIMARY_PCT"] == "0"
        assert variables["HERACLES_MIX_SECONDARY"] == "n/a"
        assert variables["HERACLES_MIX_SECONDARY_PCT"] == "0"
        assert variables["HERACLES_MIX_RESIDUAL"] == "0"
        with pytest.raises(ValueError, match=re.escape("forensics.mixture")):
            generate_variables(results=results, require_outputs=True)

    def test_single_component_mixture_tokens(self) -> None:
        """A pure single-poison mixture has no secondary: the token reads
        ``none`` and the secondary weight stays ``0``."""
        results = demo.run_demo()
        results["forensics"]["mixture"] = {
            "primary": "ricin",
            "primary_weight": 1.0,
            "secondary": None,
            "secondary_weight": None,
            "residual": 0.0,
            "num_components": 1,
        }
        variables = generate_variables(results=results, require_outputs=False)
        assert variables["HERACLES_MIX_SECONDARY"] == "none"
        assert variables["HERACLES_MIX_SECONDARY_PCT"] == "0"
        assert variables["HERACLES_MIX_PRIMARY_PCT"] != "0"


class TestProseCrossReference:
    def test_every_prose_token_is_generated(self) -> None:
        variables = generate_variables()
        generated = set(variables)
        for section in sorted(_MANUSCRIPT.glob("[0-9][0-9]_*.md")):
            text = section.read_text(encoding="utf-8")
            tokens = set(_TOKEN_RE.findall(text))
            missing = tokens - generated
            assert not missing, f"{section.name} references undefined tokens {sorted(missing)}"

    def test_each_section_cites_its_own_guide_selector(self) -> None:
        """The two selectors are different models and may disagree.

        ``select_best_guide`` maximizes specificity; ``design_report`` maximizes
        an efficiency/off-target composite. A single ``HERACLES_BEST_GUIDE``
        token hydrated from the design report was quoted in both the
        countermeasure and the guide-design sections, so the countermeasure
        prose would silently attribute the design model's answer to
        ``select_best_guide`` the moment the two diverged.
        """
        text = (_MANUSCRIPT / "03_results.md").read_text(encoding="utf-8")
        _, _, rest = text.partition("## Countermeasure demonstration")
        countermeasure_body, _, rest = rest.partition("## Guide-design ranking")
        design_body, _, _ = rest.partition("## Poison-garden catalog")
        assert "{{HERACLES_CM_BEST_GUIDE}}" in countermeasure_body
        assert "{{HERACLES_DESIGN_BEST_GUIDE}}" not in countermeasure_body
        assert "{{HERACLES_DESIGN_BEST_GUIDE}}" in design_body
        assert "{{HERACLES_CM_BEST_GUIDE}}" not in design_body

    def test_the_ambiguous_guide_token_is_not_used_in_prose(self) -> None:
        for section in sorted(_MANUSCRIPT.glob("[0-9][0-9]_*.md")):
            body = section.read_text(encoding="utf-8")
            assert "{{HERACLES_BEST_GUIDE}}" not in body, (
                f"{section.name} uses the ambiguous token; cite CM_ or DESIGN_ explicitly"
            )

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


class TestConfigValidation:
    """The 'paper' section guard and the author fallback are real branches."""

    def _write_config(self, tmp_path: Path, body: str) -> Path:
        path = tmp_path / "config.yaml"
        path.write_text(body, encoding="utf-8")
        return path

    def test_non_mapping_paper_section_raises(self, tmp_path) -> None:
        bad = self._write_config(tmp_path, "paper:\n  - not\n  - a\n  - mapping\n")
        with pytest.raises(ValueError, match="'paper' section must be a mapping"):
            generate_variables(config_path=bad)

    def test_missing_authors_yields_empty_author_token(self, tmp_path) -> None:
        minimal = self._write_config(tmp_path, 'paper:\n  title: "T"\nfilm:\n  codename: "X"\n')
        variables = generate_variables(config_path=minimal)
        assert variables["HERACLES_AUTHOR"] == ""
        assert variables["HERACLES_CODENAME"] == "X"


class TestDemoCompletenessGate:
    """The strict gate must fail on a real structural regression."""

    def test_intact_demo_result_passes(self) -> None:
        check_demo_completeness(demo.run_demo())

    def test_dropped_key_is_reported(self) -> None:
        results = demo.run_demo()
        del results["countermeasure"]["specificity"]
        with pytest.raises(ValueError, match=r"countermeasure\.specificity"):
            check_demo_completeness(results)

    def test_every_required_key_is_individually_load_bearing(self) -> None:
        """Positive control: each declared key must actually be absent-able."""
        for section, keys in REQUIRED_DEMO_KEYS.items():
            for key in keys:
                results = demo.run_demo()
                del results[section][key]  # type: ignore[literal-required]
                with pytest.raises(ValueError, match=re.escape(f"{section}.{key}")):
                    check_demo_completeness(results)

    def test_every_top_level_key_is_individually_load_bearing(self) -> None:
        assert REQUIRED_TOP_LEVEL_KEYS, "an empty declaration makes this loop vacuous"
        for key in REQUIRED_TOP_LEVEL_KEYS:
            results = demo.run_demo()
            del results[key]  # type: ignore[misc]
            with pytest.raises(ValueError, match=re.escape(key)):
                check_demo_completeness(results)

    def test_a_missing_section_is_reported_not_crashed_on(self) -> None:
        results = demo.run_demo()
        del results["forensics"]  # type: ignore[misc]
        with pytest.raises(ValueError, match=r"forensics\.\*"):
            check_demo_completeness(results)

    def test_no_demo_result_key_can_go_missing_unnoticed(self) -> None:
        """The completeness claim itself, checked exhaustively.

        ``06_reproducibility.md`` says the gate "fails if the demo result is
        missing any key the tokens read". The declared-key positive control
        above only proves each *declared* key is load-bearing — it cannot see a
        key the tokens read but nobody declared, and there was one:
        ``garden_risk_combined``, a top-level float that the section-keyed scan
        was structurally blind to. Deleting it passed the gate and then raised a
        bare ``KeyError`` from inside ``generate_variables``.

        So: delete every key of a real demo result in turn, at both levels, and
        require each deletion to land in exactly one of two buckets.

        * **Guarded** — the gate raises, naming the key.
        * **Irrelevant** — with the gate off, every rendered token is
          byte-identical to the baseline, i.e. no token read it.

        Anything else is a hole. That includes the loud case (a ``KeyError``
        escaping the gate) *and* the quiet one (a token silently degrading to
        its ``0.0``/``"n/a"`` fallback), which is the failure mode that actually
        matters: a manuscript that renders a plausible zero is worse than one
        that fails to render.
        """
        baseline = generate_variables(results=demo.run_demo(), require_outputs=False)
        template = demo.run_demo()
        paths: list[tuple[str, ...]] = [(key,) for key in template]
        paths += [
            (section, key)
            for section, bucket in template.items()
            if isinstance(bucket, dict)
            for key in bucket
        ]
        assert len(paths) > 30, f"only {len(paths)} key paths found; the sweep is too thin"

        unguarded: list[str] = []
        for path in paths:
            label = ".".join(path)
            results = demo.run_demo()
            target: Any = results
            for step in path[:-1]:
                target = target[step]
            del target[path[-1]]
            try:
                generate_variables(results=results, require_outputs=True)
            except ValueError as exc:
                assert "manuscript-critical keys" in str(exc)
                continue  # guarded, and named
            except Exception as exc:  # noqa: BLE001 — the point is to catch anything else
                unguarded.append(f"{label} -> {type(exc).__name__} escaped the gate")
                continue
            degraded = generate_variables(results=results, require_outputs=False)
            drifted = sorted(key for key in baseline if baseline[key] != degraded.get(key))
            if drifted:
                unguarded.append(f"{label} -> silently changed {drifted}")
        assert unguarded == [], f"keys read by tokens but not guarded by the gate: {unguarded}"

    def test_the_sweep_detects_an_unguarded_key(self) -> None:
        """Positive control on the sweep: an unguarded key must be visible.

        ``garden_risk_combined`` is guarded now, so simulate the pre-fix state
        by checking that removing it from a result and calling the *generator*
        without the gate produces the fallback rather than a crash — and that
        the gate, when on, names it.
        """
        results = demo.run_demo()
        del results["garden_risk_combined"]  # type: ignore[misc]
        with pytest.raises(ValueError, match="garden_risk_combined"):
            generate_variables(results=results, require_outputs=True)
        # Gate off: the token degrades to the documented zero fallback.
        variables = generate_variables(results=results, require_outputs=False)
        assert variables["HERACLES_GARDEN_RISK_PCT"] == "0"

    def test_generate_variables_propagates_the_gate(self) -> None:
        results = demo.run_demo()
        del results["exposure"]["verdict"]
        with pytest.raises(ValueError, match="manuscript-critical keys"):
            generate_variables(results=results, require_outputs=True)

    def test_require_outputs_false_skips_the_gate(self) -> None:
        results = demo.run_demo()
        del results["exposure"]["verdict"]
        variables = generate_variables(results=results, require_outputs=False)
        assert variables["HERACLES_EXPOSURE_VERDICT"] == "n/a"
