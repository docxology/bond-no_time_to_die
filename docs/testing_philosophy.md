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
  `resolve_manuscript_tree` is tested strict and non-strict; and
  `check_demo_completeness` is tested against real demo results with keys
  deliberately removed.
- **Scripts**: subprocess smoke tests run the phase CLIs and the manuscript
  generator with `sys.executable`, asserting exit codes and artifacts.
- **Figures**: each renderer writes a non-empty PNG (to `tmp_path` or the
  redirected output dir), and the redirect is restored afterwards.

## A gate must be able to fail

Coverage alone does not prove a test is doing work. Two rules follow:

1. **No unfalsifiable assertions.** An assertion whose predicate is true by
   construction (`FIGURES_DIR.parents[0].name == "output"` on a path literally
   built as `.../output/figures`) reports green forever. State the real
   invariant instead, and make sure it could fail.
2. **Positive-control the gates.** For any check that enumerates required
   things, prove each entry is load-bearing:
   `test_every_required_key_is_individually_load_bearing` deletes each key in
   `REQUIRED_DEMO_KEYS` in turn and asserts the gate raises for that specific
   key. A key that could be deleted without a failure is not being checked.

The same reasoning motivated removing two defensive branches from `src/`
(a zero-length `weights` guard behind a length equality check, and a set of
`isinstance` re-narrowings of an already-typed result): a branch no input can
reach is not defence, it is untestable dead weight.

## Test isolation

Tests that mutate module-level state (only `plots.FIGURES_DIR`) must restore it
in a `finally` block. A leaked redirect to a torn-down `tmp_path` makes later
tests order-dependent — passing or failing based on collection order rather
than on the code.

## Determinism

Fixed inputs (canonical constants in `demo.py`, including `DEMO_SEED`). Tests
assert exact computed values against hand-checkable expectations — e.g. the
even-median case uses ricin (LD50 1.0) and atropine (LD50 10.0) so the expected
5.5 can be verified by eye rather than by re-implementing the function under
test. Never tolerances around random draws, and never wall-clock behavior at
all — `tests/test_determinism.py` fails the build if any module under `src/`
imports a clock or an RNG. The former `GENERATION_TIMESTAMP` carve-out was
removed on 2026-08-05: it made the byte-reproducibility claim false while a
test asserted only that the token *existed*.

Demonstration inputs must not force their own results. `test_demo_evidence.py`
fails if the reference genome degenerates back into a shape where specificity,
off-target count, or the composite blend can only take one value — a result an
input makes inevitable is not evidence.

## No-mock scan

```bash
grep -rn "unittest.mock\|MagicMock\|@patch\|create_autospec" tests/ || echo Clean
```
