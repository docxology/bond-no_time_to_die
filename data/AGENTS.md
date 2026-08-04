# data/ — Agent Guide (HERACLES)

Versioned project **inputs** only; generated artifacts live in `output/`
(git-ignored) and must not be committed here.

## `claim_ledger.yaml`

Evidence registry for sourced numeric claims. Every numeric constant used by
the HERACLES demonstration is registered here so the evidence-registry
validation can trace it. Schema (preserve when editing):

| Field | Purpose |
| --- | --- |
| `id` | Stable claim identifier |
| `value` / `value_mg_per_kg` | Declared numeric value |
| `source` | Provenance (publication approximation, module, or 'synthetic') |
| `synthetic` | Optional bool marking purely synthetic calibrant/input |
| `note` | Optional explanatory remark |

Synthetic inputs (demo genome, guide set, spectra) are declared `synthetic:
true` so they are never mistaken for measured data.

## Edit protocol

1. Edit when a manuscript claim, figure default, or source-backed numeric fact
   changes.
2. Keep prose metrics token-driven (`manuscript_variables.py`); the ledger
   records their inputs, not the measurements themselves.
3. Never store generated CSV/JSON/PNG under `data/`.

Quick orientation: [`README.md`](README.md).
