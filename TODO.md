# no_time_to_die (HERACLES) — TODO

Forward-only backlog for the HERACLES film package (No Time to Die, 2021).

## Built (phase-2 conversion + phase-4 deepening complete)

- **Pure domain core** (`src/no_time_to_die/`, bond-api-free):
  - `bioweapon_counter.py` — DNA-targeted countermeasure: Hamming-window
    specificity, off-target risk, one-compartment bateman delivery kinetics,
    saturating neutralization probability.
  - `targeting_design.py` — guide design & population off-target: GC/homopolymer
    descriptors, Doench-style efficiency, exponential-decay population
    off-target aggregation, deterministic guide ranking.
  - `toxicology.py` — poison-garden Hill dose–response, 7-entry LD50 flora
    catalog, response-addition mixtures.
  - `antidote_screening.py` — competitive-antagonist pharmacology: Cheng–Prusoff
    IC50, Langmuir occupancy, 5-antidote survival ranking.
  - `exposure_assessment.py` — exposure pathway & risk: absorbed dose,
    cumulative body burden, margin of exposure, risk quotient, verdict.
  - `delivery_forensics.py` — vesper trace detection: SNR, logistic detection
    confidence vs LOD, concentration recovery, cosine spectral matching.
  - `demo.py` — canonical deterministic demonstration shared by mission and
    manuscript variables (single source of truth for inputs/results).
- **Protocol adapter**: `mission.py` implements the frozen `bond_api`
  `MissionProvider` (brief/recon/plan/execute/debrief), exposes `PROVIDER` and
  `GADGET_REGISTRY`, and registers all six domain modules as gadgets from the
  single `demo.DOMAIN_MODULES` source of truth.
- **scripts/**: `run_mission.py` (phase dispatcher) + thin `brief/recon/plan/
  execute/debrief.py` wrappers; `z_generate_manuscript_variables.py`.
- **manuscript/**: config.yaml (HERACLES identity) + prose sections with live
  `{{TOKEN}}`s; `manuscript_variables.py` hydrates them.
- **figures/**: five deterministic concept figures to `output/figures/`
  (delivery kinetics, toxicology dose-response, guide efficiency, antidote
  response, detection confidence), each reading the shared `demo.py` constants.
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

## Phase-5 hardening (done)

- Removed unfalsifiable code: the unreachable zero-length `weights` guard in
  `positional_bonus`, the `assert best_guide is not None` in
  `select_best_guide`, five `assert isinstance` narrowings in `mission.execute`,
  eight `isinstance` re-narrowings in `generate_variables`, and the dead `int`
  branch in `_fmt`. `demo.run_demo()` now returns a `DemoResult` TypedDict, so
  the narrowing is unnecessary rather than merely deleted.
- Replaced the unfalsifiable `require_outputs` check (a `not cm` test on a dict
  that is never empty) with `check_demo_completeness`, which enumerates every
  key the tokens read and is positive-controlled key-by-key in the suite.
- Fixed two test defects: a tautological `FIGURES_DIR` assertion, and a
  `plots.FIGURES_DIR` mutation that leaked a torn-down `tmp_path` into later
  tests.
- Fixed a figure/data contradiction: the delivery-kinetics plot marked a 2.0 h
  "exposure window" against a 4.0 h `DEMO_EXPOSURE_TIME`, and duplicated the
  absorption rate as a literal. Both now read `demo.py`.
- Manuscript: the abstract claimed three modules (there are six); the abstract
  and methodology reported the catalog LD50 range as min→**median**, understating
  the true max; the experimental-setup table hand-authored every `demo.py`
  constant; `07_scope_and_related_work.md` contained a garbled clause. All
  corrected, with ~30 new tokens so the setup table and results prose are live.

## Next candidate work

- Extend the forensic library with more poison signatures and a mixture-match
  ranking test (currently `match_unknown` ranks single spectra only).
- `match_unknown` requires the unknown spectrum to be length-compatible with
  *every* library entry; a heterogeneous-length library would raise rather than
  rank the compatible subset. Decide whether that is the desired contract and
  either document it as invariant or relax it.
- Wire bond-utilities provenance once the dependency's phase-1 is converted
  (see Declared integration points).
- `therapeutic_window` / `margin_of_safety` in `antidote_screening.py` are
  tested but not consumed by `screen_report`, the mission, or any token —
  either surface them in the screen result or drop them.

## Gates

Coverage, test count, and lint status are **not** quoted here by design: run
the gates and read their output. They are the source of truth, and a number
copied into this file would be stale by the next commit.

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
grep -rn "unittest.mock\|MagicMock\|@patch\|create_autospec" tests/ || echo Clean
git status --short
```
