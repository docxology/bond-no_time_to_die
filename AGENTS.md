# no_time_to_die (HERACLES) — AGENTS.md

Technical directives for the maintainer/build agent of this PROJECT BOND film
package: **No Time to Die (2021)**, mission codename **HERACLES**.

## Scope and hard constraints

- **Scope = this package directory only.** Never touch sibling bond packages,
  bond root files, or the template repo.
- Local-only working tree: no remote, never push. Path-scoped commits inside
  this repo only (`git add -A`).
- **No mock framework** anywhere in `tests/` — real data + computation.
- **≥90% line+branch coverage on `src/`:**
  `uv run pytest tests/ --cov=src --cov-fail-under=90`
- Deterministic, enforced structurally by `tests/test_determinism.py`: no module
  under `src/` may import `datetime`/`time`/`random`/`secrets`/`uuid`/`socket`/
  `tempfile`, and the only environment read in the package is
  `platform.python_version()` (the `PYTHON_VERSION` token). Two runs on one
  interpreter render byte-identical artifacts. `seed = 11` is recorded for
  provenance; nothing draws from an RNG, so it governs nothing today.
- Thin orchestrators in `scripts/`; business logic in `src/`.
- No leftover exemplar lineage strings (see verification).
- Type hints + docstrings; `ruff` + `mypy` clean on `src/` and `scripts/`.
- Manuscript metrics injected from `manuscript/config.yaml` +
  `src/no_time_to_die/manuscript_variables.py` — never hand-authored in prose.

## Layer contract

| Surface | Rule |
| --- | --- |
| `src/no_time_to_die/{bioweapon_counter,targeting_design,toxicology,antidote_screening,exposure_assessment,delivery_forensics,demo}.py` | Pure domain core — no bond-api, no infra, no logic-hiding I/O |
| `src/no_time_to_die/figures/plots.py` | Deterministic figure rendering to `output/figures/` |
| `src/no_time_to_die/mission.py` | Thin adapter — imports bond-api protocol + registry; implements `MissionProvider` |
| `src/no_time_to_die/manuscript_variables.py` | Token hydration from config + demo |
| `scripts/` | Thin CLIs: sys.path bootstrap + phase dispatch |

See `manuscript/layer_contract.yaml` for the machine-readable copy.

## Protocol integration (bond-api)

Frozen contract: `src/no_time_to_die/mission.py` must expose `MissionProvider`
(class name fixed by the discovery contract), a module-level `PROVIDER`, and a
populated `GADGET_REGISTRY`. Discovery by slug `no_time_to_die`. Do not invent
protocol types — use the `bond_api.protocol` dataclasses verbatim.

## Editing protocol

1. Read `docs/agent_instructions.md` before modifying any project file.
2. Read `docs/testing_philosophy.md` before writing/modifying tests.
3. Read `docs/architecture.md` before altering `scripts/` or `src/` boundaries.
4. If a bond dependency is not ready, build the pure core and note the
   integration point in `TODO.md` — do not stall.

## Verification before done

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**' \
  --glob '!output/**' || echo Clean
grep -rn "unittest.mock\|MagicMock\|@patch\|create_autospec" tests/ || echo Clean
git status --short   # clean after commit
```
