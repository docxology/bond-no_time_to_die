# manuscript/ — HERACLES (No Time to Die, 2021)

Prose sections for the `no_time_to_die` film package. Numbered `NN_*.md` files
are the only files hydrated by `src/no_time_to_die/manuscript_variables.py`:
every `{{TOKEN}}` in them must resolve through `generate_variables()`, enforced
by the live cross-reference test in `tests/test_manuscript_variables.py`.

## Token protocol

Metrics and identity flow through tokens — never hand-author a number in prose.
The source of truth is `generate_variables()`; `scripts/z_generate_manuscript_variables.py`
writes the resolved tree to `output/manuscript/` and fails (strict mode) on any
leftover token.

## Figures

Figures are Pandoc-crossref-referenced and rendered by
`src/no_time_to_die/figures/plots.py` to `output/figures/`:

| Label | File |
| --- | --- |
| `{#fig:delivery}` | `delivery_kinetics.png` |
| `{#fig:toxicology}` | `toxicology_dose_response.png` |
| `{#fig:guidance}` | `guide_efficiency.png` |
| `{#fig:antidote}` | `antidote_response.png` |
| `{#fig:detection}` | `detection_confidence.png` |

## Files

- `config.yaml` — paper/film metadata and deterministic demo parameters.
- `config.yaml.example` — copy-and-customize template.
- `layer_contract.yaml` — project-local layer boundaries.
- `references.bib` / `99_references.md` — bibliography (index-section + bib).
- `SYNTAX.md` — citation/figure syntax notes.
