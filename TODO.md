# no_time_to_die (HERACLES) — TODO

Forward-only backlog for the HERACLES film package (No Time to Die, 2021).

## Built (phase-2 conversion complete)

- **Pure domain core** (`src/no_time_to_die/`, bond-api-free):
  - `bioweapon_counter.py` — DNA-targeted countermeasure: Hamming-window
    specificity, off-target risk, one-compartment bateman delivery kinetics,
    saturating neutralization probability.
  - `toxicology.py` — poison-garden Hill dose–response, 7-entry LD50 flora
    catalog, response-addition mixtures.
  - `delivery_forensics.py` — vesper trace detection: SNR, logistic detection
    confidence vs LOD, concentration recovery, cosine spectral matching.
  - `demo.py` — canonical deterministic demonstration shared by mission and
    manuscript variables (single source of truth for inputs/results).
- **Protocol adapter**: `mission.py` implements the frozen `bond_api`
  `MissionProvider` (brief/recon/plan/execute/debrief), exposes `PROVIDER` and
  `GADGET_REGISTRY`, registers three domain gadgets.
- **scripts/**: `run_mission.py` (phase dispatcher) + thin `brief/recon/plan/
  execute/debrief.py` wrappers; `z_generate_manuscript_variables.py`.
- **manuscript/**: config.yaml (HERACLES identity) + prose sections with live
  `{{TOKEN}}`s; `manuscript_variables.py` hydrates them.
- **figures/**: three deterministic concept figures to `output/figures/`.
- **tests/**: zero-mock suite — domain modules, mission lifecycle, discovery,
  gadgets, manuscript token cross-reference (live gate), script smoke.

## Declared integration points

- **bond-api** — consumed via local path dependency (`pyproject.toml`
  `[tool.uv.sources]`). Mission discovery assumption: the orchestrator adds
  this package's `src/` to `sys.path` and discovers slug `no_time_to_die`.
- **bond-utilities `mission_io.record_provenance_outcome`** — not yet bound.
  Acceptance: when bond-utilities ships, persist each `MissionOutcome`
  provenance via `mission_io` in `scripts/execute.py` (outcome already carries
  package_version/seed/input_hash/wall_time_s for a clean bind).

## Next candidate work

- Add a bateman delivery visualization with configurable parameter overlay.
- Extend the forensic library with more poison signatures and a mixture-match
  ranking test.
- Wire bond-utilities provenance once the dependency's phase-1 is converted.

## Gates (measured)

- `pytest tests/ --cov=src --cov-fail-under=90` — passing; coverage is live,
  not hardcoded here (drift guard).
- ruff check + format, mypy, lineage `rg`, zero mocks, `git status` clean.
