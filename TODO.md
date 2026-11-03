# TODO — no_time_to_die (HERACLES)

`no_time_to_die` is the *No Time to Die* (2021) film package of the PROJECT BOND
suite, codename **HERACLES**: a pure, deterministic Python domain core (DNA
countermeasure targeting, guide design, poison-garden toxicology, antidote
screening, exposure assessment, delivery forensics) plus a thin
`bond_api.MissionProvider` adapter, a live-token manuscript, and a
constant-by-constant provenance ledger. Verified state as of 2026-08-05 on this
tree (commit `7b9382d`): `uv run pytest tests/ --cov=src --cov-fail-under=90`
passes with **301 tests** and **100.00% line+branch coverage** on `src/`
(687 statements, 216 branches, 0 missed); `ruff check`, `ruff format --check`,
and `mypy src/ scripts/` are clean; the mock grep and the exemplar-lineage grep
both report nothing; `git status --short` is empty. The Phase-6 adversarial
audit is fully remediated — every finding in
`../output/verify/no_time_to_die.json` was made true or withdrawn, and each is
now pinned by a test with a positive control, so none of them reappears below.

## Round-2 (2026-08-06)

Hostile self-review plus the standing backlog (C1/C2/C3, V1/V2, E1/E2). All
gates green: **325 passed, 0 skipped, 0 failed**; line+branch coverage on
`src/` **99.91%** (gate ≥90, 0 missed lines, 1 partial branch); `ruff check`
and `ruff format --check` clean; `mypy src/ scripts/` clean (19 files); mock
grep and exemplar-lineage grep clean; `git status` clean after commit.

### Findings and fixes

- **[NEW — hostile review] `fraction_affected` overflowed to `OverflowError`
  on a large dose.** The naive `dose**hill / (dose**hill + ld50**hill)` raises
  `OverflowError` (or would read `nan` = inf/inf at the borderline) for a large
  enough `dose` and `hill`, e.g. `fraction_affected(1e200, 1.0, 3.0)`. Fix:
  the overflow-free form `1 / (1 + (ld50/dose)**hill)`, which is equal wherever
  neither overflows and returns the correct limit 1.0 for arbitrarily large
  doses. *Evidence:* `tests/test_toxicology.py::test_extreme_dose_does_not_overflow`
  (also pins the LD50 value still reads 0.5).*
- **C2 — `mission.py` determinism constraint still said "fixed seed, no random
  draws"**, the one protocol payload an orchestrator/CLI actually reads. Change:
  detail is now `"no clock, no RNG, no external calls"` (DEMO_SEED governs
  nothing). *Evidence:* `tests/test_mission.py::test_determinism_constraint_makes_no_governing_seed_claim`.
- **C3 — `therapeutic_window` / `margin_of_safety` were 100%-covered dead
  public surface.** Resolved by *wiring them in*: `screen_report` now returns
  `challenge_therapeutic_window` (`toxin ld50 / dose`) and
  `challenge_margin_of_safety` (`window - 1`, `None` for a zero dose), tokens
  `HERACLES_WINDOW`/`HERACLES_MARGIN` quote them, and `docs/architecture.md`
  and the tests record the consumer. *Evidence:*
  `tests/test_antidote_screening.py::TestScreenReport` (shape, LD50-driven
  window, zero-dose `None`).
- **C1 — `bond-api` path dependency was an absolute machine path.** Now
  `bond-api = { path = "../bond-api" }` (relative), and `bond-utilities` is
  declared the same way for E1. *Evidence:* the package tree was copied to a
  fresh location under `/tmp`, linked to the sibling deps, `uv sync`'d and all
  325 tests passed from there — no absolute path required.
- **V1 — `match_unknown`'s all-or-nothing contract was untested.**
  `tests/test_delivery_forensics.py::test_heterogeneous_length_library_raises_all_or_nothing`
  now pins that a library mixing compatible and incompatible lengths raises
  rather than ranking the compatible subset.
- **V2 — `docs/architecture.md`'s function inventory was unbound prose.**
  `tests/test_architecture.py::TestInventoryBinding` parses the
  "The domain modules, individually" table, resolves every backticked
  identifier on its module, and proves (via a fabricated-identifier control)
  that the parse is not vacuous.
