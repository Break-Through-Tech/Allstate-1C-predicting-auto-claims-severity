# October Modeling Handoff

Version 1.0.0 · Task #15 / Gate 4 Task 3 · **PROPOSED handoff — team/advisor approval pending.** Evidence snapshot: `5353f05906ba37830500e46f4693e345f2a02d97`.

## 1. Purpose

Translate September evidence into testable October decisions. No model, baseline, encoder, split, or feature-selection procedure is fitted or executed by this task. The [recommendation register](october_recommendation_register.md) and [CSV](../artifacts/october_recommendation_register.csv) track 12 proposed actions. September's completed calculations are usable evidence, but the outstanding human approvals must not be represented as complete.

## 2. Frozen Source and Field Roles

Inherit [data/allstate_claims_data.csv](../data/allstate_claims_data.csv): **188,318 rows, 132 columns, 70,025,339 bytes**. SHA-256: `74037cb248a1064e4d578692a4f4e5d8492ed1b2033daf643496e1b68b14ae03`. Source identity is recorded in the [manifest v1.0.0](../artifacts/artifact_manifest.json); [source_profile.csv](../artifacts/source_profile.csv) has no separate version label and is identified by its manifest hash.

[Dictionary v1.1.0](../artifacts/data_dictionary_v1.1.0.csv) adds derived-field documentation to the [Gate 2-approved v1.0.0](../artifacts/data_dictionary_v1.0.0.csv); source-field roles are unchanged:

| Field(s) | Inherited role |
| :--- | :--- |
| `id` | Identifier, NOT an ordinary model feature; use for identity/audit only. |
| `cat1` through `cat116` | 116 anonymous nominal categorical predictors; no order or business meaning inferred. |
| `cont1` through `cont14` | 14 anonymous continuous predictors; supplied scale [0, 1], original units and upstream scaling unknown. |
| `loss` | Positive continuous regression target in original loss units. |

Start future comparisons with all 130 source predictors. September-derived display/bin/target-summary fields are evidence, not an approved feature set. Recheck source hash/schema before modeling (OCT-REC-001).

## 3. September Evidence Summary

- **Data:** 188,318 claims × 132 source columns; 1 identifier, 116 categorical predictors, 14 continuous predictors, 1 target. Zero missing cells and exact duplicate rows (FND-005; Gate 3 saved integrity checks). Continuous values are within inclusive [0, 1].
- **Target:** mean 3,037.34, median 2,115.57, p95 8,508.54, maximum 121,012.25, skewness 3.795; a long right tail. Values come from [target_summary.csv](../artifacts/target_summary.csv), not model predictions.
- **Categorical:** 72 binary fields, 88 with ≤4 levels, and 17 with >10 levels. Highest cardinalities: cat116 326, cat110 131, cat109 84. The inherited support <100 rule identifies 469 rare levels across 35 fields; this is an EDA support/display rule. See [inventory](../artifacts/categorical_inventory.csv), [low support](../artifacts/categorical_low_support_evidence.csv), and [high-cardinality tails](../artifacts/categorical_high_cardinality_evidence.csv). Support-aware raw target comparisons remain in the [target evidence](../artifacts/categorical_target_evidence.csv), FND-003.
- **Continuous:** strongest absolute marginal raw-loss Pearson correlations: cont2 0.142, cont7 0.120, cont3 0.111; 9 of 14 are below 0.05. Predictor pairs: cont11/cont12 0.994, cont1/cont9 0.930, cont6/cont10 0.883 (saved Gate 3 Task 4 strongest-pairs table; FND-001). The [continuous inventory](../artifacts/continuous_inventory.csv) classifies 8 fields as non-monotonic under a **proposed rule still awaiting team approval**; the [137-row bin table](../artifacts/continuous_bin_target.csv) preserves support and raw summaries. These marginal/binned patterns do not establish predictive value.
- **Limits and review status:** anonymous meanings, undocumented upstream scaling, association is not causation, and no separate future/test-period evidence. September does not establish production readiness or a winning model. Alternative-path recalculation agrees, but independent human review and final gate approval remain pending ([Gate 3](gate3_signoff.md), [Gate 4](gate4_signoff.md)).

