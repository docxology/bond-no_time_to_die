# Architecture — no_time_to_die (HERACLES)

## Layers and dependency direction

```
scripts/  (thin CLIs: brief/recon/plan/execute/debrief, z_generate_manuscript_variables)
   │  sys.path bootstrap + phase dispatch; no business logic
   ▼
src/no_time_to_die/  (the package)
   ├─ pure domain core: bioweapon_counter.py · targeting_design.py · toxicology.py
   │      · antidote_screening.py · exposure_assessment.py · delivery_forensics.py
   │     (bond-api-free, infra-free, no logic-hiding I/O)
   ├─ demo.py           canonical deterministic inputs + one shared run_demo() result
   ├─ mission.py        thin bond-api adapter — implements MissionProvider, registers gadgets
   ├─ manuscript_variables.py   reads manuscript/config.yaml + demo.py → tokens, writes output/
   └─ figures/plots.py  deterministic matplotlib renders → output/figures/
manuscript/  (config.yaml + prose sections + bibliography)
tests/       (zero-mock, real-data; enforces ≥90% coverage on src/)
```

The dependency arrow is one-directional: `scripts → src`; `mission.py → domain
core + bond-api`; `manuscript_variables → domain core + config`. Nothing
imports upward. The pure domain modules can be lifted into any Python
environment without bond-api or the pipeline installed.

## The domain modules, individually

| Module | Computes |
| --- | --- |
| `bioweapon_counter.py` | Hamming-window on/off-target counts over a reference genome, specificity, best-guide selection, the one-compartment bateman `plasma_concentration`, `fraction_delivered`, and the saturating `neutralization_probability`. Also owns `validate_sequence` / `DNA_ALPHABET`, which the other DNA modules reuse. |
| `targeting_design.py` | Sequence descriptors (`gc_content`, `longest_homopolymer`, `positional_bonus`), the Doench-style composite `guide_efficiency`, `population_off_target_risk` (exponential mismatch decay summed across a genome population), and `rank_guides` / `design_report`. |
| `toxicology.py` | Hill `fraction_affected` and its analytic inverse `dose_for_fraction`; the `PlantToxin` dataclass and 7-entry `TOXIN_CATALOG`; `catalog_stats` (count/min/max/median over any catalog); `combined_fraction_affected` (Bliss response addition) and `garden_risk_profile`. |
| `antidote_screening.py` | `cheng_prusoff_ic50`, Langmuir `fraction_antagonized` and its inverse, `therapeutic_window` / `margin_of_safety`, and `screen_antidotes` / `screen_report` ranking the 5-entry `ANTIDOTE_LIBRARY` by restored survival. |
| `exposure_assessment.py` | `absorbed_dose` (pathway intake), `cumulative_exposure` (body burden under first-order elimination), `margin_of_exposure`, `risk_quotient`, and the composed `exposure_scenario_report` verdict. |
| `delivery_forensics.py` | `signal_to_noise`, logistic `detection_confidence` vs the LOD, `estimate_concentration` from a linear calibration, `recovered_dose`, `cosine_similarity` / `match_unknown` against the 5-entry `SPECTRUM_LIBRARY`, and the composed `vesper_trace_report`. |

`bioweapon_counter` is the only module the others depend on
(`targeting_design` imports its validators); everything else is a sibling.

## How the pieces compose

`demo.py` is the single composition point. It holds every demonstration
constant (`DEMO_REFERENCE`, `DEMO_CANDIDATES`, `EXPOSURE_SCENARIO`,
`FORENSIC_SCENARIO`, the delivery-plot parameters) and one `run_demo()` that
calls each domain module exactly once, returning a typed `DemoResult`.

Three consumers read that one result, which is what makes drift impossible:

1. `mission.py::execute` puts it in a `MissionOutcome`.
2. `manuscript_variables.py::generate_variables` turns it into `{{TOKEN}}`s.
3. `figures/plots.py` reads the same constants for its curves and annotations.

`demo.DOMAIN_MODULES` is likewise the single source of truth for *which*
modules exist: `mission.register_gadgets` registers exactly that mapping, and
the manuscript's module-count token is `len()` of it.

## How `mission.py` implements the frozen `bond_api` MissionProvider

`bond-api` is Layer 1 of the suite and its protocol is **frozen** — `bond-cli`,
the coordinator's reconcile pass, and the orchestrator consume the same five
method names across all film packages. Discovery works by slug: the
orchestrator puts this package's `src/` on `sys.path`, imports
`no_time_to_die.mission`, and expects three names:

| Name | Kind | Why it must not move |
| --- | --- | --- |
| `MissionProvider` | class | `bond_api.discovery.load_provider` looks it up by this exact name |
| `PROVIDER` | module-level instance | coordinators bind to it without constructing |
| `GADGET_REGISTRY` | populated `GadgetRegistry` | gadget lookup across packages; filled at import by `register_gadgets()` |

The adapter is deliberately thin — it contains no mathematics. Each phase maps
domain output onto a frozen `bond_api.protocol` dataclass:

- **`brief()` → `MissionBrief`**: declares one objective string and one `Asset`
  per domain module, plus `Constraint`s asserting determinism and
  frozen-protocol-types-only.
- **`recon(request) → ReconReport`**: `Finding`s echoing the request goal, the
  catalog size, and the determinism requirement. Read-only; no computation.
- **`plan(brief) → MissionPlan`**: one `Step` per domain concept
  (countermeasure, targeting, toxicology, antidote, exposure, forensics), each
  carrying its parameters, ordered by evidence dependency.
- **`execute(plan) → MissionOutcome`**: the only phase that computes. It calls
  `demo.run_demo()` and packs the result plus a `Provenance` record carrying
  the package version, `DEMO_SEED`, and `demo.input_hash()`. `wall_time_s` is
  pinned to `0.0` — a real clock reading would break byte-reproducibility of
  persisted outcomes.
- **`debrief(outcome) → Debrief`**: wraps the outcome with the standing
  lessons. No recomputation.

Only this file imports `bond_api`. If bond-api were removed, every domain
module and the manuscript pipeline would still import and run; only
`mission.py` and `scripts/run_mission.py` would fail. That is the intended
blast radius.

## Forbidden patterns

- Importing `bond_api` from any domain module or from `demo.py`.
- Any `infrastructure.*` import anywhere in this standalone tree.
- Business logic (math, evidence) in `scripts/`.
- Hardcoded metrics in `manuscript/*.md`.
- Changing the public shape of `MissionProvider` / `PROVIDER` /
  `GADGET_REGISTRY` — that breaks cross-package discovery.
- Duplicating a demonstration constant instead of reading it from `demo.py`.

## How to add a concept module

1. Add `src/no_time_to_die/<name>.py` as a pure module with typed functions and
   docstrings; keep it bond-api-free.
2. Add its constants and its call to `src/no_time_to_die/demo.py`, extend the
   `DemoResult` TypedDict, and register it in `DOMAIN_MODULES` so both the
   gadget registry and the module-count token pick it up automatically.
3. Add `tests/test_<name>.py` covering normal, boundary, and error branches.
4. Add the keys your tokens will read to
   `manuscript_variables.REQUIRED_DEMO_KEYS` so the completeness gate covers
   them, then add the `HERACLES_*` tokens and reference them in a prose
   section; the live cross-reference test enforces completeness.
5. Add a `Step` in `mission.plan` and an objective/`Asset` in `mission.brief`.
   Do **not** change the method signatures.
6. Optionally add a figure generator in `figures/plots.py`, reading its
   parameters from `demo.py`.
7. Gate: `pytest --cov=src --cov-fail-under=90`, ruff, mypy.
