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
   with population off-target burden (`targeting_design.py`) — with the blend
   doing real work: it separates two candidates that tie at maximum efficiency,
   and it erodes the winner's own score by a non-zero off-target term.
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
names: nothing here is a measurement. Most constants are invented for this
demonstration; the rest are commonly-cited order-of-magnitude figures carried
without a citation. The demonstration therefore supports claims about the
*method* — that these threats admit deterministic, auditable, end-to-end
modelling — and not about any real toxin, guide, or instrument. Two concrete
cases: a margin of exposure of {{HERACLES_MOE}} against a risk quotient of
{{HERACLES_RQ}} is a statement about the demonstration's chosen NOAEL and
reference dose, not about anyone's actual risk; and the antidote ranking is a
statement about the arithmetic of Cheng–Prusoff over five invented inhibition
constants, not about which drug to reach for.

A second limitation is structural and worth stating in its own right: the
reference genome is a constructed input whose on-target and near-miss windows
were placed deliberately. The countermeasure and guide-design results measure
**recovery of a planted structure**, which is a weaker claim than performance on
an unseen genome and a stronger one than the package could previously make at
all — the earlier periodic reference made its own headline numbers arithmetically
inevitable.