## 4. Target and Evaluation Metric

Target: **`loss`**. Primary metric: **Mean Absolute Error (MAE) in original `loss` units**, the average absolute difference between predicted and actual claim loss. This inherits the [project overview](../Challenge-Project-Overview.md) (Success Criteria / Evaluation Metrics) and [Gate 2 sign-off](gate2_signoff.md).

`log1p(loss)` improved September visualization; it is not a replacement for original-scale business reporting. A future transformed-target experiment is only HYP-001: inverse-transform predictions before headline MAE and document any training-fitted correction. No performance claim follows from the descriptive skewness reduction (OCT-REC-003, 009).

## 5. Proposed Validation Design

**PROPOSED — requires October confirmation.** The notebook's existing *October Evaluation Plan (Draft)* freezes neither a split fraction nor fold count/seed. Proposed implementation: **5-fold regression cross-validation, shuffle=True, random seed 42**. Record fold assignments using source row identity; use identical folds across candidates and both baselines. All learned preprocessing and constants are refitted inside each training fold. Do not stratify on the September full-file target summaries.

Report each fold's MAE, unweighted mean and sample standard deviation (ddof=1) across five fold MAEs, plus sample-weighted pooled out-of-fold MAE. Persist train/validation counts and random seeds. This uses the available labeled file efficiently and measures partition variability, but assumes rows are exchangeable—unique IDs do not prove this. Confirm temporal/group structure with the advisor before approving random folds; use group/time-respecting partitions if necessary.

No folds are created here. Predeclare comparisons; validation observations must not influence fitted preprocessing or ad hoc tuning. Before repeated model/parameter selection, approve an untouched final holdout or nested evaluation, including its allocation/seed, so selection scores are not reported as unbiased final performance. That extra protocol remains unresolved; future-period generalization is untested (OCT-REC-002, Q1).

## 6. Baseline Plan

- **Mean-constant baseline:** predict the **TRAINING-set mean `loss`** for every validation observation. The project explicitly requests this comparator.
- **Median-constant baseline:** predict the **TRAINING-set median `loss`** for every validation observation. The median minimizes absolute error for a constant prediction under MAE.

Learn both constants anew from TRAINING DATA ONLY for each fold. Never use the full-file mean/median in section 3 as the evaluation constants. Report both original-scale baseline MAEs on the exact candidate validation rows. No baseline is run here and no September full-dataset descriptive MAE is model performance (OCT-REC-003).

## 7. Preprocessing and Leakage Boundaries

Methodological requirements from the notebook's October plans and coach milestones:

| Partition | Permitted operation |
| :--- | :--- |
| TRAINING | Fit preprocessing + transform; fit constants/model on this partition only. |
| VALIDATION | Transform only using training-fitted preprocessing; evaluate predictions. |
| TEST/FUTURE | Transform only using training-fitted preprocessing; no refitting from these rows. |

This covers categorical encoders, category-frequency calculations, rare-category grouping, target-derived transformations, imputers if needed, scalers if needed, feature-selection procedures, and every learned transformation. Validation/test values and targets must not influence fitting. Prefer a reproducible training/modeling pipeline, refitted per fold; learned target-dependent mappings, if ever proposed, would also require training-internal cross-fitting, not full-file statistics. No such encoding is selected or implemented here.

September has no missing cells, so it supplies no evidence for a fitted imputer now. October must define explicit schema/missing behavior and test safe unknown/unseen-category handling that does not crash. The supplied continuous scaling predates this task; its provenance is unresolved and should not be claimed training-fitted by the team (OCT-REC-004, Q2).

## 8. Categorical / High-Cardinality Considerations

Observed cardinalities are cat116 326, cat110 131, cat109 84; consult [all high-cardinality tails](../artifacts/categorical_high_cardinality_evidence.csv) for supported/rare level counts, rare observation counts and denominators. OCT-REC-005/006 ask: how should each family encode high-cardinality fields; does cardinality materially hurt held-out MAE or resources; should rare levels be grouped; what training-only frequency rule should define rare; how will unseen validation/inference levels be handled; which candidates improve held-out MAE?

