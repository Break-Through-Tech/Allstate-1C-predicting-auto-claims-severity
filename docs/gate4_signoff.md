### Gate 4 Sign-Off — September Complete

**Status:** DRAFT — complete the items marked ☐ before the Team Readiness Review.

#### Task 1 — Final Artifact Bundle and traceability

**Official run**

| Item | Value |
| :--- | :--- |
| Workflow Run ID | ☐ `WR-SEPT-G4-…` (from the Gate 4 Run Receipt, last notebook cell) |
| Code revision | ☐ commit SHA from the receipt |
| September Artifact Bundle ID | ☐ `SEPT-BUNDLE-…` |
| Source | `data/allstate_claims_data.csv` · SHA-256 `74037cb248a1064e4d578692a4f4e5d8492ed1b2033daf643496e1b68b14ae03` |
| Code-cell hash | ☐ `code_cells_sha256` from the receipt |
| Configuration hash | ☐ `configuration_sha256` from the receipt |
| Manifest | `artifacts/artifact_manifest.json` |

**Bundle contents** (each item is also listed under `required_contents` in the manifest)

| Required item | Location |
| :--- | :--- |
| Source identity and manifest | `data/allstate_claims_data.csv` (SHA-256 above); `artifacts/artifact_manifest.json` |
| Plain-language analysis contract | `notebooks/data-understanding.ipynb`, Gate 2 Task 1 |
| Project-specific data dictionary | `artifacts/data_dictionary_v1.1.0.csv` (v1.0.0 kept as the version approved at Gate 2) |
| Anomaly register | `docs/anomaly_register.md` |
| Reproducible EDA notebook | `notebooks/data-understanding.ipynb`; `requirements.txt` |
| Data-quality and field-profile tables | `artifacts/source_profile.csv` |
| Target-distribution tables and figures | `artifacts/target_summary.csv`; figures in the notebook, Gate 2 Task 1 |
| Categorical cardinality, support, and target-effect evidence | `artifacts/categorical_*.csv` (8 files) |
| Continuous distribution, binned-target, and correlation evidence | `artifacts/continuous_inventory.csv`; `artifacts/continuous_bin_target.csv`; figures in the notebook, Gate 3 Task 4 |
| Findings register | `docs/findings_register.md` |
| Independent-review records | `docs/gate1_signoff.md`; `docs/gate2_signoff.md`; `docs/gate3_signoff.md`; `artifacts/categorical_cardinality_verification.csv`; reviewer section in the notebook, Gate 3 Task 4 |
| Reproduction instructions | `README.md`, Setup and Installation |

**Traceability** (checked by the notebook on every run; all must pass)

- [ ] All regenerated artifacts reproduce the committed versions
- [ ] Dictionary unique and missing counts = source profile, for all 132 fields
- [ ] Categorical cardinalities and continuous unique counts, minimums, and maximums = source profile
- [ ] Target table = Gate 3 verification values (mean 3,037.34; median 2,115.57; p95 8,508.54; max 121,012.25; skewness 3.795)
- [ ] All 45 findings-register values reproduced, and every evidence link exists
- [ ] Every derived field documented in the dictionary
- [ ] Independent recalculation matches
- [ ] Saved notebook outputs and figures come from the official run (G4-WF-010)

**Open before Task 1 can close**

- [ ] Gate 3 independent review completed (`T4_REVIEW_ASSIGNMENTS`), so the bundle's review records are complete
- [ ] Official Gate 4 run recorded above, with the executed notebook committed (G4-WF-010)

#### Gate 4 Run Receipt

☐ Paste the JSON receipt printed by the last notebook cell of the official run here.