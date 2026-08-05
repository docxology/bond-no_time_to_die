# Scope and Related Work

## Scope

This package models the *computational* skeleton of the HERACLES narrative arc
in *No Time to Die* (2021). It does **not** claim biological fidelity to a
real bioweapon, a real pharmacology database, or a real analytical instrument.
The DNA reference and guide set are synthetic fixed inputs chosen to exercise
the algorithms deterministically; the poison LD50 values are standard
published approximations recorded for transparency in
`data/claim_ledger.yaml`; the forensic "spectral fingerprints" are synthetic
non-negative calibrants. The value is in the *method* — reproducible,
task-appropriate modelling with auditable provenance — not in the specific
constants.

Boundaries kept deliberately out of scope:

- No simulation of DNA damage or clearance pharmacology beyond the
  one-compartment delivery model.
- No instrument noise model beyond additive RMS noise.
- No claims of real-world forensic admissibility.

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
- **Antidote pharmacology** uses the Cheng–Prusoff relation
  [@cheng1973relationship] over Langmuir occupancy [@langmuir1918adsorption].
- **Exposure and risk** follow the NRC risk-assessment framing
  [@nrc1983risk]; **limit-of-detection** reasoning follows Currie
  [@currie1968limits].

The simplifications are the point: each is small enough to test exactly against
a hand-checkable value, which is what makes the whole assessment auditable.
