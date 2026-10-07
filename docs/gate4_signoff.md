### Gate 4 Sign-Off — September Complete

**Status:** APPROVED — full-team handoff completed on 2026-10-06.

#### Task 1 — Final Artifact Bundle and traceability

**Official run**

| Item | Value |
| :--- | :--- |
| Workflow Run ID | `WR-SEPT-G4-20261006T200457Z-b5c2b8e` |
| Code revision | `b5c2b8e11236ddb25930406573a99ca3c58758e6` |
| September Artifact Bundle ID | `SEPT-BUNDLE-b45bed5c989c` |
| Source | `data/allstate_claims_data.csv` · SHA-256 `74037cb248a1064e4d578692a4f4e5d8492ed1b2033daf643496e1b68b14ae03` |
| Code-cell hash | `d05ccb2d8739ff6ac524106539ed19f57fa592b60416cf3f0b7f4c235dc0f8df` |
| Configuration hash | `9dca91702e86217139cf1cd8031358a2842a2fdd84c259d855442e9d9b2bd0ca` |
| Manifest | `artifacts/artifact_manifest.json` |
| Run environment | VS Code · Python 3.13.2 · macOS arm64 · pandas 2.3.2, numpy 2.3.3, scipy 1.18.1, matplotlib 3.11.2, seaborn 0.13.2 · 2026-10-06 20:04:57 UTC |
| Status | `SUCCESS` |
| Official Gate 4 run | `true` |
| Clean at start | `true` |
| Problems | `[]` |
| Warnings | `[]` |

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

- [x] Gate 3 independent review completed (`T4_REVIEW_ASSIGNMENTS`), so the bundle's review records are complete
- [x] Official Gate 4 run recorded above, with the executed notebook committed (G4-WF-010)

#### Gate 4 Run Receipt

```json
{
  "workflow_run_id": "WR-SEPT-G4-20261006T200457Z-b5c2b8e",
  "status": "SUCCESS",
  "official_gate4_run": true,
  "run_utc": "2026-10-06T20:04:57+00:00",
  "code_revision": "b5c2b8e11236ddb25930406573a99ca3c58758e6",
  "clean_at_start": true,
  "source_sha256": "74037cb248a1064e4d578692a4f4e5d8492ed1b2033daf643496e1b68b14ae03",
  "code_cells_sha256": "d05ccb2d8739ff6ac524106539ed19f57fa592b60416cf3f0b7f4c235dc0f8df",
  "configuration_sha256": "9dca91702e86217139cf1cd8031358a2842a2fdd84c259d855442e9d9b2bd0ca",
  "runtime": {
    "python": "3.13.2",
    "platform": "macOS-27.0.1-arm64-arm-64bit-Mach-O"
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
  "september_artifact_bundle_id": "SEPT-BUNDLE-b45bed5c989c",
  "problems": [],
  "warnings": []
}
```

#### Task 4 — Independent verification, final handoff, and retrospective

##### Independent verification

- [x] Independent reviewers recalculated evidence from the locked source and configuration.
- [x] All reviewer calculations matched the primary results within the recorded tolerances.
- [x] Every reviewer was independent of the evidence they reviewed.
- [x] The final workflow ran from a clean committed revision using the pinned dependencies.
- [x] Every regenerated artifact reproduced the committed version exactly.
- [x] The final run completed with no problems or warnings.

| Evidence reviewed | Reviewer | Checks | Matches | Independent |
| :--- | :--- | ---: | ---: | :---: |
| Target summary | Hector Baeza | 13 | 13 | Yes |
| Categorical cardinalities including `cat116` | Hector Baeza | 9 | 9 | Yes |
| Continuous-to-target correlations | Krish Patel | 14 | 14 | Yes |
| Three strongest continuous pairs | Leng Lim | 3 | 3 | Yes |
| Headline findings FND-001, FND-005, FND-006, and FND-008 | Hector Baeza | 7 | 7 | Yes |

**Final verified evidence**

