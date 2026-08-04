---
name: no-time-to-die
description: PROJECT BOND film package (No Time to Die, 2021) — HERACLES mission. DNA-targeted bioweapon countermeasure, poison-garden toxicology, poison-delivery forensics; bond-api MissionProvider.
version: 1.0.0
author: PROJECT BOND
license: MIT
tags: [bond, film, pharmaco-forensics, bond-api, thin-orchestrator]
---

# no-time-to-die

Project-scoped skill for the BOND film package at
`projects/working/bond/no_time_to_die/`. Load this when working inside the
project.

## When to Use

- Working inside the HERACLES package — running mission phases, editing source,
  or regenerating figures/manuscript variables.
- Implementing or verifying the `bond_api.MissionProvider` adapter and the
  frozen protocol integration.

## Quick Reference

```bash
cd projects/working/bond/no_time_to_die
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
- **Outputs are disposable.** Regenerate `output/` (git-ignored); never hand-edit.
- **Local-only.** No remote, never push.

## Cross-refs

- Project contract: [`AGENTS.md`](../../../AGENTS.md)
- README: [`README.md`](../../../README.md)
- TODO: [`TODO.md`](../../../TODO.md)
