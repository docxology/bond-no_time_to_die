# Manuscript syntax (HERACLES)

- Provisional `.md` sections use Pandoc markdown. Citations use `[@key]`
  (parenthetical) or `@key` (narrative); figure references use Pandoc-crossref
  `[@fig:label]` / `@fig:label` and a markdown image with `{#fig:label}`.
- Figures live under `../output/figures/` relative to the manuscript root and
  are rendered by `src/no_time_to_die/figures/plots.py`.
- Tokens: `{{TOKEN}}` literals in numbered (`NN_*.md`) sections must resolve
  through `generate_variables()`. Do **not** put literal `{{...}}` placeholders
  in rendered prose — keep them only in `.md` guide files (SYNTAX.md, AGENTS.md,
  README.md) that are excluded from the strict token gate.
- This package does not run the monorepo render pipeline; the token gate and
  coverage/mypy/ruff suites are the enforced contract.
