# data/

Versioned project inputs for the `no_time_to_die` (HERACLES) package.

- `claim_ledger.yaml` — every numeric constant the demonstration consumes, each
  classified `synthetic: true` (invented here) or `synthetic: false` (a
  commonly-cited order-of-magnitude figure carried without a citation). Nothing
  here is a measurement. Bound to the code by `tests/test_claim_ledger.py`. See
  `AGENTS.md` in this directory for the schema and edit protocol.

Generated artifacts (figures, resolved manuscript, manuscript variables) are
written under `output/`, which is git-ignored.
