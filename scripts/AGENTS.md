# scripts/ — the phase CLIs and the manuscript generator

`run_mission.py` plus the five per-phase wrappers `brief.py`, `recon.py`, `plan.py`, `execute.py`,
`debrief.py`, and `z_generate_manuscript_variables.py`.

## Rules

- **Thin wrappers only.** Each script bootstraps `sys.path` and forwards to `src/no_time_to_die/`.
  The engines live in the package; no phase logic belongs here.
- **`execute.py` runs the mission and persists a provenance record.** It is the one wrapper that does
  more than dispatch, and the record it writes is the evidence that the run happened.
- **Exit code 0 iff the phase succeeded.** Report the code; never describe a failed phase as done.
- **`z_generate_manuscript_variables.py` hydrates tokens and renders figures.** It writes into
  `output/`. Never hand-author into prose a value a generated token should carry.
- **`output/` is regenerable and git-ignored.** Never hand-edit anything under it.
- **Scope is this package directory.** Do not write to sibling bond packages, the bond root, or the
  template repository.
- **`mission.py` and `run_mission.py` need `bond-api`** (the frozen protocol), resolved from the
  recorded copy at `vendor/bond-api`; the pure core and its own tests do not.
- `ruff` and `mypy` are clean on this directory, as they are on `src/`.
