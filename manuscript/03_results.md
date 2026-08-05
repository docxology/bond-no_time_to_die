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

## Guide-design ranking

Across the `{{HERACLES_NUM_GUIDES}}` demonstration candidates, `design_report`
selects guide `{{HERACLES_BEST_GUIDE}}` with an efficiency score of
**{{HERACLES_BEST_GUIDE_SCORE}}%** and a population off-target risk of
**{{HERACLES_POP_OFFTARGET}}** over the reference genome. The efficiency
landscape (vs GC content) is rendered in [Figure @fig:guidance].

![HERACLES guide-design efficiency across the candidate
set.](../output/figures/guide_efficiency.png){#fig:guidance}

## Poison-garden catalog

The `{{HERACLES_NUM_TOXINS}}`-toxin catalog spans median LD50
{{HERACLES_MEDIAN_LD50}} mg/kg. Dose–response curves for every flora member are
rendered in [Figure @fig:toxicology]. A garden-risk mixture of ricin, nicotine,
and cyanide combines under response addition.

![Poison-garden Hill dose–response curves across the catalog
flora.](../output/figures/toxicology_dose_response.png){#fig:toxicology}

## Antidote screen

Against a ricin dose, the `{{HERACLES_ANTIDOTE_COUNT}}`-antidote library is
ranked by restored survival. The best antidote is **{{HERACLES_BEST_ANTIDOTE}}**,
restoring a survival probability of **{{HERACLES_SURVIVAL_PCT}}%** by
antagonizing **{{HERACLES_ANTAGONIZED_PCT}}%** of the toxin's receptor
occupancy. The competitive-antagonist dose–response for the library is rendered
in [Figure @fig:antidote].

![Competitive-antagonist antidote response
curves.](../output/figures/antidote_response.png){#fig:antidote}

## Exposure assessment

For the demonstration Vesper pathway, the absorbed dose is
**{{HERACLES_ABSORBED_DOSE}}** (mass units), a cumulative body burden of
**{{HERACLES_CUMULATIVE}}**, a margin of exposure of **{{HERACLES_MOE}}**, and a
risk quotient of **{{HERACLES_RQ}}** against the reference dose — a verdict of
**{{HERACLES_EXPOSURE_VERDICT}}**.

## Vesper trace forensics

At a limit-of-detection SNR of `{{HERACLES_LOD_SNR}}`, the demonstration signal
is detected with high confidence; the back-computed, transfer-corrected residue
dose is **{{HERACLES_RECOVERED_DOSE}}** (arbitrary mass units) on the glass.
Spectral matching identifies the residue's top match against the
`{{HERACLES_NUM_LIBRARY}}`-entry reference library. Detection confidence vs
signal-to-noise is rendered in [Figure @fig:detection].

![Vesper trace detection confidence vs signal-to-noise against the
limit of detection.](../output/figures/detection_confidence.png){#fig:detection}
