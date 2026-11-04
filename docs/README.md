# docs/ — Agent-Facing Documentation Hub (HERACLES)

Technical rulebook for agents and developers working inside the
`no_time_to_die` (HERACLES) film package.

## File inventory

| File | Purpose |
| --- | --- |
| `README.md` | `docs/` navigation (this file) |
| `AGENTS.md` | `docs/` index — overview of this directory |
| `agent_instructions.md` | Behavioral rules R1–R7 for AI agents (read-first) |
| `architecture.md` | Layer boundaries, per-module inventory, how `mission.py` implements the frozen MissionProvider, how-to-add-concept |
| `testing_philosophy.md` | Zero-mock policy and coverage mechanics |

## Reading order

1. `agent_instructions.md` — start here; 7 hard rules + consequence matrix.
2. `architecture.md` — layer boundaries before touching any file.
3. `testing_philosophy.md` — zero-mock constraint before writing tests.

## Verification commands

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
uv run python scripts/vendor.py --check
grep -rn --include='*.py' "unittest.mock\|MagicMock\|@patch\|create_autospec" tests/ || echo Clean
rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**' --glob '!output/**' || echo Clean
```
