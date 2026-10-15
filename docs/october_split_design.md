# October Split Design and Partition Manifest

**Version:** `october-split-v1` · **Status: PROPOSED partition artifact for team review; not advisor-approved split details.** Owner: Krish Patel. Evidence base: `d3b6a8be02d1045eb3dd5f1e7d08753177daa348`.

## Decisions and evidence

The [October Gate 1 overview](../artifacts/october/gate%201/gate1_overview.md) inherits September's approved source and acknowledges prior full-file EDA exposure. [Gate 4 sign-off](../artifacts/september/gate4_signoff.md) records full-team approval on October 6. The newer [recommendation register, OCT-REC-002](../artifacts/september/october_recommendation_register.md) records October 13 advisor guidance: reserve a test partition for final evaluation and use cross-validation within training. It leaves proportions, seed, folds and group/time assessment for team approval. The old handoff's five-fold full-file proposal is not an approved replacement for that guidance.

The assigned split task explicitly supplies a **75% training / 15% validation / 10% internal test, seed 42** fallback if proportions are not approved. This implementation materializes that proposal for review. It does not claim the advisor selected these fractions, and the team must approve this exact manifest and group/time assumptions before downstream modeling. Future cross-validation/tuning is confined to the 75% training partition; the extra validation partition is a separate development check, not a reason to use the test partition. Fold count/construction remain undecided and are not implemented here. No split/manifest utility existed on main before this task.

## Frozen source and field roles

- Source: `data/allstate_claims_data.csv`, 70,025,339 bytes, **188,318 claims × 132 columns**.
- SHA-256: `74037cb248a1064e4d578692a4f4e5d8492ed1b2033daf643496e1b68b14ae03`.
- [September manifest v1.0.0](../artifacts/september/artifact_manifest.json) supplies the source identity and reference hashes; [source profile](../artifacts/september/source_profile.csv) confirms the 132 fields and ID population.
- [Dictionary v1.1.0](../artifacts/september/data_dictionary_v1.1.0.csv): `id` is a unique claim identifier, not a predictor; `cat1`–`cat116` are nominal predictors; `cont1`–`cont14` are continuous predictors; `loss` is the positive numeric regression target. All 130 original predictors remain available; no EDA-derived fields become model inputs here.
- Original-scale MAE remains the primary future metric. No baseline, encoder or model is fitted by this task.

Repository migration moved September files into `artifacts/september/`. Historical paths within the archived manifest and old Markdown still refer to their former locations. The script resolves reference entries by unique filename in the preserved manifest, uses the current September directory, and verifies their original byte hashes; it does not rewrite historical evidence. The old documentation validator also expects pre-migration paths and is not a validation workflow for this task.

## Eligibility: all-or-abort

Before partition assignment, require the exact authoritative source SHA-256, bytes, row count and ordered schema. Verify dictionary source roles and source-profile identities against their frozen reference hashes. Every claim must have a nonmissing, valid canonical positive integer `id`, within the source int64 type, and IDs must be unique. Every `loss` must pass numeric, finite and strictly positive predicates.

These predicates implement the source's existing contract, not new claim exclusions. No high-loss claim, rare category, high-cardinality field or valid record is removed. Any failed check aborts the complete run with a specific error, before exporting artifacts; do not silently filter, deduplicate, repair, or continue with a smaller population. A source hash mismatch stops before diagnostic inspection. The successful eligibility summary records source/included/excluded counts, zero exclusions and an empty reasons list in metadata. Failed runs print the integrity discrepancy and exit nonzero; they must not be published as a valid split.

## Assignment and rounding

Method: **SHA-256 seeded pseudorandom ranking of canonical claim IDs**. For each ID, hash the ASCII string `october-split-v1|42|<id>`; rank ascending by digest bytes, with ascending integer ID as the collision tie-breaker. Assign successive rank blocks to train, validation and test. Targets and predictors never enter assignment. Serialize the manifest in ascending integer ID order with only `id,partition`, LF newlines and no index.

