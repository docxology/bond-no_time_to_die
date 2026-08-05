# Results

All results below are computed live from `src/no_time_to_die/demo.py` by
`src/no_time_to_die/manuscript_variables.py`; none are hand-authored. The
deterministic demonstration uses a fixed {{HERACLES_REFERENCE_LENGTH}}-nucleotide
periodic reference, a {{HERACLES_NUM_GUIDES}}-guide candidate set, seed
`{{HERACLES_SEED}}`, and a fixed {{HERACLES_EXPOSURE_TIME}} h exposure window
(canonical input digest `{{HERACLES_INPUT_HASH}}`).

## Countermeasure demonstration

`select_best_guide` selects guide `{{HERACLES_BEST_GUIDE}}`
({{HERACLES_GUIDE_LENGTH}} nt), which attains a target specificity of
**{{HERACLES_SPECIFICITY}}%** — **{{HERACLES_ON_TARGET}}** on-target windows
against **{{HERACLES_OFF_TARGET}}** off-target near matches (within
{{HERACLES_MAX_MISMATCHES}} mismatches) in the demonstration reference.
Combined with a delivered fraction of **{{HERACLES_DELIVERED_PCT}}%** and a
saturating avidity term (avidity {{HERACLES_AVIDITY}}), the HERACLES
neutralization probability is **{{HERACLES_NEUTRALIZATION}}%**.

The delivery kinetics (one-compartment bateman model) are rendered in
[Figure @fig:delivery].

![HERACLES one-compartment delivery kinetics over a
{{HERACLES_DELIVERY_HORIZON_H}} h horizon (absorption rate
{{HERACLES_ABSORPTION_RATE}} h⁻¹, elimination rate
{{HERACLES_DELIVERY_ELIM_RATE}} h⁻¹), with the
{{HERACLES_EXPOSURE_TIME}} h exposure window
marked.](../output/figures/delivery_kinetics.png){#fig:delivery}

## Guide-design ranking

Across the `{{HERACLES_NUM_GUIDES}}` demonstration candidates, `design_report`
selects guide `{{HERACLES_BEST_GUIDE}}` with an efficiency score of
**{{HERACLES_BEST_GUIDE_SCORE}}%** and a population off-target risk of
**{{HERACLES_POP_OFFTARGET}}** over the reference genome. The efficiency
landscape (vs GC content) is rendered in [Figure @fig:guidance].

![HERACLES guide-design efficiency across the candidate
set.](../output/figures/guide_efficiency.png){#fig:guidance}

## Poison-garden catalog

The `{{HERACLES_NUM_TOXINS}}`-toxin catalog spans LD50 {{HERACLES_MIN_LD50}} to
{{HERACLES_MAX_LD50}} mg/kg, median {{HERACLES_MEDIAN_LD50}} mg/kg.
Dose–response curves for every flora member are rendered in
[Figure @fig:toxicology]. A garden-risk mixture of ricin, nicotine, and cyanide
combines under response addition to affect **{{HERACLES_GARDEN_RISK_PCT}}%** of
an exposed population.

![Poison-garden Hill dose–response curves across the catalog
flora.](../output/figures/toxicology_dose_response.png){#fig:toxicology}

## Antidote screen

Against a ricin dose at an antagonist concentration of
{{HERACLES_ANTAGONIST_CONC}} mg/L, the `{{HERACLES_ANTIDOTE_COUNT}}`-antidote
library is ranked by restored survival. The best antidote is
**{{HERACLES_BEST_ANTIDOTE}}**, restoring a survival probability of
**{{HERACLES_SURVIVAL_PCT}}%** by antagonizing **{{HERACLES_ANTAGONIZED_PCT}}%**
of the toxin's receptor occupancy. The competitive-antagonist dose–response for
the library is rendered in [Figure @fig:antidote].

![Competitive-antagonist antidote response
curves.](../output/figures/antidote_response.png){#fig:antidote}

## Exposure assessment

For the demonstration Vesper pathway, the absorbed dose is
**{{HERACLES_ABSORBED_DOSE}}** (mass units), a cumulative body burden of
**{{HERACLES_CUMULATIVE}}**, a margin of exposure of **{{HERACLES_MOE}}**, and a
risk quotient of **{{HERACLES_RQ}}** against the reference dose
{{HERACLES_EXP_RFD}} — a verdict of **{{HERACLES_EXPOSURE_VERDICT}}**. The
margin of exposure exceeds unity against the NOAEL {{HERACLES_EXP_NOAEL}} while
the risk quotient does not, which is precisely the discordance the verdict rule
is written to catch: an intake far below the lethality threshold can still sit
far above the reference dose.

## Vesper trace forensics

At a limit-of-detection SNR of `{{HERACLES_LOD_SNR}}`, the demonstration signal
({{HERACLES_FOR_SIGNAL}} against RMS noise {{HERACLES_FOR_NOISE}}, giving SNR
**{{HERACLES_SNR}}**) is detected with **{{HERACLES_DETECTION_CONFIDENCE_PCT}}%**
confidence. The calibration model back-computes a residue concentration of
**{{HERACLES_CONCENTRATION}}**, and applying the
{{HERACLES_FOR_TRANSFER}} transfer fraction over {{HERACLES_FOR_VOLUME}} mL
gives a transfer-corrected residue dose of **{{HERACLES_RECOVERED_DOSE}}**
(arbitrary mass units) on the glass. Spectral matching against the
`{{HERACLES_NUM_LIBRARY}}`-entry reference library identifies the residue as
**{{HERACLES_TOP_MATCH}}**. Detection confidence vs signal-to-noise is rendered
in [Figure @fig:detection].

![Vesper trace detection confidence vs signal-to-noise against the
limit of detection.](../output/figures/detection_confidence.png){#fig:detection}