Candidate approaches, not decisions: one-hot encoding with unknown handling, an explicit unknown bucket, or training-frequency rare grouping with safe unseen handling. Compare retaining levels against grouping, with thresholds learned/selected within training partitions. **The September EDA rare-level threshold is NOT automatically the October modeling threshold.** High cardinality alone does not justify feature removal. Source categories remain intact. Report MAE and support counts for rare/unseen slices, alongside overall results and runtime/memory.

## 9. Correlated-Feature Considerations

The saved strongest-pairs table and FND-001 show Pearson **cont11/cont12 0.994, cont1/cont9 0.930, cont6/cont10 0.883**. Strong predictor correlation can complicate coefficient interpretation for linear models; it does not establish that dropping either member improves performance. OCT-REC-007 proposes controlled same-fold retain/omit comparisons only after approval. Nonlinear/tree-based models may behave differently. Separate coefficient stability/interpretation from held-out original-scale MAE; no predictors are removed here.

## 10. Candidate Model Families

Only the [project overview](../Challenge-Project-Overview.md), *Suggested Approach → Algorithm examples*, supplies the list below. These are **candidates**, not selected models; libraries mentioned elsewhere are not extra family requirements. GLM distribution/link, encoding, settings, and any regularization remain undecided.

| Model family | Why test / September evidence | Preprocessing considerations | Validation required |
| :--- | :--- | :--- | :--- |
| Generalized linear model (GLM) | Project candidate; provides a structured comparator for weak marginal relationships (FND-007) and correlated predictors (FND-001). | Training-fitted nominal encoding, unknown handling; check collinearity and any needed scaling; choose distribution/link later. | Same-fold original-scale MAE vs both constants; coefficient stability and retained-feature sensitivity. |
| Random forest | Project candidate; exploratory nonlinear binned patterns motivate testing flexibility (FND-008/HYP-002, rule approval pending). | Compatible training-fitted category representation; unseen fallback; record high-cardinality resource cost. | Same-fold MAE vs both constants, fold variability, runtime and rare/high-loss slices. |
| Gradient boosting machine (GBM) | Project candidate; test whether flexible relationships help beyond marginal correlations (FND-007/008, HYP-002). | Training-fitted category handling and missing/schema behavior; keep validation out of preprocessing fits. | Same-fold MAE vs both constants, fold variability and configuration/runtime. |
| Extreme gradient boosting (XGBoost) | Explicit project example; categorical support variation and binned structure motivate an experiment, not a performance expectation. | Confirm encoding compatibility for the eventual library/version and safe unseen behavior; no native-category capability assumed here. | Same-fold MAE vs both constants, memory/runtime, error slices and exact dependencies. |

## 11. Required October Validation Evidence

These are **validation requirements**, not September findings. Every proposed decision needs:

1. Held-out/cross-validated MAE in original `loss` units, compared against **both mean-constant and median-constant baselines** on identical rows.
2. Exact split/fold configuration and saved assignments, random seed(s), training/validation sample counts, fold-level MAE, mean/std MAE and pooled MAE when using CV.
3. Training-only preprocessing confirmation: fit-row membership, transformation/configuration provenance, and evidence validation/test data did not influence fitted preprocessing. Record unseen-category behavior and explicit tests of it.
4. Model and preprocessing configuration (including inverse target transformation if any), reproducible code/commit, source hash, dependency versions, runtime/platform, and experiment output locations.
5. Error distribution, high-loss observation performance and rare/high-cardinality/unseen sensitivity with support/denominators; predeclare diagnostic thresholds from training data.
6. Decision rationale, uncertainty and limitations, plus reviewer/team approval. Complete outstanding September reviews first; report repeated-selection limitations and the untouched final-evaluation protocol before any final model claim.

## 12. Recommendation Register Summary

12 stable IDs, all PROPOSED: OCT-REC-001 source/roles; 002 validation design; 003 both constants and MAE; 004 leakage boundaries; 005 high-cardinality encoders; 006 rare/unseen handling; 007 correlated-feature sensitivity; 008 project model families; 009 transformed-target hypothesis; 010 error diagnostics; 011 review/reproducibility; 012 advisor gaps. Each [register entry](october_recommendation_register.md) contains observed context, exact evidence location, rationale, type, action and validation needed. General methodological requirements are labeled as such.