- **E1 — provenance persistence is now bound to `bond-utilities`.**
  `scripts/execute.py` runs the execution then persists the mission record via
  `mission_io.record_provenance_outcome` into
  `output/data/mission_record.json` with **pinned** `started_at`/`now` (a real
  wall clock would break byte-identity). `bond-utilities` is a declared
  dependency. *Evidence:*
  `tests/test_scripts_smoke.py::test_execute_writes_a_byte_identical_mission_record`
  (two runs byte-identical, and the record passes `verify_provenance`).
- **E2 — mixture spectral decomposition added.** `decompose_mixture` /
  `mixture_analysis` in `delivery_forensics.py` do a non-negative 1-/2-component
  least-squares fit (spirit of Lawson & Hanson 1974, added to
  `references.bib`) that recovers the mixing fractions of a residue that is a
  blend — which single-spectrum cosine matching cannot express. The demo carries
  a 60/40 ricin+atropine blend (`FORENSIC_MIXTURE`, registered in
  `data/claim_ledger.yaml` and in `input_payload()`), `run_demo`'s forensics
  includes it, and tokens `HERACLES_MIX*` quote the live result. *Evidence:*
  `tests/test_delivery_forensics.py::TestDecomposeMixture` /
  `TestMixtureAnalysis` (blend→pair, pure→single, empty/zero/heterogeneous
  errors, clip and collinear branch controls).
- **NEW — the str/weight swap bug in `mixture_analysis` was caught and fixed
  during development** (secondary name vs weight were swapped); covered by the
  test suite.

### Manuscript deepening

- `manuscript/02_methodology.md`: mixture-decomposition maths; the challenge
  therapeutic-window definition in the antidote section.
- `manuscript/03_results.md`: live-token "Mixture decomposition" subsection; a
  therapeutic-window + margin sentence in the antidote section.
- `manuscript/07_scope_and_related_work.md`: a dedicated "Uncertainty and
  limitations (round-2 additions)" subsection covering the mixture fractions,
  the therapeutic window, and the uncited LD50 status; a Lawson & Hanson
  related-work entry.
- `manuscript/references.bib`: `@lawsonhanson1974`.
- `output/` regenerated live from the engine (`manuscript_variables.json`, 9
  resolved sections, 5 figures) by `z_generate_manuscript_variables.py`.

### Left for a future round

- **D1 remains open, by deliberate choice.** The seven `ld50_*` values still
  carry no `citation:`; `synthetic: false` remains "commonly-cited
  order-of-magnitude … without a specific citation". Round-2 did **not**
  fabricate bibliographic entries to fill them — sourcing each to a specific
  real publication (and re-flagging any that cannot be) is recorded in
  `manuscript/07_scope_and_related_work.md` "Uncertainty and limitations" and
  left here. This is the honest resolution, not a made-true one.
- The final partial branch on `manuscript_variables._mix_*` non-numeric-guard
  paths (99.91% line+branch, gate ≥90%) is left uncovered: it is defensive code
  not reachable from a real demo result.
- C1's symlink relocation check is not part of the committed suite (needs a
  sibling-tree copy); re-run the `/tmp` relocation + `uv sync` + pytest to
  confirm relocatability on a fresh checkout.

---
## Open work

Eight items. Two trace to entries still listed in
`../output/verify/no_time_to_die.unresolved.json` (C2, D1); the rest were found
by reading the tree this session.

### Correctness

**C1 — `bond-api` path dependency is an absolute machine path.**
`pyproject.toml:33` reads
`bond-api = { path = "/Users/4d/Documents/GitHub/template/projects/working/bond/bond-api" }`.
The package therefore cannot be synced from a relocated or cloned checkout, and
this violates the standing "never hardcode paths" rule. `bond-cli` and
`bond-orchestrator` already use the relative form (`{ path = "../bond-api" }`);
most film packages, including this one, do not — so this is a suite-wide
pattern, but fixing it here is self-contained and needs no sibling edits.
*Done:* line 33 is `bond-api = { path = "../bond-api" }` and a sync + full suite
succeeds with the package tree moved (or with the absolute path made
unreachable).
*Command:*
```bash
cp -R no_time_to_die /tmp/ntd_relocate && cd /tmp/ntd_relocate \
  && ln -s "$OLDPWD/../bond-api" ../bond-api \
  && uv sync --all-extras && uv run pytest tests/ -q
```

