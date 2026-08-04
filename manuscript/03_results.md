# Results

All results below are computed live from `src/no_time_to_die/demo.py` by
`src/no_time_to_die/manuscript_variables.py`; none are hand-authored. The
deterministic demonstration uses a fixed 64-nucleotide periodic reference, a
guide set, `seed = 11`, and a fixed exposure window.

## Countermeasure demonstration

`select_best_guide` selects guide `{{HERACLES_BEST_GUIDE}}`, which attains a
target specificity of **{{HERACLES_SPECIFICITY}}%** with zero off-target near
matches in the demonstration reference. Combined with the delivered fraction
and a saturating avidity term, the HERACLES neutralization probability is
**{{HERACLES_NEUTRALIZATION}}%**.

The delivery kinetics (one-compartment bateman model) are rendered in
[Figure @fig:delivery].

![HERACLES one-compartment delivery kinetics over a 12 h exposure
window.](../output/figures/delivery_kinetics.png){#fig:delivery}

## Poison-garden catalog

The `{{HERACLES_NUM_TOXINS}}`-toxin catalog spans median LD50
{{HERACLES_MEDIAN_LD50}} mg/kg. Dose–response curves for every flora member are
rendered in [Figure @fig:toxicology]. A garden-risk mixture of ricin, nicotine,
and cyanide combines under response addition.

![Poison-garden Hill dose–response curves across the catalog
flora.](../output/figures/toxicology_dose_response.png){#fig:toxicology}

## Vesper trace forensics

At a limit-of-detection SNR of `{{HERACLES_LOD_SNR}}`, the demonstration signal
is detected with high confidence; the back-computed, transfer-corrected residue
dose is **{{HERACLES_RECOVERED_DOSE}}** (arbitrary mass units) on the glass.
Spectral matching identifies the residue's top match against the
`{{HERACLES_NUM_LIBRARY}}`-entry reference library. Detection confidence vs
signal-to-noise is rendered in [Figure @fig:detection].

![Vesper trace detection confidence vs signal-to-noise against the
limit of detection.](../output/figures/detection_confidence.png){#fig:detection}
