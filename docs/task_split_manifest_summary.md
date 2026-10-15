# October Split Design and Manifest — Completion Summary

## Work completed

Implemented an immutable, reproducible **proposed** partition manifest and train/validation diagnostics on the approved source. All 188,318 rows pass the source contract and eligibility checks; **0 rows are excluded**, with no exclusion reasons. No rows/features/categories were removed. The implementation follows the current October artifact layout and leaves September evidence and the notebook unchanged.

The branch incorporates merged advisor guidance at `d3b6a8be02d1045eb3dd5f1e7d08753177daa348`. October 13 guidance calls for an untouched test set and cross-validation within training; exact proportions and folds remain for team approval. The task-authorized fallback is materialized for review, not presented as advisor-approved.

## Split design

Version `october-split-v1`; **75% train / 15% validation / 10% internal test, seed 42**. Deterministic SHA-256 seeded ranking of canonical unique claim IDs; largest-remainder rounding; manifest serialized in ascending integer ID order. Assignment depends on IDs and declared configuration only, never loss or predictors. See [design and change criteria](october_split_design.md).

| Partition | Claims | Share of eligible population |
| :--- | ---: | ---: |
| train | 141,238 | 74.999734% |
| validation | 28,248 | 15.000159% |
| test | 18,832 | 10.000106% |

Training contains future CV/tuning; validation is a separate development check; test stays sealed until the final candidate and selection procedure are fixed and access is authorized. Global pre-assignment target access is limited to mandatory numeric/finite/positive eligibility predicates. Test target values are not retained or converted in the post-assignment diagnostics pass.

## Artifacts

- [october_partition_manifest.csv](../artifacts/october/gate%201/october_partition_manifest.csv): 188,318 rows; only `id` and `partition`, no target/predictors; approximately 2.5 MB, permitted by repository policy.
- [october_split_diagnostics.csv](../artifacts/october/gate%201/october_split_diagnostics.csv): all partition counts/shares; train/validation-only raw target summaries and high-loss support.
- [october_categorical_coverage.csv](../artifacts/october/gate%201/october_categorical_coverage.csv): all 116 predictors, unseen labels/support and separate training/validation-local EDA rarity.
- [october_split_metadata.json](../artifacts/october/gate%201/october_split_metadata.json): source, dictionary, configuration/code and output hashes; eligibility, runtime, actual checks and sealed-test policy.
- [create_partition_manifest.py](../scripts/create_partition_manifest.py): separate verification, eligibility, assignment, validation, diagnostic and export functions.
- [test_partition_manifest.py](../tests/test_partition_manifest.py): nine behavioral tests for integrity, determinism, row-order invariance, rare support boundaries, test-target isolation and overwrite refusal.
- [october_split_design.md](october_split_design.md): rationale, constraints, approval status, change criteria and reproduction/handoff instructions.
- `docs/task_split_manifest_summary.md`: this generated-evidence completion summary.

Manifest SHA-256: `18e69673953fa61cbbabdd0421e83d31bd46b6f93356a2227793c6013e0850f1`.
Source SHA-256: `74037cb248a1064e4d578692a4f4e5d8492ed1b2033daf643496e1b68b14ae03`.

## Validation results

All eligible IDs appear exactly once; no overlaps, omissions or unknown IDs. Independent ID-only reconciliation against the source and serialized output-hash checks passed. Counts sum to 188,318 and each differs from its ideal proportion by less than one claim. A second full execution reproduced identical artifacts; reversed eligible-ID order reproduces identical manifest bytes. Different existing artifacts are rejected before any writes.

Nine unit tests passed, including a test that replaces test loss strings with nonnumeric poison and verifies development diagnostics are unchanged. The test-access assertion means no test target diagnostics after assignment; it does not pretend that the shared CSV is physically inaccessible or that September never saw these claims.

