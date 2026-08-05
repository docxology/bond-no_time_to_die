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

## R5 — Determinism

Fixed `seed = 11`; no untracked RNG; no wall-clock in persisted artifacts or
manuscript tokens (the `GENERATION_TIMESTAMP` token is the single allowed
wall-clock stamp). Two runs must be byte-identical in generated artifacts.

## R6 — No exemplar lineage

Do not reintroduce the template exemplar's name or file names. The lineage `rg`
gate uses the bracket-split spell `template[_]code_project` so this doc cannot
trip its own check.

## Consequence matrix

| Rule | Fail example | Gate it trips |
| --- | --- | --- |
| R1 | `from unittest.mock import patch` | `grep` mock scan |
| R2 | `import bond_api` in `toxicology.py` | mypy/import lock + review |
| R3 | gradient math inside a script | review + tests |
| R4 | literal `0.75` for sensitivity in prose | token cross-ref test |
| R5 | `time.time()` in a result | determinism review |
| R6 | the literal `template[_]code_project` appears in a doc | lineage `rg` |

## Pre-submit checklist

Run from the package root:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
```
