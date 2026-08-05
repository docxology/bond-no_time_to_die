# Conclusion

{{HERACLES_TITLE}} demonstrates that the three central threats of *No Time to
Die* (2021) — a DNA-targeted bioweapon, a poison garden, and delivery
forensics — can be expressed as a single deterministic, fully-tested
computational core under the BOND suite contract.

The package delivers **{{HERACLES_NUM_MODULES}}** concrete claims — one per
domain module — each verified by real computation rather than assertion:

1. A target-specific countermeasure can be selected and its neutralization
   probability bounded by specificity, delivered fraction, and avidity
   (`bioweapon_counter.py`).
2. A guide can be *designed* and ranked by a Doench-style efficiency blended
   with population off-target burden (`targeting_design.py`).
3. A poison-garden flora catalog can be profiled as Hill-curve hazards and
   combined under response addition (`toxicology.py`).
4. A competitive-antagonist antidote can be screened against a toxin dose by
   Cheng–Prusoff pharmacology and restored survival
   (`antidote_screening.py`).
5. A delivered exposure can be assessed through pathway intake, cumulative
   burden, margin of exposure, and risk quotient (`exposure_assessment.py`).
6. A delivered poison leaves a structurally detectable and identifiable
   residue on the vessel (`delivery_forensics.py`).

The domain core is infrastructure-free and importable without bond-api; a thin
adapter implements the frozen `MissionProvider` protocol, and every metric
flows into the manuscript through the shared `demo.py` + `manuscript_variables.py`
path, guarded by `check_demo_completeness` so a renamed result key fails the
build rather than silently hydrating a zero. This is the reference film pattern
for the remaining BOND suite packages.

The clearest limitation is the one the [Scope](#scope-and-related-work) section
names: the constants are published approximations and synthetic calibrants, not
measurements. The demonstration therefore supports claims about the *method* —
that these threats admit deterministic, auditable, end-to-end modelling — and
not about any real toxin, guide, or instrument. The exposure verdict makes the
point concretely: a margin of exposure of {{HERACLES_MOE}} against a risk
quotient of {{HERACLES_RQ}} is a statement about the demonstration's chosen
NOAEL and reference dose, not about anyone's actual risk.
