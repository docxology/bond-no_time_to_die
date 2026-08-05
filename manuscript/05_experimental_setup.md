# Experimental Setup

## Software environment

- Python {{PYTHON_VERSION}} (host), NumPy for the delivery/figure numerics,
  matplotlib (Agg backend) for figure rendering, PyYAML for config loading.
- Repository tree: isolated local-only package rooted at
  `projects/working/bond/no_time_to_die`; a local path dependency on the frozen
  `bond-api` protocol.

## Deterministic demonstration parameters

Canonical inputs live in `src/no_time_to_die/demo.py` and
`manuscript/config.yaml`. Every value below is a resolved token read from those
constants at hydration time, so the table cannot drift from the code that runs:

| Parameter | Value |
| --- | --- |
| Reference genome length | {{HERACLES_REFERENCE_LENGTH}} nt ({{HERACLES_REFERENCE_SEGMENTS}} labelled {{HERACLES_GUIDE_LENGTH}}-nt segments) |
| — exact on-target windows planted | {{HERACLES_PLANTED_ON_TARGET}} |
| — near-miss windows planted | {{HERACLES_PLANTED_NEAR_MISS}} |
| Guide candidates | {{HERACLES_NUM_GUIDES}} |
| Guide length | {{HERACLES_GUIDE_LENGTH}} nt |
| Off-target tolerance `k` | {{HERACLES_MAX_MISMATCHES}} |
| Absorption rate `k_a` | {{HERACLES_ABSORPTION_RATE}} h⁻¹ |
| Exposure time | {{HERACLES_EXPOSURE_TIME}} h |
| Avidity | {{HERACLES_AVIDITY}} |
| Antidote antagonist concentration | {{HERACLES_ANTAGONIST_CONC}} mg/L |
| Exposure pathway — concentration | {{HERACLES_EXP_CONCENTRATION}} |
| Exposure pathway — contact rate | {{HERACLES_EXP_CONTACT_RATE}} |
| Exposure pathway — duration | {{HERACLES_EXP_DURATION}} |
| Exposure pathway — absorbed fraction | {{HERACLES_EXP_ABSORBED_FRACTION}} |
| Exposure pathway — elimination rate `k_e` | {{HERACLES_EXP_ELIMINATION_RATE}} |
| Exposure pathway — NOAEL | {{HERACLES_EXP_NOAEL}} |
| Exposure pathway — reference dose (RfD) | {{HERACLES_EXP_RFD}} |
| Forensic signal / RMS noise | {{HERACLES_FOR_SIGNAL}} / {{HERACLES_FOR_NOISE}} |
| Forensic residue volume | {{HERACLES_FOR_VOLUME}} mL |
| Forensic transfer fraction | {{HERACLES_FOR_TRANSFER}} |
| Forensic calibration slope `m` / intercept `b` | {{HERACLES_FOR_SLOPE}} / {{HERACLES_FOR_INTERCEPT}} |
| Limit-of-detection SNR | {{HERACLES_LOD_SNR}} |
| Catalog flora | {{HERACLES_NUM_TOXINS}} |
| Forensic library | {{HERACLES_NUM_LIBRARY}} |
| Domain modules | {{HERACLES_NUM_MODULES}} |
| Seed | {{HERACLES_SEED}} |
| Canonical input digest (sha256, first 12) | `{{HERACLES_INPUT_HASH}}` |

All are fixed at import. No module in the package imports a clock or an RNG
(structurally enforced — see [Reproducibility](#reproducibility)), so two runs
on one interpreter render byte-identical artifacts. The single host-dependent
value in the whole package is the `PYTHON_VERSION` token above.

The reference genome is not an arbitrary or periodic string. It is assembled
from labelled segments — {{HERACLES_PLANTED_ON_TARGET}} exact copies of the
target guide, {{HERACLES_PLANTED_NEAR_MISS}} near-miss windows at declared
Hamming distances, and neutral fillers — precisely so the specificity and
off-target results are *measured against a known planted structure* rather than
forced by the input. The earlier reference was `AACCGGTTAACCGGTT` repeated four
times, whose period equalled the guide length; that reference could only ever
return 100% specificity, zero off-target windows, and zero population
off-target risk, so those numbers carried no information. See
[Results](#results).

## Figure generation

Figures are rendered deterministically by `src/no_time_to_die/figures/plots.py`
under a headless `Agg` backend to `output/figures/`. Each renderer reads the
same `demo.py` constants as the mission and the manuscript tokens, so a figure
cannot annotate a parameter the demonstration does not use:

- `delivery_kinetics.png` — bateman plasma-concentration curve over a
  {{HERACLES_DELIVERY_HORIZON_H}} h horizon, marking the
  {{HERACLES_EXPOSURE_TIME}} h exposure window.
- `toxicology_dose_response.png` — Hill curves for the full catalog.
- `guide_efficiency.png` — guide-design efficiency vs GC content.
- `antidote_response.png` — competitive-antagonist dose–response, marking the
  {{HERACLES_ANTAGONIST_CONC}} mg/L demonstration dose.
- `detection_confidence.png` — logistic detection confidence vs SNR against the
  {{HERACLES_LOD_SNR}} limit of detection.
