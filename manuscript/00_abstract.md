# Abstract

{{HERACLES_TITLE}} — mission codename **{{HERACLES_CODENAME}}** — reduces the
three pharmaco-forensic concepts of *No Time to Die* (2021) to deterministic,
tested mathematics with a shared provenance ledger. The pure domain core in
`src/no_time_to_die/` comprises three modules: a DNA-targeted bioweapon
countermeasure model (Heracles target specificity and delivery kinetics), a
poison-garden toxicology dose–response catalog, and poison-delivery forensics
for trace detection on the Vesper's glass. A thin adapter binds that core to
the frozen bond-api mission protocol so the film is discoverable and drivable
by the BOND suite orchestrator.

The poison-garden catalog profiles **{{HERACLES_NUM_TOXINS}}** flora toxins
with published-approximation LD50 values and Hill slopes, spanning
{{HERACLES_MIN_LD50}} to {{HERACLES_MEDIAN_LD50}} mg/kg across the median. The
HERACLES countermeasure demonstration selects a target guide that attains
{{HERACLES_SPECIFICITY}}% specificity and a combined neutralization
probability of {{HERACLES_NEUTRALIZATION}}%. Forensic trace detection clears a
limit-of-detection signal-to-noise ratio of {{HERACLES_LOD_SNR}}, recovering a
dosable residue from the glass.

The entire assessment is deterministic (fixed seed, no random draws, no
wall-clock dependence) and reproduced under Python {{PYTHON_VERSION}}, satisfying
the suite's coverage, mock-free, and lineage gates.
