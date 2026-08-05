# no_time_to_die — HERACLES · Special-Agent Mission Software

Film package for **No Time to Die** (2021) in the PROJECT BOND suite, mission
codename **HERACLES**. A deterministic, fully-tested Python package that models
the pharmaco-forensic concepts of the film as real mathematics with a
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

This surface is **frozen**: `bond-cli`, the coordinator's reconcile pass, and
the orchestrator all consume `brief` / `recon` / `plan` / `execute` / `debrief`
plus the gadget registry across every film package. Deepen inside the package;
never change these names or signatures. See
[`docs/architecture.md`](docs/architecture.md) for the phase-by-phase mapping.

The `MissionProvider` phases return frozen `bond_api.protocol` dataclasses:

| Phase | Returns | Content |
| --- | --- | --- |
| `brief()` | `MissionBrief` | one objective and one `Asset` per domain module, plus determinism/protocol `Constraint`s |
| `recon(request)` | `ReconReport` | `Finding`s for the goal, the catalog size, and the determinism requirement |
| `plan(brief)` | `MissionPlan` | one `Step` per domain concept, ordered by evidence dependency |
| `execute(plan)` | `MissionOutcome` | the full `demo.run_demo()` result plus a `Provenance` record (version, seed, input hash) |
| `debrief(outcome)` | `Debrief` | the outcome plus the standing HERACLES lessons |

## Guardrails

Local-only working tree (never push, no remote). ≥90% line+branch coverage on
`src/` enforced by `pyproject.toml` (the gate is authoritative — this README
deliberately does not quote a coverage figure that would go stale); zero mocks;
thin scripts; full type hints; `ruff` + `mypy` clean. `output/` is git-ignored
(regenerable).

Determinism is a structural property, not a promise: no module under `src/`
imports a clock or a random-number generator, the package makes exactly one
environment read (`platform.python_version()`, the single host-dependent
token), and `tests/test_determinism.py` fails the build on a violation of
either — with positive controls proving those scans report a reintroduced
`datetime` or `random` import rather than passing quietly. Two runs on one
interpreter render byte-identical artifacts.

## See also

- [`AGENTS.md`](AGENTS.md) — technical directives for this package.
- [`TODO.md`](TODO.md) — open work (grouped correctness / verification /
  documentation / extension), accepted limitations, and the gate commands.
- [`docs/`](docs/) — the agent-facing rulebook:
  [`agent_instructions.md`](docs/agent_instructions.md) (rules R1–R6),
  [`architecture.md`](docs/architecture.md) (layer contract + protocol
  mapping), [`testing_philosophy.md`](docs/testing_philosophy.md) (zero-mock
  doctrine).
- [`manuscript/`](manuscript/) — prose + config.
- [`data/claim_ledger.yaml`](data/claim_ledger.yaml) — every numeric constant
  the demonstration consumes, each marked `synthetic: true` (invented here) or
  `synthetic: false` (a commonly-cited order-of-magnitude figure carried without
  a specific citation). Nothing in the package is a measurement. The registry is
  bound to the code by `tests/test_claim_ledger.py`, which derives the expected
  constant set from the modules themselves and fails on an unregistered
  constant, an orphaned entry, or a value edited on one side only.
- `bond-api` / `bond-orchestrator` / `bond-utilities` — the BOND suite Layer
  1/3/0 building blocks this film binds to.
