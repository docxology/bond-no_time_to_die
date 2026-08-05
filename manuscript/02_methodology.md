# Methodology

This section specifies the mathematics of each concept module. All functions
are pure, side-effect-free, and deterministic; the canonical demonstration
inputs live in `src/no_time_to_die/demo.py` and are shared verbatim by the
mission adapter and the manuscript variable generator so outcomes cannot
drift.

## DNA-targeted bioweapon countermeasure (`bioweapon_counter.py`)

**Specificity.** For a guide `g` and a reference genome `r`, every
length-`|g|` window of `r` is scored by Hamming distance `d(g, w)`. A window
at distance 0 is an on-target hit; a window at distance in `[1, k]` is an
off-target hit representing a mis-address risk. Specificity is the share of
hits that are on-target:

```
specificity = on_target / (on_target + off_target)
```

`select_best_guide` chooses the candidate maximizing specificity, ties broken
by first-in-order for determinism.

**Delivery.** The one-compartment bateman equation models plasma concentration
after an absorbed dose:

```
C(t) = dose * k_a/(k_a - k_e) * (exp(-k_e t) - exp(-k_a t))
```

with `k_a` the absorption rate and `k_e` the elimination rate
(`plasma_concentration`). The absorbed fraction at exposure time `t` is
`fraction_delivered = 1 - exp(-k_a t)`.

**Countermeasure efficacy.** `neutralization_probability` combines specificity,
delivered fraction, and a saturating avidity term:

```
P = specificity * delivered_fraction * avidity/(1 + avidity)
```

clamped to `[0, 1]`, so any near-zero component drives neutralization to zero.

## Poison-garden toxicology (`toxicology.py`)

Each flora toxin is a Hill dose–response hazard with LD50 and slope `n`
(`PlantToxin`). The fraction of a population affected at dose `d` is

```
f(d) = d^n / (d^n + LD50^n)
```

with analytic inverse `dose_for_fraction`. A mixture of agents combines under
response addition — the system is unaffected only if every agent misses:

```
F = 1 - prod_i (1 - f_i(d_i))
```

The `TOXIN_CATALOG` records `{{HERACLES_NUM_TOXINS}}` botanical toxins spanning
LD50 from {{HERACLES_MIN_LD50}} to {{HERACLES_MEDIAN_LD50}} mg/kg (median), each
with a published-approximation value and a botanical source; the forensic
spectral library profiles `{{HERACLES_NUM_LIBRARY}}` poisons for identification.

## Poison-delivery forensics (`delivery_forensics.py`)

A residue signal `S` with root-mean-square noise `N` yields
`snr = S/N`. Detection confidence under a logistic model with limit of
detection `lod` is

```
confidence = 1 / (1 + exp(-(snr - lod)))
```

Concentration is back-computed from a linear calibration `S = m·C + b`
(sub-LOD signals clamp to zero), the transferred dose is
`concentration · volume · transfer_fraction` (`recovered_dose`), and an unknown
residue spectrum is identified by cosine similarity against the reference
library (`match_unknown`). The demonstration operates at a
limit-of-detection SNR of `{{HERACLES_LOD_SNR}}`.

## Guide design and population off-target (`targeting_design.py`)

The countermeasure guide is not given — it is *designed*. `gc_content` and
`longest_homopolymer` are base sequence descriptors; `guide_efficiency`
combines a GC-content sweet-spot penalty, a homopolymer-run penalty, and an
optional position-dependent nucleotide bonus into a Doench-style activity
score in `[0, 1]` (spirit of Doench et al. 2014).

Off-target burden is assessed *across a population* of reference genomes:

```
off_target_risk = sum_{genomes} sum_{windows, 1<=d<=k} exp(-lambda * d)
```

where `d` is the Hamming distance of a mismatched window and `lambda` the
mismatch decay (`population_off_target_risk`). `rank_guides` scores each
candidate as `efficiency * (1 - min(1, off_target_risk))` and `design_report`
returns the ranked table plus the best guide. The demonstration ranks
`{{HERACLES_NUM_GUIDES}}` candidates against the reference genome.

## Antidote screening (`antidote_screening.py`)

A poison-garden toxin is acted on through a receptor; a competitive
antagonist counteracts it. The apparent IC50 of a competitive antagonist
follows Cheng–Prusoff (1973):

```
IC50_app = Ki * (1 + [S] / Km)
```

with the toxin dose `[S]` and its LD50 standing in as the affinity proxy
`Km`. The fraction of receptors occupied is the Langmuir isotherm
`[A] / ([A] + IC50_app)` (`fraction_antagonized`). `screen_antidotes` ranks a
library of `{{HERACLES_ANTIDOTE_COUNT}}` antagonists by the survival they
restore against a toxin dose:

```
residual = f_tox * (1 - f_antag);  survival = 1 - residual
```

## Exposure assessment (`exposure_assessment.py`)

The hazard of a delivered poison is set by the absorbed dose, not the residue.
`absorbed_dose = concentration * contact_rate * duration * absorption_fraction`
models intake through an exposure pathway; `cumulative_exposure` accumulates
body burden under first-order elimination
`(intake_rate / k_e) * (1 - exp(-k_e t))`; `margin_of_exposure` computes
`NOAEL / absorbed` (NRC 1983 framing) and `risk_quotient` computes
`absorbed / reference_dose`. `exposure_scenario_report` composes these into a
single verdict (acceptable vs elevated risk).
