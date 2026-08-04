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
