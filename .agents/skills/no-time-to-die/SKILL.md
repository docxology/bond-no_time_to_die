---
name: no-time-to-die
description: PROJECT BOND film package (No Time to Die, 2021) — HERACLES mission. DNA-targeted bioweapon countermeasure, poison-garden toxicology, poison-delivery forensics; bond-api MissionProvider.
version: 1.0.0
author: PROJECT BOND
license: MIT
tags: [bond, film, pharmaco-forensics, bond-api, thin-orchestrator]
---

# no-time-to-die

Project-scoped skill for the BOND film package at the root of this repository.
Load this when working inside the project.

## When to Use

- Working inside the HERACLES package — running mission phases, editing source,
  or regenerating figures/manuscript variables.
- Implementing or verifying the `bond_api.MissionProvider` adapter and the
  frozen protocol integration.

## Quick Reference

```bash
cd "$(git rev-parse --show-toplevel)"
uv sync --extra dev
uv run python scripts/run_mission.py all   # brief|recon|plan|execute|debrief|all
uv run python scripts/z_generate_manuscript_variables.py
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
```

## Pitfalls

- **Keep scripts thin.** Business logic lives in `src/no_time_to_die/`, not in
  `scripts/`.
- **Domain purity.** The pure modules (`bioweapon_counter`, `toxicology`,
  `delivery_forensics`, `demo`) must not import bond-api; only
  `mission.py` adapts.
- **No mocks.** Tests use real data + real computation; deterministic fakes
  implement the REAL protocol.
- **Live metrics.** Every manuscript number is a `{{TOKEN}}` from
  `manuscript_variables.py`; never hardcode in prose.
- **No clock, no RNG.** Nothing under `src/` may import `datetime`, `time`,
  `random`, `secrets`, `uuid`, `socket`, or `tempfile`;
  `platform.python_version()` is the only sanctioned environment read.
  `tests/test_determinism.py` enforces this structurally.
- **Register every constant.** A new numeric constant in a domain module needs a
  `data/claim_ledger.yaml` entry in the same commit, or
  `tests/test_claim_ledger.py` fails. Mark it `synthetic: true` unless it is a
  commonly-cited figure for a real substance — and nothing here is a measurement.
- **Demonstration inputs must not force their results.** The reference genome
  plants a documented structure precisely so specificity and off-target risk are
  measured rather than assumed; `tests/test_demo_evidence.py` fails if the
  demonstration degenerates.
- **Outputs are disposable.** Regenerate `output/` (git-ignored); never hand-edit.
- **Published tree.** `origin` is the GitHub repository; changes land through an
  ordinary branch, pull request and merge.

## Cross-refs

- Project contract: [`AGENTS.md`](../../../AGENTS.md)
- README: [`README.md`](../../../README.md)
- TODO: [`TODO.md`](../../../TODO.md)