Counts use largest-remainder apportionment: floor each ideal count, then assign remaining rows to the largest fractional remainders (ties use train/validation/test order). Each count differs from its ideal by less than one claim. This produces **141,238 train, 28,248 validation and 18,832 test** rows. It is deterministic pseudorandom allocation, not a cryptographic privacy guarantee. Stable ID ranking makes assignment and manifest bytes independent of source row order; the production entry point still rejects a reordered source file because its exact source hash is frozen. Row-order invariance is tested separately on the eligible IDs.

## Intended partition use and leakage boundaries

| Partition | Intended use | Permitted in this task |
| :--- | :--- | :--- |
| Train — 75% | Fit preprocessing, both constant baselines and candidate models; future cross-validation/tuning only inside this partition. | Row counts, raw target summaries and categorical support/coverage. |
| Validation — 15% | Separate held-out development check; not input to training-fitted preprocessing. Record repeated selection exposure. | Row counts, raw target summaries, historical high-loss support and unseen-level coverage relative to training. |
| Test — 10% | **sealed** until the model-selection procedure and final candidate are fixed and the team authorizes final evaluation. | IDs/partition membership, row count and population share only. |

All learned encoders, frequencies, grouping rules, imputers, scalers, feature selection and target-derived transforms must fit only within training (and within each training fold during CV). Validation/test/future inputs are transform-only. Test targets must never guide split revisions, stratification, preprocessing, tuning or seed choice. No seed search is performed.

There is a necessary distinction between eligibility and target analysis: before partition labels exist, the entire source gets only the mandatory validity predicates for `loss`; no target values or distribution summaries are printed or retained from that pass. After assignment, the diagnostics loader checks each ID and skips every test row **before converting its loss or retaining predictor values**. The CSV parser necessarily traverses bytes in the shared source file; the source is not physically access-controlled. A regression test poisons test loss strings and verifies the diagnostics are unchanged. This is an enforced diagnostic boundary, not a claim that the shared source is inaccessible.

## Diagnostics and inherited EDA rules

[Split diagnostics](../artifacts/october/gate%201/october_split_diagnostics.csv) use long format: partition, metric, value, denominator, unit. Each partition receives count/share; **only train and validation** receive loss count, mean, median, sample standard deviation (ddof=1), p90/p95/p99, maximum, and high-loss support. Pandas' default linear quantile interpolation is used. CSV values use 12 significant digits; metadata retains hashes and exact integer counts.

The existing September notebook defines high loss descriptively as **loss > p95**. Use the exact **historical** p95 from [target_summary.csv](../artifacts/september/target_summary.csv), `8508.536499999998`, without recomputing any full-file or test target summaries. Report counts, denominators and shares for train/validation only. This threshold reflects September full-file EDA, including rows now assigned to test; it is a historical diagnostic reference, not a training-fitted modeling rule. It is never used for assignment or seed choice. Any future learned high-loss decision threshold must be defined within training.

[Categorical coverage](../artifacts/october/gate%201/october_categorical_coverage.csv) covers all 116 categorical predictors: train/validation cardinalities; the explicit unseen validation labels and counts; unseen validation observation counts, denominators and shares; training rare-level counts/support; and validation-local rare-level counts/support. It separately reports validation observations on training-rare levels (unseen levels do not count as observed training-rare levels). The inherited September EDA rule is **support <100**; validation-local rarity is descriptive and must not become a fitted mapping. **This is not a selected October modeling threshold.** All labels remain intact; no encoder is fitted. Feature-level observation counts overlap across fields and must not be summed as distinct claims.

## Predeclared Criteria for Changing the Split

No automatic split revision is allowed. The following criteria are fixed before diagnostics; none permits optimizing the seed or assignments to improve MAE. Proposed numerical floors below are review triggers, not established statistical-power guarantees.

