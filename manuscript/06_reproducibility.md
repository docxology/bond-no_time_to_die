# Reproducibility

This package treats reproducibility as a hard constraint enforced by tests,
not a prose promise. The guarantees are:

## Deterministic computation

The domain core makes no random draws and performs no wall-clock reads. All
demonstration inputs are fixed  constants in `src/no_time_to_die/demo.py` and
`manuscript/config.yaml`; `seed = 11` is stable. The mission outcome carries a
`Provenance` record with the package version, the seed, and a sha256
`input_hash` of the canonical inputs (`demo.input_hash()`) so any outcome can
be audited without re-execution.

## Live manuscript metrics

Every numeric value in the prose sections flows through a resolved `HERACLES_*` token from `src/no_time_to_die/manuscript_variables.py`, computed from the shared demo result;
none are hand-authored. The token cross-reference test fails if any section token
is undefined, and `z_generate_manuscript_variables.py` fails in strict mode on
any unresolved token.

## Verification commands

From the package root:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
# Lineage gate — pattern is bracket-split so this doc cannot trip its own
# check (template[_]code_project resolves to the literal string when run).
rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**' \
  --glob '!output/**' || echo Clean
git diff --exit-code   # clean tree after regeneration
```

The suite enforces ≥90% line+branch coverage on `src/`, zero mocks, and a
clean tree after deterministic regeneration (a live byte-equality proof).
Generated at {{GENERATION_TIMESTAMP}} (UTC) under Python {{PYTHON_VERSION}}.