## 13. Unresolved Questions for Challenge Advisor

| ID | Question | Why it matters / evidence context | Decision affected |
| :--- | :--- | :--- | :--- |
| Q1 | Is shuffled 5-fold CV appropriate, or do claims share groups/time structure? Is external/future-period data available, and what untouched final evaluation is required after selection? | FND-009: one anonymous labeled file; draft plan has no approved split/seed. | Validation design, independence assumptions and generalization claims (REC-002). |
| Q2 | Are every predictor and its upstream scaling available at the intended prediction time? Can group/time metadata or scaling provenance be supplied? | FND-005/009 and dictionary: meanings/processing undocumented; reserve objective requires early information. | Leakage audit, feature eligibility and valid split (REC-001/004/012). |
| Q3 | Are there required or prohibited encoders, grouping rules, resource limits or unseen-category policies? | FND-002/004: rare tails and high cardinality; no approved modeling encoder. | Encoding experiments and safe inference behavior (REC-005/006). |
| Q4 | Must all four overview families be tested, and are transformed-target experiments permitted? | Overview gives examples; HYP-001/002 remain hypotheses. | Experiment scope and target-transform candidates (REC-008/009). |
| Q5 | What interpretation is expected for anonymous fields, and what exact October artifacts/acceptance criteria are required beyond original-scale MAE and baselines? | Overview monthly milestones and FND-009 do not supply field meanings or detailed deliverable approval rules. | Interpretation/reporting scope, deliverables and approvals (REC-010/012). |
| Q6 | Who will complete the independent checks, approve the binned-pattern rule, review fixes and approve this handoff? | Gate 3/4 sign-offs remain DRAFT; reviewer names PENDING and independent=false despite matching calculations. | Final September gate approval and start of modeling (REC-011). |

These questions have no inferred answers. Record advisor/team decisions before treating any affected proposal as approved.

## 14. Work Explicitly Deferred to October

Creating splits, fitting both baselines, implementing preprocessing, encoding/grouping, model training/comparison, feature inclusion/exclusion experiments, target-transform tests and hyperparameter work are deferred. No source records, rare levels, high-loss observations or predictors are removed. No SHAP or production deployment work is performed.

### Not Yet Decided

Winning model; final feature set; final categorical encoder; final rare-category threshold for modeling; whether correlated predictors should be removed; final hyperparameters; production-readiness; causal interpretation; and individual claim reserve decisions. This handoff is not authority to make claim-level reserve decisions.

## 15. Reproduction / Evidence References

The [September report](september_report.md), [findings v2.0.0](findings_register.md), [anomaly register](anomaly_register.md), [Gate 3 sign-off](gate3_signoff.md) and [Gate 4 sign-off](gate4_signoff.md) give evidence and review status. Categorical independent calculation is in [cardinality verification](../artifacts/categorical_cardinality_verification.csv); the saved notebook reviewer section independently recalculates metrics via csv/numpy but does not constitute completed human review.

Original official run: `WR-SEPT-G4-20261002T205412Z-03140d1`; code `03140d1e665bdb331bccad20cc7a93d1fbe0148a`; executed outputs committed in `ab17125`; bundle `SEPT-BUNDLE-78876ab8c12d`. Manifest configuration/dictionary and [requirements.txt](../requirements.txt) capture dependency pins. Use [README Setup and Installation](../README.md) to reproduce September from the exact recorded revision. The receipt says **COMPLETED WITH WARNINGS**, with independent review pending; it is not final team approval.

Task #15 preserves all prior notebook cells/outputs and adds only a Markdown completion-summary cell. It preserves the code-cell hash and all manifest-listed file hashes. This documentation extension is not a newly executed official EDA run. Validate the new register, links, required content, frozen evidence hashes and summary from the repository root with:

```bash
python3 scripts/validate_october_handoff.py
```

The [Task #15 Completion Summary](../notebooks/data-understanding.ipynb#task-15-completion-summary) is in the notebook, as requested. No separate task-summary Markdown file is created.
