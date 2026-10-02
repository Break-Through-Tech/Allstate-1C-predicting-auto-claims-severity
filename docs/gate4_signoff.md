### Gate 4 Sign-Off — September Complete

**Status:** DRAFT — complete the items marked ☐ before the Team Readiness Review.

#### Task 1 — Final Artifact Bundle and traceability

**Official run**

| Item | Value |
| :--- | :--- |
| Workflow Run ID | `WR-SEPT-G4-20261002T205412Z-03140d1` |
| Code revision | `03140d1e665bdb331bccad20cc7a93d1fbe0148a` |
| September Artifact Bundle ID | `SEPT-BUNDLE-78876ab8c12d` |
| Source | `data/allstate_claims_data.csv` · SHA-256 `74037cb248a1064e4d578692a4f4e5d8492ed1b2033daf643496e1b68b14ae03` |
| Code-cell hash | `67d4749eb00f7e13f0d6f8fd8247f565031bd3777b87b0b956d5d7fda84f28ac` |
| Configuration hash | `9dca91702e86217139cf1cd8031358a2842a2fdd84c259d855442e9d9b2bd0ca` |
| Manifest | `artifacts/artifact_manifest.json` |
| Run environment | VS Code · Python 3.13.16 · macOS arm64 · pandas 2.3.2, numpy 2.3.3, scipy 1.18.1, matplotlib 3.11.2, seaborn 0.13.2 · 2026-10-02 20:54 UTC |

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

- [x] All regenerated artifacts reproduce the committed versions
- [x] Dictionary unique and missing counts = source profile, for all 132 fields
- [x] Categorical cardinalities and continuous unique counts, minimums, and maximums = source profile
- [x] Target table = Gate 3 verification values (mean 3,037.34; median 2,115.57; p95 8,508.54; max 121,012.25; skewness 3.795)
- [x] All 45 findings-register values reproduced, and every evidence link exists
- [x] Every derived field documented in the dictionary
- [x] Independent recalculation matches
- [x] Saved notebook outputs and figures come from the official run (G4-WF-010)

**Open before Task 1 can close**

- [ ] Gate 3 independent review completed (`T4_REVIEW_ASSIGNMENTS`), so the bundle's review records are complete
- [x] Official Gate 4 run recorded above, with the executed notebook committed (G4-WF-010)

#### Gate 4 Run Receipt

```json
{
  "workflow_run_id": "WR-SEPT-G4-20261002T205412Z-03140d1",
  "status": "COMPLETED WITH WARNINGS",
  "official_gate4_run": true,
  "run_utc": "2026-10-02T20:54:12+00:00",
  "code_revision": "03140d1e665bdb331bccad20cc7a93d1fbe0148a",
  "clean_at_start": true,
  "source_sha256": "74037cb248a1064e4d578692a4f4e5d8492ed1b2033daf643496e1b68b14ae03",
  "code_cells_sha256": "67d4749eb00f7e13f0d6f8fd8247f565031bd3777b87b0b956d5d7fda84f28ac",
  "configuration_sha256": "9dca91702e86217139cf1cd8031358a2842a2fdd84c259d855442e9d9b2bd0ca",
  "runtime": {
    "python": "3.13.16",
    "platform": "macOS-26.5.2-arm64-arm-64bit-Mach-O"
  },
  "dependencies": {
    "matplotlib": "3.11.2",
    "numpy": "2.3.3",
    "pandas": "2.3.2",
    "scipy": "1.18.1",
    "seaborn": "0.13.2"
  },
  "traceability_checks": "all passed",
  "reproduction": {
    "artifacts/source_profile.csv": "exact",
    "artifacts/data_dictionary_v1.1.0.csv": "exact",
    "artifacts/categorical_cardinality_verification.csv": "exact",
    "artifacts/categorical_dominance_evidence.csv": "exact",
    "artifacts/categorical_high_cardinality_evidence.csv": "exact",
    "artifacts/categorical_inventory.csv": "exact",
    "artifacts/categorical_level_target.csv": "exact",
    "artifacts/categorical_low_support_evidence.csv": "exact",
    "artifacts/categorical_starting_checks.csv": "exact",
    "artifacts/categorical_target_evidence.csv": "exact",
    "artifacts/continuous_inventory.csv": "exact",
    "artifacts/continuous_bin_target.csv": "exact",
    "artifacts/target_summary.csv": "exact",
    "artifacts/artifact_manifest.json": "exact"
  },
  "september_artifact_bundle_id": "SEPT-BUNDLE-78876ab8c12d",
  "problems": [],
  "warnings": [
    "independent review incomplete (PENDING or not independent)"
  ]
}
```