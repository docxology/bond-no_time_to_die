# Architecture — no_time_to_die (HERACLES)

## Layers and dependency direction

```
scripts/  (thin CLIs: brief/recon/plan/execute/debrief, z_generate_manuscript_variables)
   │  sys.path bootstrap + phase dispatch; no business logic
   ▼
src/no_time_to_die/  (the package)
   ├─ pure domain core: bioweapon_counter.py · toxicology.py · delivery_forensics.py · demo.py
   │     (bond-api-free, infra-free, no logic-hiding I/O)
   ├─ mission.py         thin bond-api adapter — implements MissionProvider, registers gadgets
   ├─ manuscript_variables.py   reads manuscript/config.yaml + demo.py → tokens, writes output/
   └─ figures/plots.py   deterministic matplotlib renders → output/figures/
manuscript/  (config.yaml + prose sections + bibliography)
tests/       (zero-mock, real-data; enforces ≥90% coverage on src/)
```

The dependency arrow is one-directional: `scripts → src`; `mission.py → domain
core + bond-api`; `manuscript_variables → domain core + config`. Nothing
imports upward. The pure domain modules can be lifted into any Python
environment without bond-api or the pipeline installed.

## Forbidden patterns

- Importing `bond_api` from `bioweapon_counter.py` / `toxicology.py` /
  `delivery_forensics.py` / `demo.py`.
- Any `infrastructure.*` import anywhere in this standalone tree.
- Business logic (math, evidence) in `scripts/`.
- Hardcoded metrics in `manuscript/*.md`.

## How to add a concept module

1. Add `src/no_time_to_die/<name>.py` as a pure module with typed functions and
   docstrings; keep it bond-api-free.
2. Wire deterministic demonstration inputs + outputs through `src/no_time_to_die/demo.py`
   so both `mission.py` and `manuscript_variables.py` consume the same result.
3. Add `tests/test_<name>.py` covering normal, boundary, and error branches.
4. Register the module as a gadget in `mission.py::register_gadgets`.
5. Add a `HERACLES_*` token in `manuscript_variables.py` and reference it in a
   prose section; the live cross-reference test enforces completeness.
6. Optionally add a figure generator in `figures/plots.py`.
7. Gate: `pytest --cov=src --cov-fail-under=90`, ruff, mypy.
