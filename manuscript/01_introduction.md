# Introduction

*No Time to Die* (2021) introduces three interlocking threats that map cleanly
onto computational modelling problems: a DNA-targeted bioweapon program
codename **HERACLES** designed against a specific genetic profile; the poison
garden cultivated on the villain's island, a landscape of naturally occurring
plant toxins; and the forensic task of detecting a poison delivered through a
drink — the trace left on the Vesper's glass.

This package treats each as a real, deterministic computational object rather
than a narrative device:

1. **Target specificity and delivery** — a designed nucleic-acid guide must hit
   its intended target while minimizing off-target matches in a reference
   genome, and the fraction of an administered dose that reaches the target
   compartment follows first-order absorption kinetics.
2. **Dose–response toxicology** — every member of the garden's flora is a
   Hill-curve hazard characterized by an LD50 and a slope; mixtures combine
   under response addition.
3. **Delivery forensics** — given an observed analytical signal and noise, we
   decide whether a trace is present, back-compute its concentration from a
   calibration model, and identify the poison by spectral matching.

The design honours the BOND suite contract: the domain core is pure and
importable without bond-api, the mission adapter implements the frozen
protocol, every metric flows into the manuscript through
`src/no_time_to_die/manuscript_variables.py`, and the whole assessment is
deterministic and fully tested. A reader can open any function named in
[Methodology](#methodology) and trace it to its source file in seconds.
