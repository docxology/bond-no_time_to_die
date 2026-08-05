# Abstract

{{HERACLES_TITLE}} — mission codename **{{HERACLES_CODENAME}}** — reduces the
pharmaco-forensic threats of *No Time to Die* (2021) to deterministic, tested
mathematics with a shared provenance ledger. The pure domain core in
`src/no_time_to_die/` comprises **{{HERACLES_NUM_MODULES}}** modules spanning
three threat families: a DNA-targeted bioweapon countermeasure (target
specificity, guide design, and delivery kinetics), poison-garden toxicology
(dose–response and competitive-antagonist pharmacology), and poison-delivery
forensics (exposure assessment and trace detection on the Vesper's glass). A
thin adapter binds that core to the frozen bond-api mission protocol so the
film is discoverable and drivable by the BOND suite orchestrator.

The poison-garden catalog profiles **{{HERACLES_NUM_TOXINS}}** flora toxins
spanning {{HERACLES_MIN_LD50}} to {{HERACLES_MAX_LD50}} mg/kg (median
{{HERACLES_MEDIAN_LD50}}) — commonly-cited order-of-magnitude LD50 figures
paired with invented Hill slopes. The HERACLES countermeasure demonstration
selects a target guide that attains {{HERACLES_SPECIFICITY}}% specificity
against a constructed reference genome with a planted, documented structure, and
a combined neutralization probability of {{HERACLES_NEUTRALIZATION}}%. Guide
design ranks {{HERACLES_NUM_GUIDES}} candidates by a Doench-style efficiency
blended with population off-target burden; a screen over five invented
inhibition constants restores {{HERACLES_SURVIVAL_PCT}}% survival against a
ricin dose; and the delivered
exposure carries a margin of exposure of {{HERACLES_MOE}} (risk quotient
{{HERACLES_RQ}}) — a verdict of {{HERACLES_EXPOSURE_VERDICT}}. Forensic trace
detection clears a limit-of-detection signal-to-noise ratio of
{{HERACLES_LOD_SNR}} at an observed SNR of {{HERACLES_SNR}}, recovering a
dosable residue from the glass and identifying it as {{HERACLES_TOP_MATCH}}.

The entire assessment is deterministic — no module imports a clock or an RNG,
the canonical input digest is `{{HERACLES_INPUT_HASH}}`, and two runs on one
interpreter render byte-identical artifacts — and it is reproduced under Python
{{PYTHON_VERSION}}, satisfying the suite's coverage, mock-free, and lineage
gates. Every constant is registered with its provenance class in
`data/claim_ledger.yaml`; none is a measurement.