| Item | Value |
| :--- | :--- |
| Workflow Run ID | `WR-SEPT-G4-20261006T200457Z-b5c2b8e` |
| September Artifact Bundle ID | `SEPT-BUNDLE-b45bed5c989c` |
| Source SHA-256 | `74037cb248a1064e4d578692a4f4e5d8492ed1b2033daf643496e1b68b14ae03` |
| Code-cell SHA-256 | `d05ccb2d8739ff6ac524106539ed19f57fa592b60416cf3f0b7f4c235dc0f8df` |
| Configuration SHA-256 | `9dca91702e86217139cf1cd8031358a2842a2fdd84c259d855442e9d9b2bd0ca` |
| Result | `SUCCESS` with no problems or warnings |

##### Evidence preservation

- [x] The manifest, Workflow Run receipt, hashes, anomaly register, decisions, deviations, and reproduction instructions are preserved on the shared repository branch.
- [x] The required evidence is accessible in the team’s GitHub repository. The coach and Challenge Advisor were notified that our team is not using Google Colab.
- [x] Confirm that every team member, the coach, and the Challenge Advisor can access the approved handoff evidence.

##### Full-team handoff

- [x] Present the verified September Artifact Bundle to the full team.
- [x] Record approvals, dissent, unresolved risks, and work explicitly deferred to October.

| Member | Role | Approves Y or N | Date | Comment |
| :--- | :--- | :---: | :--- | :--- |
| Rachel Cheung | Fellow | Y | 2026-10-06 |  |
| Leng Lim | Fellow | Y | 2026-10-06 |  |
| Krish Patel | Fellow | Y | 2026-10-06 |  |
| Hector Baeza | Fellow | Y | 2026-10-06 |  |

**Dissent and unresolved risks**

**Dissent:** No dissent was raised during the full-team handoff.

**Unresolved risks:**

| Topic | Description | Risk | Status or October response |
| :--- | :--- | :--- | :--- |
| Anonymous predictors | The team cannot connect `cat*` and `cont*` fields to confirmed business concepts. | Interpretations could assign meanings the data does not support. | Acknowledged; do not assign unsupported business meanings during modeling or interpretation. |
| High-cardinality and unseen categories | Some categorical fields contain many or rare levels. | Encoding could overfit or leak validation information. | Open; fit encoders using training data only and define handling for unseen levels. |
| Sparse high-loss claims | Large claims are uncommon but economically important. | Overall model results could be influenced by a relatively small number of extreme claims. | Open; retain valid claims and evaluate errors across loss ranges during October validation. |


**Work explicitly deferred to October**

| Work item | September evidence | October decision or experiment |
|---|---|---|
| Establish held-out baselines | Long-tailed `loss` distribution and MAE requirement | Fit mean- and median-constant baselines using training data only; evaluate on untouched validation data |
| Compare candidate model families | Weak marginal relationships and nonlinear binned patterns | Compare GLM and tree-based models using original-scale validation MAE without preselecting a winner |
| Test categorical encoding | High-cardinality and rare levels in fields such as `cat116` | Compare leakage-safe encoding methods fitted only on training data |
| Handle unseen and rare categories | Rare-level support evidence | Define and validate a rule for categories absent from training or insufficiently supported |
| Evaluate correlated predictors | Strong `cont11`–`cont12`, `cont1`–`cont9`, and `cont6`–`cont10` correlations | Test their effect on linear-model stability and held-out performance before removing anything |
| Perform feature interpretation | Anonymous predictors and lack of established feature importance | Use model-specific interpretation only after a model is properly validated; do not assign unsupported business meanings |
| Tune model settings | Modeling and tuning were prohibited before Gate 4 approval | Tune only within training folds after the evaluation design is frozen |

##### Team retrospective

- [x] **Practice to keep:** Use reproducible workflow runs, versioned artifacts, and independent reviewers before approving important findings.
- [x] **Practice to change:** Assign evidence reviewers when work is assigned instead of waiting until the final gate, reducing last-minute coordination.
- [x] **Experiment to try:** Add a pull-request checklist or automated check that verifies the manifest, hashes, dependency versions, and reviewer assignments before merge.
- [x] **Lesson about responsibly interpreting anonymous insurance-claim data:** Anonymous features support statements about observed associations, but they do not justify causal claims or assumed business meanings; extreme losses should not be discarded merely because they are unusual.

- [x] Confirm that no speculative October implementation tickets were created before approval of this handoff.

**Gate 4 Task 4 verdict:** Approved by the full team on 2026-10-06. Independent verification, evidence preservation, handoff decisions, deferred October work, and the retrospective are complete.
