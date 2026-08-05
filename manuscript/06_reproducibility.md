# Reproducibility

This package treats reproducibility as a hard constraint enforced by tests, not
a prose promise. Every guarantee below names the test that would fail if it
stopped holding.

## Deterministic computation

No module under `src/` imports a clock, a random-number generator, or any other
entropy source, and the package makes exactly one environment read in total —
`platform.python_version()`, rendered as the `PYTHON_VERSION` token. That is a
structural property, checked structurally: `tests/test_determinism.py` parses
every source file and fails on a forbidden import or an unsanctioned
environment read, and its positive controls confirm the scan reports a
reintroduced `datetime` or `random` import rather than passing silently.

Two consequences, stated precisely:

- **On one interpreter, two runs render byte-identical artifacts.** The byte
  gate renders the whole manuscript tree twice and compares every file byte for
  byte.
- **Across interpreter versions, exactly one substring differs** — the
  `PYTHON_VERSION` token. This is the single host-dependent value in the
  package; nothing else varies with the machine.

Through 2026-08-04 this section claimed byte-reproducibility while the
generator stamped `datetime.now(timezone.utc)` into both
`output/data/manuscript_variables.json` and this rendered section, so
consecutive runs demonstrably differed. The token was removed rather than
reworded, and the value gate now fails on any rendered token shaped like a date
or a clock time.

All demonstration inputs are fixed constants in `src/no_time_to_die/demo.py` and
`manuscript/config.yaml`; seed `{{HERACLES_SEED}}` is stable, though no code
path draws from an RNG, so it currently governs nothing and is recorded for
provenance only. The mission outcome carries a `Provenance` record with the
package version, the seed, and a sha256 `input_hash` over the canonical inputs
(`demo.input_hash()`, currently `{{HERACLES_INPUT_HASH}}…`). That digest covers
every demonstration constant — an earlier version hashed only five of sixteen —
and the suite scans `demo.py` independently to fail if a newly added constant is
left out of it.

Figure renderers read the same `demo.py` constants as the mission and the
tokens. This is enforced, not asserted: each figure is composed by a
`build_*_figure()` function the tests inspect directly, checking the plotted
series and the annotation positions against the constants the captions quote.
Five of the seven figure tests previously asserted only that a PNG was
non-empty, which a blank or wrong-data figure passes.

## Live manuscript metrics

Every numeric value in the prose sections flows through a resolved `HERACLES_*`
token from `src/no_time_to_die/manuscript_variables.py`, computed from the
shared demo result; none are hand-authored. Three gates protect this:

1. `check_demo_completeness` fails if the demo result is missing any key the
   tokens read — including the top-level `garden_risk_combined`, which the
   section-keyed scan was structurally blind to until 2026-08-05 (deleting it
   passed the gate and then raised a bare `KeyError`). The suite's positive
   control now deletes *every* key of a real demo result in turn and requires
   each deletion to surface as a named gate failure rather than as any other
   exception.
2. The token cross-reference test scans `manuscript/[0-9]*.md` and fails if any
   `{{`-delimited token is not produced by `generate_variables()`.
3. `z_generate_manuscript_variables.py` fails in strict mode on any token left
   unresolved after substitution.

## Evidence provenance

`data/claim_ledger.yaml` registers every numeric constant the demonstration
consumes, with its live value and one of two provenance classes: `synthetic:
true` (invented for this demonstration) or `synthetic: false` (a commonly-cited
order-of-magnitude figure for a real substance, recorded without a specific
citation). `tests/test_claim_ledger.py` derives the expected constant set from
the modules themselves, so an unregistered constant, an orphaned entry, or a
value edited on one side only all fail the build. Nothing here is a
measurement.

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

The suite enforces ≥90% line+branch coverage on `src/` and zero mocks. Rendered
under Python {{PYTHON_VERSION}}.
