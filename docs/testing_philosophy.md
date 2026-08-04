# Testing Philosophy — no_time_to_die (HERACLES)

## Zero-mock policy

All tests use real algorithms and real data. No `unittest.mock`, `MagicMock`,
`@patch`, or `create_autospec`. A mock test can pass while the underlying
mathematics is wrong — it tests call signatures, not correctness. The enforced
gate is `uv run pytest tests/ --cov=src --cov-fail-under=90` (≥90% line+branch
on `src/`, set in `pyproject.toml`).

## What is tested

- **Domain primitives**: known values, analytic inverses, error branches
  (validation, degenerate cases, clamps) for every pure function.
- **Mission lifecycle**: `brief/recon/plan/execute/debrief` return protocol
  dataclasses; provenance carries the fixed seed, package version, and input
  hash. The full flow is driven through `bond_api.protocol.run_mission`.
- **Protocol integration**: `bond_api.discovery.load_provider` /
  `discover` and `GadgetRegistry` binding are exercised against the real film
  slug, proving the orchestrator can discover this package.
- **Manuscript hygiene**: a live cross-reference test scans `manuscript/[0-9]*.md`
  and fails if any `{{TOKEN}}` is not produced by `generate_variables()`;
  `resolve_manuscript_tree` is tested strict and non-strict.
- **Scripts**: subprocess smoke tests run the phase CLIs and the manuscript
  generator with `sys.executable`, asserting exit codes and artifacts.
- **Figures**: each renderer writes a non-empty PNG (to `tmp_path` or the
  redirected output dir).

## Determinism

Fixed inputs (`seed = 11`, canonical `demo.py`). Tests assert exact computed
values, never tolerances around random draws, and never wall-clock behavior
except the documented `GENERATION_TIMESTAMP` manuscript token.

## No-mock scan

```bash
grep -rn "unittest.mock\|MagicMock\|@patch\|create_autospec" tests/ || echo Clean
```
