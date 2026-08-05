# data/ — Agent Guide (HERACLES)

Versioned project **inputs** only; generated artifacts live in `output/`
(git-ignored) and must not be committed here.

## `claim_ledger.yaml`

Registry of every numeric constant the HERACLES demonstration consumes. This is
not a documentation courtesy: `tests/test_claim_ledger.py` derives the expected
constant set by scanning the domain modules and fails the build on an
unregistered constant, an orphaned entry, or a value edited on one side only.
Schema v2.0.0 (preserve when editing — the test reads these fields):

| Field | Required | Purpose |
| --- | --- | --- |
| `id` | yes | Stable claim identifier; must be unique |
| `value` | yes | The live value: scalar, list, or mapping. Compared for equality against the code |
| `units` | yes | Unit label for readers |
| `synthetic` | yes | `true` = invented for this demonstration; `false` = commonly-cited order-of-magnitude figure for a real substance, carried without a specific citation |
| `source` | yes | Human-readable provenance label. **Not a citation** |
| `note` | no | Explanatory remark |

**`synthetic: false` does not mean "measured".** Nothing in this package is a
measurement. The `source` field is a label, and no entry carries a reference.
Before v2.0.0 the five antidote `Ki` values were labelled "Published
approximation" and left unflagged, which asserted a provenance that does not
exist; see `manuscript/07_scope_and_related_work.md` for the withdrawal.

Id naming is mechanical, because the test derives it: a module constant
registers under its lowercased name (`DEMO_EXPOSURE_TIME` → `demo_exposure_time`),
and a catalog/library entry under `<field>_<entry>` (`ld50_ricin`, `hill_ricin`,
`ki_naloxone`, `spectrum_ricin`).

## Edit protocol

1. Change the code and the ledger in the same commit — the gate compares them.
2. Adding a constant to a domain module means adding an entry here, or the suite
   reports `unregistered constant: <id>`.
3. Keep prose metrics token-driven (`manuscript_variables.py`); the ledger
   records their inputs, not the measurements themselves.
4. Never store generated CSV/JSON/PNG under `data/`.

Quick orientation: [`README.md`](README.md).