- Authoritative source verified: PASS
- Categorical coverage documented: PASS
- Eligibility rules documented: PASS
- Every eligible claim assigned exactly once: PASS
- Field roles verified: PASS
- High-loss support documented: PASS
- Internal test decision documented: PASS
- No omitted eligible claims: PASS
- No partition overlap: PASS
- Partition counts reconcile: PASS
- Proportions documented: PASS
- Reproducibility confirmed: PASS
- Seed documented: PASS
- Source dataset unchanged: PASS
- Split design documented: PASS
- Split-change criteria documented: PASS
- Test targets remain uninspected: PASS
- Train/validation target summaries generated: PASS

## Key diagnostics

Raw loss units, calculated only for training and validation:

| Statistic | Train (n=141,238) | Validation (n=28,248) |
| :--- | ---: | ---: |
| Mean | 3,038.30 | 3,032.02 |
| Median | 2,116.66 | 2,120.02 |
| Sample standard deviation | 2,909.75 | 2,858.75 |
| 90th percentile | 6,400.17 | 6,398.21 |
| 95th percentile | 8,511.92 | 8,483.15 |
| 99th percentile | 13,900.78 | 14,084.34 |
| Maximum | 121,012.25 | 54,190.39 |

Using the archived September p95 threshold **loss > 8,508.5365**, high-loss support is **7,071 / 141,238 (5.0064%)** in training and **1,405 / 28,248 (4.9738%)** in validation. This historical full-file EDA threshold is not recalculated from test data or used to select assignments; any learned modeling threshold must use training only.

There are **6 fields with 12 field-specific validation levels unseen in training**:

| Feature | Unseen levels | Validation observations / denominator | Share |
| :--- | ---: | ---: | ---: |
| cat105 | 1 | 1 / 28,248 | 0.003540% |
| cat107 | 1 | 1 / 28,248 | 0.003540% |
| cat109 | 1 | 1 / 28,248 | 0.003540% |
| cat110 | 1 | 1 / 28,248 | 0.003540% |
| cat114 | 1 | 1 / 28,248 | 0.003540% |
| cat116 | 7 | 8 / 28,248 | 0.028321% |

These are ordinary category-coverage findings, not reasons to resplit or remove rows. Counts across fields can overlap and are not distinct-claim totals. The complete coverage CSV reports support <100 as the inherited September EDA rule, separately from future modeling choices; no encoder or grouping is fitted.

## Assumptions and limitations

- The design is **PROPOSED** until team approval: confirm the 75/15/10 allocation, additional validation partition, training-only CV fold construction and test release process. No approved numeric proportions were found in the merged guidance.
- Anonymous predictors provide no confirmed time/group key. Unique IDs do not prove independent entities; seek advisor confirmation of grouping and temporal requirements before modeling.
- September EDA already exposed the whole labeled file. This internal test is sealed for October development, not historically unseen or a separate future-period evaluation.
- Historical manifest paths were left unchanged after repository reorganization; reference files are resolved under `artifacts/september/` and verified against their preserved hashes. The old handoff validator still points to historical paths and was not changed or represented as passing.
- Current pandas/NumPy/Python versions are recorded in metadata. No additional packages were installed. Seeded hash assignments do not depend on a library RNG; diagnostics should be reproduced in the recorded environment.
- No split was changed in response to target distributions or model results. Only predeclared, documented and approved criteria permit a new version; never overwrite this manifest to hide a revision.

## Future modeling handoff

Run `python3 scripts/create_partition_manifest.py` and `python3 -m unittest discover -s tests -p 'test_partition_manifest.py' -v`. Modeling code must verify the manifest hash, join on unique `id` with one-to-one validation, and preserve these exact IDs. Load train/validation targets only after selecting their IDs. Keep all learned preprocessing and any CV/tuning within training; score original-scale MAE against both training-only constant baselines later. Do not independently resplit or access test targets before the approved final-evaluation step.

## Work not performed

No models or baselines trained, no encoders fitted, no hyperparameters tuned, no features selected, no category/row removal, and **no test-target distribution, high-loss, or performance analysis**. The source file is unchanged. This work does not approve the split, decide CV folds, select a model or merge the PR.
