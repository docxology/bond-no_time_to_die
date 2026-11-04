# tests/ — the gate: real data and computation, no mock framework

`conftest.py` and fifteen `test_*.py` modules, one per domain module plus the cross-cutting checks.

## What each part holds

| Test module | Subject |
| --- | --- |
| `test_bioweapon_counter.py`, `test_targeting_design.py`, `test_toxicology.py` | The three core domain modules |
| `test_antidote_screening.py`, `test_exposure_assessment.py`, `test_delivery_forensics.py` | The assessment modules |
| `test_demo_evidence.py` | The demo inputs the rest build on |
| `test_manuscript_variables.py`, `test_figures.py` | Token hydration and figure rendering |
| `test_determinism.py` | The structural determinism rule (reads the sources, not a run) |
| `test_architecture.py` | The layer contract between `src/` and `scripts/` |
| `test_claim_ledger.py` | The repository's own claims against the files |
| `test_scripts_smoke.py` | Each phase CLI still runs |
| `test_mission.py` | The `bond_api` protocol adapter — the integration surface |

## Rules

- **No mock framework anywhere.** No `unittest.mock`, `MagicMock`, `@patch` or `create_autospec`:
  real data and real computation, or the check is not evidence.
- **The gate is `uv run pytest tests/ --cov=src --cov-fail-under=90`** — 90% floor, line and branch.
- **`test_determinism.py` enforces the rule by reading sources.** A new `datetime`, `random` or
  `tempfile` import under `src/` fails here; do not weaken it to accommodate a module.
- **`test_architecture.py` holds the boundary.** New code that puts computation in `scripts/` or
  I/O in the pure core fails this, by design.
- **`test_mission.py` is the one module that needs `bond-api`** (resolved from the recorded copy at
  `vendor/bond-api`). It exercises the frozen protocol; it is not a unit test of the pure core.
- **If the suite cannot import `bond_api` under `uv run pytest`,** run it as
  `uv run python -m pytest`: a stale console script left in `.venv/bin` by an earlier interpreter
  outlives that interpreter and runs a different library set. Gate through the interpreter.
- `pytest` is configured in `pyproject.toml` (`pythonpath = [".", "src"]`, `testpaths = ["tests"]`,
  `--strict-markers`), so no marker may be used that is not declared.
