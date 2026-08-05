# Experimental Setup

## Software environment

- Python {{PYTHON_VERSION}} (host), numPy for the delivery/figure numerics,
  matplotlib (Agg backend) for figure rendering, PyYAML for config loading.
- Repository tree: isolated local-only package rooted at
  `projects/working/bond/no_time_to_die`; a local path dependency on the frozen
  `bond-api` protocol.

## Deterministic demonstration parameters

Canonical inputs live in `src/no_time_to_die/demo.py` and
`manuscript/config.yaml`:

| Parameter | Value |
| --- | --- |
| Reference genome length | 64 nt (periodic 16-mer) |
| Guide candidates | {{HERACLES_NUM_GUIDES}} |
| Off-target tolerance `k` | 2 |
| Absorption rate `k_a` | 1.2 h⁻¹ |
| Exposure time | 4.0 h |
| Avidity | 3.0 |
| Antidote antagonist concentration | 10.0 mg/L |
| Exposure pathway (conc/rate/duration/absorbed/elim) | 0.02 / 0.5 / 30 / 0.2 / 0.1 |
| Seed | 11 |
| Limit-of-detection SNR | {{HERACLES_LOD_SNR}} |
| Catalog flora | {{HERACLES_NUM_TOXINS}} |
| Forensic library | {{HERACLES_NUM_LIBRARY}} |

All are fixed at import; no run consumes wall-clock or random state, so
results are byte-reproducible.

## Figure generation

Figures are rendered deterministically by `src/no_time_to_die/figures/plots.py`
under a headless `Agg` backend to `output/figures/`:

- `delivery_kinetics.png` — bateman plasma-concentration curve.
- `toxicology_dose_response.png` — Hill curves for the full catalog.
- `guide_efficiency.png` — guide-design efficiency vs GC content.
- `antidote_response.png` — competitive-antagonist dose–response.
- `detection_confidence.png` — logistic detection confidence vs SNR.
