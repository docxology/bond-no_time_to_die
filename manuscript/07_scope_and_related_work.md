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
template exemplar scaffold under the shared 90%-coverage, zero-mock, thin-
orchestrator contract. The domain models are uncommon-billion
pharmaco-forensic analogues; the engineering contract is inherited from the
suite's other film packages.
