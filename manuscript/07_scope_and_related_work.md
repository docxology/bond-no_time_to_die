# Scope and Related Work

## Scope

This package models the *computational* skeleton of the HERACLES narrative arc
in *No Time to Die* (2021). It does **not** claim biological fidelity to a
real bioweapon, a real pharmacology database, or a real analytical instrument.
**Nothing in this package is a measurement.** The value is in the *method* —
reproducible, task-appropriate modelling with auditable provenance — not in the
specific constants.

Every constant is registered in `data/claim_ledger.yaml` under one of exactly
two provenance classes, and the split matters:

- **Invented for this demonstration** (`synthetic: true`): the DNA reference and
  guide set, all seven Hill slopes, the forensic spectral fingerprints and the
  unknown spectrum, the guide-design model parameters, every demonstration
  scenario parameter, and **all five antidote `Ki` values**.
- **Commonly-cited order-of-magnitude figures for real substances**
  (`synthetic: false`), recorded without a specific citation and used as
  plausible calibrants rather than as data: the seven LD50 values and the
  conventional limit-of-detection SNR of 3.

### Withdrawn claim: the antidote inhibition constants

This is worth naming rather than burying in a table. Through 2026-08-04 the
ledger labelled all five antidote `Ki` values "Published approximation, *drug*
Ki" and left them unflagged, placing them on the measured side of the ledger's
own distinction, and the module docstring called them
"published-approximation inhibition constants". That was false. No publication
reports these numbers, and two independent facts make it impossible that any
could:

- Naloxone and flumazenil bind their receptors at nanomolar affinity. The
  recorded 0.4 and 1.0 mg/L are not those quantities in any unit system.
- Pralidoxime reactivates phosphorylated acetylcholinesterase, acetylcysteine is
  a glutathione precursor, and vitamin K is a cofactor in an enzymatic cycle.
  None is a competitive receptor antagonist, so none has a `Ki` of the kind the
  Cheng–Prusoff relation consumes. The model is applied to them uniformly
  regardless — a property of this demonstration, not of the pharmacology.

The values are now marked `synthetic: true` with honest source labels, and
`tests/test_claim_ledger.py` fails if any is re-flagged as measured. The
antidote screen therefore demonstrates that the ranking arithmetic is correct,
and demonstrates nothing about clinical antidote choice.

Boundaries kept deliberately out of scope:

- No simulation of DNA damage or clearance pharmacology beyond the
  one-compartment delivery model.
- No instrument noise model beyond additive RMS noise.
- No claims of real-world forensic admissibility.
- No claim that any model would behave this way on a real genome, patient, or
  instrument. The reference genome is a *constructed* input with a planted,
  documented structure; the results measure recovery of that planted structure.

### Uncertainty and limitations (round-2 additions)

Three quantities introduced or re-exposed in round 2 carry their own,
explicit uncertainty:

- **Mixture mixing fractions.** `decompose_mixture` reports weights that are
  a *fit*, not a measurement. They are exact here only because the 5-bin
  fingerprints are noiseless and the blend was planted; on a real residue the
  weight estimates would carry instrument noise, unknown transfer, and
  library incompleteness that no model in this package captures. The residual
  token reports the fit's unexplained variance, and the weights sum to one by
  construction (they cannot express a missing third component or an absolute
  recovered amount).
- **The challenge therapeutic window.** `HERACLES_WINDOW` is the ratio of the
  toxin LD50 to the administered demo dose. It is arithmetic context, not a
  pharmacology finding: the LD50 is itself an order-of-magnitude figure with
  no citation (see the `synthetic`/`synthetic: false` split in
  `data/claim_ledger.yaml`), the dose is a synthetic input, and a real
  therapeutic window depends on route, species, and formulation the ratio
  does not model. The margin is consequently not a clinical safety margin.
- **The LD50 values remain uncited.** Per the ledger contract, `synthetic:
  false` means ``a commonly-cited order-of-magnitude figure … recorded without
  a specific citation`` — a provenance *label*, not a reference. This round
  deliberately did **not** fabricate bibliographic entries to fill the seven
  `ld50_*` `citation:` fields; sourcing each to a specific publication is
  recorded as open work in `TODO.md` rather than papered over.

## Related work

The package extends the BOND suite pattern established by `bond-api` (the
frozen mission protocol), `bond-orchestrator` (the DAG runner), and
`bond-utilities` (Layer 0 provenance/cipher utilities), each converted from a
template exemplar scaffold under the shared 90%-coverage, zero-mock,
thin-orchestrator contract. The engineering contract is inherited from the
suite's other film packages; what is specific here is the domain lineage.

Each model is a deliberately simplified, deterministic instance of a
well-established published method rather than an invention of this package:

- **Dose–response** follows the Hill equation [@hill1910possible]; mixtures
  combine under Bliss independent action / response addition
  [@bliss1939toxicity].
- **Guide activity and off-target burden** follow the feature-based sgRNA
  design rules of Doench et al. [@doench2014rational] and the mismatch-tolerance
  characterization of Hsu et al. [@hsu2013dna], reduced here to a transparent
  GC/homopolymer score and an exponential mismatch decay.
- **Delivery kinetics** use the one-compartment first-order absorption model
  usually attributed to Bateman [@bateman1910solution] and standard in
  pharmacokinetics texts [@gibaldi1982pharmacokinetics].
- **Mixture decomposition** is a non-negative least-squares fit in the spirit
  of Lawson and Hanson [@lawsonhanson1974].
- **Antidote pharmacology** uses the Cheng–Prusoff relation
  [@cheng1973relationship] over Langmuir occupancy [@langmuir1918adsorption].
- **Exposure and risk** follow the NRC risk-assessment framing
  [@nrc1983risk]; **limit-of-detection** reasoning follows Currie
  [@currie1968limits].

The simplifications are the point: each is small enough to test exactly against
a hand-checkable value, which is what makes the whole assessment auditable.
