# Introduction

*No Time to Die* (2021) introduces three interlocking threats that map cleanly
onto computational modelling problems: a DNA-targeted bioweapon program
codename **HERACLES** designed against a specific genetic profile; the poison
garden cultivated on the villain's island, a landscape of naturally occurring
plant toxins; and the forensic task of detecting a poison delivered through a
drink — the trace left on the Vesper's glass.

This package treats each as a real, deterministic computational object rather
than a narrative device. Each threat family decomposes into a pair of concerns,
giving the **{{HERACLES_NUM_MODULES}}** domain modules of the core:

1. **Target specificity and delivery** (`bioweapon_counter.py`) — a designed
   nucleic-acid guide must hit its intended target while minimizing off-target
   matches in a reference genome, and the fraction of an administered dose that
   reaches the target compartment follows first-order absorption kinetics.
2. **Guide design under population off-target burden** (`targeting_design.py`)
   — the guide is not given but *designed*: sequence descriptors drive a
   Doench-style activity score, which is then discounted by the near-miss
   burden the guide would incur across a population of reference genomes.
3. **Dose–response toxicology** (`toxicology.py`) — every member of the
   garden's flora is a Hill-curve hazard characterized by an LD50 and a slope;
   mixtures combine under response addition.
4. **Antidote pharmacology** (`antidote_screening.py`) — a competitive
   antagonist shifts a toxin's effective dose–response, so a library of
   candidate antidotes can be ranked by the survival each restores against a
   given toxin dose.
5. **Exposure assessment** (`exposure_assessment.py`) — the hazard is set by
   the *absorbed* dose rather than the residue: pathway intake, body burden
   under first-order elimination, margin of exposure, and risk quotient.
6. **Delivery forensics** (`delivery_forensics.py`) — given an observed
   analytical signal and noise, we decide whether a trace is present,
   back-compute its concentration from a calibration model, and identify the
   poison by spectral matching.

Modules 1–2 and 3–4 are deliberately paired: detection without design, and
hazard without countermeasure, would each leave the mission's central question
— *can this threat be neutralized?* — unanswerable. Module 5 bridges the
forensic and toxicological halves, converting a recovered residue into an
absorbed dose the toxicology models can act on.

The design honours the BOND suite contract: the domain core is pure and
importable without bond-api, the mission adapter implements the frozen
protocol, every metric flows into the manuscript through
`src/no_time_to_die/manuscript_variables.py`, and the whole assessment is
deterministic and fully tested. A reader can open any function named in
[Methodology](#methodology) and trace it to its source file in seconds.
