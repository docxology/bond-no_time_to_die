# no_time_to_die — HERACLES · Special-Agent Mission Software

Film package for **No Time to Die** (2021) in the PROJECT BOND suite, mission
codename **HERACLES**. A deterministic, fully-tested Python package that models
three pharmaco-forensic concepts from the film as real mathematics with a
shared provenance ledger.

## Concepts

| Module | Concept | What it computes |
| --- | --- | --- |
| `src/no_time_to_die/bioweapon_counter.py` | DNA-targeted bioweapon countermeasure (Heracles) | guide target specificity, off-target risk, one-compartment delivery kinetics, neutralization probability |
| `src/no_time_to_die/targeting_design.py` | Guide design & population off-target | GC/homopolymer descriptors, Doench-style efficiency, population off-target aggregation, guide ranking |
| `src/no_time_to_die/toxicology.py` | Poison-garden toxicology (Safin's island flora) | Hill dose–response, LD50 catalog, response-addition mixtures |
| `src/no_time_to_die/antidote_screening.py` | Competitive-antagonist pharmacology | Cheng–Prusoff IC50, Langmuir occupancy, antidote-library survival ranking |
| `src/no_time_to_die/exposure_assessment.py` | Exposure pathway & risk assessment | absorbed dose, cumulative body burden, margin of exposure, risk quotient |
| `src/no_time_to_die/delivery_forensics.py` | Poison delivery forensics (Vespers) | signal-to-noise, detection confidence vs LOD, concentration recovery, spectral matching |

The domain core is pure and importable **without** bond-api; a thin adapter
(`src/no_time_to_die/mission.py`) implements the frozen
`bond_api.MissionProvider` protocol so the orchestrator discovers and drives
this film by slug through bond-api discovery/registry.

## Layout

```
src/no_time_to_die/        pure domain core + mission adapter + token hydration
  bioweapon_counter.py     DNA-targeted countermeasure model
  targeting_design.py      guide design & population off-target aggregation
  toxicology.py            poison-garden dose-response catalog
  antidote_screening.py    competitive-antagonist antidote screening
  exposure_assessment.py   exposure pathway & risk assessment
  delivery_forensics.py    vesper trace-detection forensics
  demo.py                  canonical deterministic demonstration (shared inputs)
  mission.py               MissionProvider adapter (bond-api)
  manuscript_variables.py  {{TOKEN}} hydration from manuscript/config.yaml
  figures/plots.py         deterministic figure rendering
scripts/                   thin per-phase CLIs (brief/recon/plan/execute/debrief)
manuscript/                prose sections + config + bibliography
tests/                     zero-mock real-data suite
```

## Quick start

```bash
cd projects/working/bond/no_time_to_die
uv sync --extra dev

# Run the full deterministic mission flow
uv run python scripts/run_mission.py all          # or: brief|recon|plan|execute|debrief

# Hydrate manuscript tokens + render figures
uv run python scripts/z_generate_manuscript_variables.py

# Gates
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
```

## Protocol integration

- Local path dependency on `bond-api` (the FROZEN mission protocol) declared in
  `pyproject.toml` under `[tool.uv.sources]`.
- `src/no_time_to_die/mission.py` exposes `MissionProvider` (class) plus a
  module-level `PROVIDER` instance and a populated `GADGET_REGISTRY`
  (`register_gadgets()`).
- Discovery contract: slug `no_time_to_die` → `no_time_to_die.mission`.

## Guardrails

Local-only working tree (never push, no remote). ≥90% line+branch coverage on
`src/` enforced by `pyproject.toml`; zero mocks; deterministic computation
(fixed `seed = 11`, no wall-clock in persisted artifacts); thin scripts; full
type hints; `ruff` + `mypy` clean. `output/` is git-ignored (regenerable).

## See also

- [`AGENTS.md`](AGENTS.md) — technical directives for this package.
- [`TODO.md`](TODO.md) — what was built and declared integration points.
- [`manuscript/`](manuscript/) — prose + config.
- `bond-api` / `bond-orchestrator` / `bond-utilities` — the BOND suite Layer
  1/3/0 building blocks this film binds to.