| Observable condition | Why it matters | Required evidence | Who must approve | Versioning |
| :--- | :--- | :--- | :--- | :--- |
| Duplicate claim identity or documented shared policy/vehicle/person spans partitions | Claim-level independence fails. | Identity audit and confirmed grouping metadata; do not infer groups from anonymous category similarity. | Team + Challenge Advisor | Preserve v1; approve a new version with group-safe assignments and a new manifest/hash. |
| Newly supplied dates establish temporal dependence or a future-period evaluation requirement | Random splitting may overstate deployment generalization. | Date provenance, ordering and advisor explanation of the prediction horizon. | Team + Challenge Advisor | New version with a dated rationale and time-respecting assignments. |
| Source/hash/schema/eligibility discrepancy | Population no longer matches the approved contract. | Failed integrity check and corrected approved source/role version; abort rather than repair automatically. | Data owner + team; advisor for source replacement | New source/split version, hashes and eligibility report. |
| Validation population below 10,000 claims or a required, predeclared reporting slice has fewer than 100 validation observations | Precision may be inadequate for an agreed reporting objective. | ID/count-only review for overall floor; train/validation-only slice counts and a precision justification. Test target slices prohibited. | Team + Challenge Advisor | New version only if design truly needs revision; document tradeoffs and preserve old IDs. |
| A required evaluation cannot be executed because unseen levels lack a supported safe fallback, or a predeclared slice has zero training support | Technical evaluation feasibility, not evidence of poor accuracy. | Reproducible preprocessing failure and evidence that training-only unknown handling cannot resolve it; unseen categories alone do not justify resplitting. | Modeling owner + team + Challenge Advisor | Prefer a preprocessing fix; any split change requires a new version and rationale. |
| Dated Challenge Advisor requirement mandates a different design | Evaluation must meet the agreed project objective. | Written requirement and reviewed design amendment, without revealing test target diagnostics. | Team + Challenge Advisor | New version; archive the old artifact and decision. |

Every approved change records who approved, why, source/configuration/code versions and new manifest hash. If test targets have ever been accessed, disclose that exposure; moving labels does not restore an untouched holdout. Poor model performance, attractive loss distributions or ordinary unseen labels are not split-change reasons.

## Reproduction and modeling handoff

From the repository root:

```bash
python3 scripts/create_partition_manifest.py
python3 -m unittest discover -s tests -p 'test_partition_manifest.py' -v
```

The default output directory is `artifacts/october/gate 1/`. Metadata records source/field-role hashes, eligibility summary, split version/configuration, counts, seed, code-file SHA-256, Python/pandas/NumPy versions, manifest/diagnostic hashes, test policy and actual validation checks. Use the PR/commit containing that code hash for reproduction. Re-running in the same recorded environment is byte-identical; a different artifact or runtime receipt is never silently overwritten. A new `--output-dir` supports an isolated reproduction check or a separately approved version, not automatic replacement of v1. No dependency changes are needed.

Future modeling must read the frozen manifest, check its SHA-256 against metadata, assert unique source/manifest IDs and a one-to-one join, then select only the declared train/validation IDs before loading targets. Use all 130 source predictors initially, exclude `id`, `loss` and EDA-derived fields from X, and keep the exact assignments; never independently call a split utility. Baselines/model evaluation use original `loss` units. Final test access requires a separately reviewed evaluation step; this script offers no test-target diagnostics option.

## Assumptions and limitations

Unique claim IDs do not prove independence of people, policies or vehicles. The 132-field dictionary exposes no confirmed time/group key, so the claim-level random proposal is implementable but exchangeability remains an assumption. Confirm grouping/time dependencies with the advisor before modeling. The merged register records that supplied fields may be assumed available at claim filing; upstream scaling provenance and external/future-period validation remain unresolved.

September already examined this whole file, including rows now in test. Sealing these IDs from this point prevents additional October feedback but cannot make them historically unseen or establish future-period performance. The historical p95 is labeled accordingly. Final proportions, the additional validation holdout, CV fold design and the test release procedure still need team confirmation. No evidence here selects a model, encoder, rare threshold or feature set.