**C2 — `mission.py` still emits the withdrawn "fixed seed" framing.**
`src/no_time_to_die/mission.py:108-110` builds
`Constraint(kind="determinism", detail="fixed seed, no random draws, no external calls")`
into every `MissionBrief`. Phase-6 established that `DEMO_SEED` governs nothing
(no code path draws from an RNG) and corrected the wording in `AGENTS.md:19-20`,
`docs/agent_instructions.md:68-69`, `manuscript/06_reproducibility.md:34-36`,
and `data/claim_ledger.yaml:237` — the protocol payload was missed, so the one
copy an orchestrator or `bond-cli` actually reads is the one still implying the
seed does work. *(Residual of unresolved-audit entry #3.)*
*Done:* the constraint detail no longer asserts a governing seed (e.g.
`"no clock, no RNG, no external calls"`), and `tests/test_mission.py` asserts
the emitted detail rather than leaving it unpinned — so a re-introduction fails.
*Command:* `uv run pytest tests/test_mission.py -q && rg -n "fixed seed" src/ scripts/ docs/ manuscript/ AGENTS.md README.md`
(expected: no hits in `src/`).

**C3 — `therapeutic_window` / `margin_of_safety` are advertised but consumed by
nothing.** Defined at `src/no_time_to_die/antidote_screening.py:148` and `:161`,
exported at `:53,56`, and listed in `docs/architecture.md:33` as part of what
the module computes. No caller exists in `src/` (`screen_antidotes`,
`screen_report`, `demo.run_demo`, `mission.execute`, and
`manuscript_variables.generate_variables` all ignore them), no manuscript token
reads them, and they are reachable only from
`tests/test_antidote_screening.py:82-95`. They are therefore 100%-covered dead
public surface: the coverage figure asserts nothing about them being used.
*Done:* either (a) `screen_report` returns a window/margin per antidote, a
`HERACLES_*` token quotes it, and the claim ledger registers any new constant;
or (b) both functions are removed from the module, `__all__`, the tests, and
`docs/architecture.md:33`. Not both, and not left as-is.
*Command:* `uv run pytest tests/ --cov=src --cov-fail-under=90 -q && rg -n "therapeutic_window|margin_of_safety" src/ manuscript/ docs/`

### Verification

**V1 — `match_unknown`'s all-or-nothing contract is documented but untested.**
`src/no_time_to_die/delivery_forensics.py:159-162` states it raises
`ValueError` "if `unknown_spectrum` … length differs from *any* library
spectrum — matching is all-or-nothing, never a partial ranking over the
compatible subset". `tests/test_delivery_forensics.py:124-141` covers the happy
path, the empty library, descending order, and a custom library, but never
passes a heterogeneous-length library. The invariant that distinguishes this
design from a partial ranking is the one behaviour nothing can fail on. (The
underlying `cosine_similarity` length check is tested at
`tests/test_delivery_forensics.py:110`, which is a different claim.)
*Done:* a test in `tests/test_delivery_forensics.py` passes a library where one
entry is length-compatible and one is not, and asserts `ValueError` — proving no
partial ranking is returned.
*Command:* `uv run pytest tests/test_delivery_forensics.py -q`

**V2 — the function inventory in `docs/architecture.md` is unbound prose.**
`tests/test_architecture.py` binds the *import graph* and the layer rules to the
source by AST, and proves the derivation can fail. It does not bind the table at
`docs/architecture.md:28-36`, which names roughly thirty public functions and
constants (`plasma_concentration`, `dose_for_fraction`, `catalog_stats`,
`risk_quotient`, `vesper_trace_report`, …). Renaming or deleting any of them
leaves that table silently wrong — the exact drift class that produced the
SEVERE and MODERATE doc-vs-code findings in the Phase-6 audit.
*Done:* a test parses the backticked identifiers out of that table, resolves the
module each row names, and asserts every identifier is in that module's
`__all__`; a negative control (a fabricated identifier injected into a temp copy
of the table) proves the parse is not vacuous.
*Command:* `uv run pytest tests/test_architecture.py -q`

### Documentation

**D1 — the seven LD50 values carry no citation.**
`data/claim_ledger.yaml:32,42,52,62,72,82,92` register `ld50_ricin`,
`ld50_atropine`, `ld50_coniine`, `ld50_aconitine`, `ld50_strychnine`,
`ld50_nicotine`, `ld50_cyanide` as `synthetic: false` with a `source` that is a
label ("Commonly-cited order-of-magnitude figure, …"), not a reference; the
values live in `src/no_time_to_die/toxicology.py:109` (`TOXIN_CATALOG`).
`manuscript/references.bib` has 14 entries, none of them toxicological. The
ledger header (`data/claim_ledger.yaml:15-23`) is honest about this — that is
the *stated limitation* resolution the audit accepted, not a made-true one.
*(Carried from unresolved-audit entry #1.)*
*Done:* each `ld50_*` entry gains a `citation:` key naming a specific
publication or authoritative compendium, those references land in
`manuscript/references.bib` and `manuscript/99_references.md`, and
`manuscript/07_scope_and_related_work.md:19-22` is updated to say the values are
sourced rather than carried without a citation. Anything that cannot be sourced
must be re-flagged `synthetic: true` instead of being left in the middle.
*Command:* `uv run pytest tests/test_claim_ledger.py -q && rg -n "citation:" data/claim_ledger.yaml | wc -l`
(expected: 7 or more, and every uncited `synthetic: false` toxin entry gone).

### Extension

**E1 — bind `bond-utilities` provenance persistence (now unblocked).**
`TODO.md` has carried this as "not yet bound" since phase 2, but the dependency
has shipped:
`../bond-utilities/src/bond_utilities/mission_io.py:153` defines
`record_provenance_outcome(mission_id, seed, version, input_payload, outcome, path, fmt=None, codename=None, started_at=None, now=None)`.
`scripts/execute.py` currently just forwards to `run_mission.main(["execute"])`
and persists nothing; `mission.execute` already builds a `Provenance` carrying
package version, `DEMO_SEED`, `demo.input_hash()`, and `wall_time_s`, so the
bind is mechanical. **Determinism trap:** `record_provenance_outcome` calls
`datetime.now(timezone.utc)` unless *both* `started_at` and `now` are supplied —
writing its record into a tracked artifact without pinning those reintroduces
exactly the wall-clock defect Phase-6 removed, and
`tests/test_determinism.py:147-172` will only catch it if the record is inside
the rendered manuscript tree.
*Done:* `scripts/execute.py` (or `run_mission.py`) writes the mission record via
`mission_io.record_provenance_outcome` with a pinned `started_at`/`now` into
`output/data/` (the existing artifact directory, e.g.
`output/data/mission_record.json`), the written file is byte-identical across
two runs, and `bond-utilities` is declared in `pyproject.toml`
`[tool.uv.sources]`.
*Command:*
```bash
REC=output/data/mission_record.json
uv run python scripts/run_mission.py execute && cp "$REC" /tmp/r1.json \
  && uv run python scripts/run_mission.py execute && diff /tmp/r1.json "$REC" \
  && uv run pytest tests/test_determinism.py tests/test_scripts_smoke.py -q
```

**E2 — mixture spectral matching in `delivery_forensics`.**
`match_unknown` (`src/no_time_to_die/delivery_forensics.py:150`) ranks a single
unknown spectrum against the 5-entry `SPECTRUM_LIBRARY` (`:141-147`) by cosine
similarity. A residue that is a blend of two library poisons ranks as a poor
single match with no indication that it is a mixture, even though `toxicology`
already models mixtures (`combined_fraction_affected`, Bliss response addition).
*Done:* a mixture-aware ranking (e.g. non-negative two-component decomposition)
exists with tests that pin a synthesised 60/40 blend to the correct pair and to
approximately the right weights, its constants are registered in
`data/claim_ledger.yaml`, and the method appears in
`manuscript/02_methodology.md`.
*Command:* `uv run pytest tests/test_delivery_forensics.py tests/test_claim_ledger.py -q`

## Known limitations (not bugs)

These are accepted and recorded so they are not re-litigated. Several are the
honest scope the Phase-6 audit forced claims down to.

- **Nothing in this package is a measurement.** `synthetic: false` in
  `data/claim_ledger.yaml` means "a commonly-cited order-of-magnitude figure for
  a real substance, recorded without a specific citation, used as a plausible
  calibrant" — the `source` field is a provenance *label*, not a reference. This
  is stated in the ledger header (`:15-23`) and in
  `manuscript/07_scope_and_related_work.md`. D1 above is the open half of this;
  the labelling itself is settled.
- **The reference genome is a constructed input.** `demo.DEMO_REFERENCE` is 144
  nt assembled from labelled segments with planted exact hits, declared
  near-misses at known Hamming distances, and fillers. Countermeasure and
  guide-design results therefore establish *recovery of a planted structure* and
  discrimination between candidates — not performance on an unseen genome.
  Real-genome or held-out evaluation is deliberately out of scope for a film
  package; the claim is stated in exactly these terms in Results, Setup, Scope,
  and Conclusion, and `tests/test_demo_evidence.py` fails if the demonstration
  degenerates back to a self-fulfilling reference. *(Unresolved-audit entry #2,
  accepted as scope.)*
- **`DEMO_SEED = 11` governs nothing.** No code path draws from an RNG. The
  constant is retained because it is part of the frozen `Provenance` record the
  protocol carries, not because it controls behaviour. Do not "fix" this by
  adding randomness. *(Unresolved-audit entry #3; C2 above is the one remaining
  place the prose was not updated.)*
- **The antidote screen demonstrates arithmetic, not pharmacology.** All five
  `Ki` values are `synthetic: true` after the Phase-6 withdrawal, and three of
  the five agents are not competitive antagonists at all — the Cheng–Prusoff
  model is applied uniformly regardless. See
  `manuscript/07_scope_and_related_work.md`, "Withdrawn claim".
- **Byte-identity is per-interpreter.** Across Python versions exactly one
  rendered substring differs: the `PYTHON_VERSION` token, the package's single
  environment read. `tests/test_determinism.py:243` pins that it is the only one.
- **`match_unknown` is all-or-nothing by design.** A library containing any
  length-incompatible spectrum raises rather than ranking the compatible subset.
  This is the intended contract (documented at
  `src/no_time_to_die/delivery_forensics.py:159-162`); V1 asks for a test, not a
  behaviour change.
- **The package is not standalone-installable.** It depends on the sibling
  `bond-api` tree by path; there is no index release. C1 makes that path
  relative, not remote.
- **Published tree.** `origin` is the GitHub repository; changes land through
  an ordinary branch, pull request and merge, and commits stay inside this
  repository.

## Verification

Run from the package root
(`projects/working/bond/no_time_to_die`). If `uv` reports
`Failed to initialize cache at ~/.cache/uv`, the shell sandbox is blocking it —
re-run the same command unsandboxed.

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
# → 301 passed; TOTAL 100.00% (line+branch) on src/; gate is >=90%

uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
# → "All checks passed!" and "34 files already formatted"

uv run mypy src/ scripts/
# → "Success: no issues found in 19 source files"

grep -rn "unittest.mock\|MagicMock\|@patch\|create_autospec" tests/ || echo Clean
# → Clean (zero-mock policy)

rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**' --glob '!output/**' || echo Clean
# → Clean (no exemplar lineage)

git status --short
# → empty
```

Targeted gates worth knowing by name: `tests/test_determinism.py` (import scan,
rendered-value scan, two-render byte comparison, all positive-controlled),
`tests/test_claim_ledger.py` (constant registry derived from the modules),
`tests/test_demo_evidence.py` (the demonstration is not green by construction),
`tests/test_architecture.py` (AST import graph vs `docs/architecture.md`), and
`tests/test_scripts_smoke.py` (real subprocess runs, strict mode, end-to-end
two-run byte equality).
