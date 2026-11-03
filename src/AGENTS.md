# src/ — the pure domain core, one figures module and one adapter

`src/no_time_to_die/`, the installable package. Everything below is either pure computation or a
single boundary crossing.

## Layout

| Module | What it does |
| --- | --- |
| `bioweapon_counter.py` | Countermeasure accounting for the DNA-targeted agent |
| `targeting_design.py` | The targeting design and its constraints |
| `toxicology.py` | Poison-garden toxicology |
| `antidote_screening.py` | Antidote screening against the agent |
| `exposure_assessment.py` | Exposure assessment |
| `delivery_forensics.py` | Poison-delivery forensics |
| `demo.py` | Demo inputs the token layer and tests build on |
| `figures/plots.py` | Deterministic figure rendering into `output/figures/` |
| `mission.py` | The **only** module that imports `bond_api`; implements `MissionProvider` |
| `manuscript_variables.py` | Token hydration from `manuscript/config.yaml` + the demo |

## Rules

- **Business logic lives here; orchestration lives in `scripts/`.** A phase CLI that computes
  something is misplaced.
- **The pure modules take no dependency on `bond-api`, infrastructure, or hidden I/O.** That is what
  keeps `mission.py` a thin adapter and lets the core be tested alone.
- **Determinism is structural, not aspirational.** No module under `src/` may import
  `datetime`, `time`, `random`, `secrets`, `uuid`, `socket` or `tempfile`, and the only environment
  read in the package is `platform.python_version()` (the `PYTHON_VERSION` token). Two runs on one
  interpreter render byte-identical artifacts. `tests/test_determinism.py` enforces this by reading
  the sources, so a new import fails the gate rather than going unnoticed.
- **Protocol types come from `bond_api.protocol` verbatim.** Do not invent a look-alike dataclass in
  `mission.py`.
- **Manuscript metrics are injected, never typed twice.** They come from `manuscript/config.yaml`
  through `manuscript_variables.py`; hand-authored prose figures are a defect.
- **Type hints and docstrings throughout**; `ruff` and `mypy` are clean here.
