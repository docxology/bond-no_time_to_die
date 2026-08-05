# Agent Instructions — no_time_to_die (HERACLES)

Behavioral rules for AI agents working inside this PROJECT BOND film package.
Read this file **first** before modifying any project file. Every rule is
enforced by the package gates.

## R1 — Zero-mock testing

No `unittest.mock`, `MagicMock`, `@patch`, or `create_autospec` anywhere in
`tests/`. Tests exercise real algorithms and real data. Deterministic fakes
implement the REAL protocol contract — they are real providers, not mocks.

## R2 — Domain purity

`src/no_time_to_die/{bioweapon_counter,targeting_design,toxicology,antidote_screening,exposure_assessment,delivery_forensics,demo}.py`
must stay pure: no bond-api import, no `infrastructure.*`, no logic-hiding I/O.
The bond-api coupling lives ONLY in `src/no_time_to_die/mission.py` (the thin
adapter) and `manuscript_variables.py`/`figures/` (which read/write generated
artifacts). If bond-api is ever absent, the domain core must still import.

## R3 — Thin orchestrators

`scripts/` only bootstraps `sys.path` and forwards phase subcommands; all
business logic lives in `src/`. Never put math in a script.

## R4 — Live metrics, never hand-authored

Every numeric value in `manuscript/[0-9]*.md` must be a `{{TOKEN}}` resolved by
`src/no_time_to_die/manuscript_variables.py` from `manuscript/config.yaml` and
the shared `demo.py` result. Hardcoding a number that changes when config or
code changes is the primary manuscript-drift bug.

This covers **setup parameters, not just results**. The experimental-setup
table once repeated the `demo.py` constants as literals; changing a constant
silently falsified the table. Every cell is now a token. The exempt numerals
are film years, citation years/pages, ordered-list indices, formula constants
inside fenced blocks, and the coverage-gate threshold (which describes the gate
rather than reporting a measurement).

Figure captions count as prose: if a figure annotates a parameter, the renderer
must read it from `demo.py` and the caption must cite the same token.

## R4b — Prefer a source of truth over a repeated literal

If a value appears in two places it will eventually appear in two *different*
places. `demo.DOMAIN_MODULES` exists so the gadget registry and the module-count
token cannot disagree; `demo.DELIVERY_PLOT_*` exists because the delivery figure
previously marked a 2.0 h "exposure window" while the demonstration used 4.0 h.
When you add a constant, ask which other file will want it.

## R5 — Determinism

Fixed inputs in `demo.py`. **No module under `src/` may import `datetime`,
`time`, `random`, `secrets`, `uuid`, `socket`, or `tempfile`**, and the package
makes exactly one environment read in total — `platform.python_version()`,
rendered as `PYTHON_VERSION`, the single host-dependent token.
`MissionOutcome.provenance.wall_time_s` is pinned to `0.0` for the same reason.
Two runs on one interpreter must be byte-identical in generated artifacts.

There is no allowed wall-clock stamp. This rule previously carved out a
`GENERATION_TIMESTAMP` token *and* demanded byte-identical runs in the same
paragraph, which cannot both hold; the token stamped `datetime.now()` into the
persisted JSON and into the rendered manuscript, and consecutive runs differed.
The token is gone. `tests/test_determinism.py` enforces all three gates (import
scan, rendered-value scan, two-render byte comparison) and each carries a
positive control proving it reports a reintroduced violation.

`DEMO_SEED` is recorded for provenance only: no code path draws from an RNG, so
the seed governs nothing today. Say that rather than implying it controls
reproducibility.

## R6 — No exemplar lineage

Do not reintroduce the template exemplar's name or file names. The lineage `rg`
gate uses the bracket-split spell `template[_]code_project` so this doc cannot
trip its own check.

## R7 — Every gate must be able to fail

Do not add a defensive branch no input can reach, an assertion true by
construction, or an enumerated check without a positive control proving each
entry is load-bearing. See `docs/testing_philosophy.md` § "A gate must be able
to fail".

## Consequence matrix

| Rule | Fail example | Gate it trips |
| --- | --- | --- |
| R1 | `from unittest.mock import patch` | `grep` mock scan |
| R2 | `import bond_api` in `toxicology.py` | mypy/import lock + review |
| R3 | gradient math inside a script | review + tests |
| R4 | literal `0.75` for sensitivity in prose | token cross-ref test |
| R4 | a setup-table cell repeating a `demo.py` constant | review + strict token gate |
| R4b | a renamed demo result key silently hydrating `0` | `check_demo_completeness` |
| R5 | `time.time()` or `datetime.now()` anywhere in `src/` | `test_determinism.py` import scan |
| R5 | a rendered token shaped like a date or a clock time | `test_determinism.py` value scan |
| R7 | a ledger constant edited on one side only | `test_claim_ledger.py` |
| R7 | a degenerate demo input that forces its own result | `test_demo_evidence.py` |
| R6 | the literal `template[_]code_project` appears in a doc | lineage `rg` |
| R7 | an assertion that cannot fail | positive-control tests |

## Pre-submit checklist

Run from the package root:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
```
