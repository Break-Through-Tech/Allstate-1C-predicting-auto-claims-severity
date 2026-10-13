# October Recommendation Register

Version 1.0.0 · Task #15 / Gate 4 Task 3 · Evidence snapshot: `5353f05906ba37830500e46f4693e345f2a02d97`.

All entries are **PROPOSED** October work. This register synthesizes committed September evidence; it does not assert final September approval. Gate 3/4 independent human reviews and team decisions remain pending. Methodological requirements are explicitly distinguished from empirical findings.

[Structured CSV](../artifacts/october_recommendation_register.csv) · [Modeling handoff](october_modeling_handoff.md). CSV `evidence_location` uses repository-relative paths with `::` section/row selectors, separated by semicolons. Each section below contains the same nine fields as the CSV.

## OCT-REC-001 — Inherit the frozen source and source-field roles.

- **september_evidence:** Manifest records 188,318 rows × 132 columns; dictionary v1.1.0 preserves the source roles from v1.0.0; FND-005 reports zero missing cells and duplicate rows.
- **evidence_location:** [artifacts/artifact_manifest.json](../artifacts/artifact_manifest.json) — source; [artifacts/data_dictionary_v1.1.0.csv](../artifacts/data_dictionary_v1.1.0.csv) — field_type=source; [artifacts/source_profile.csv](../artifacts/source_profile.csv) — all 132 rows; [docs/findings_register.md](../docs/findings_register.md) — FND-005
- **rationale:** Methodological requirement: source identity and feature-role consistency make experiment comparisons reproducible.
- **recommendation_type:** validation_requirement
- **october_action:** Check source hash/schema at experiment entry; exclude id and September-derived display fields from ordinary predictors; retain all 130 source predictors initially.
- **validation_needed:** Recorded matching SHA-256, role counts, dictionary version, input-column list, and explicit schema-failure behavior.
- **status:** PROPOSED

## OCT-REC-002 — Confirm a reproducible validation design before experiments.

- **september_evidence:** FND-009 records one labeled file and no separate future/test period. The notebook October Evaluation Plan (Draft) requires a fixed seed but approves no specific split.
- **evidence_location:** [docs/findings_register.md](../docs/findings_register.md) — FND-009; [notebooks/data-understanding.ipynb](../notebooks/data-understanding.ipynb) — October Evaluation Plan (Draft); [docs/gate3_signoff.md](../docs/gate3_signoff.md) — Team approval
- **rationale:** Methodological requirement: common partitions permit fair comparison; anonymous fields do not establish independent or temporally exchangeable rows.
- **recommendation_type:** future_decision
- **october_action:** Propose shuffled 5-fold regression cross-validation with random seed 42, subject to advisor confirmation of grouping/time constraints; persist fold assignments and reuse them.
- **validation_needed:** Team approval, group/time assessment, fold counts and assignments, seed, fold-level original-scale MAE, unweighted mean/std MAE and sample-weighted pooled MAE; separate untouched final evaluation if repeated selection is performed.
- **status:** PROPOSED

## OCT-REC-003 — Plan both training-only constant baselines and original-scale MAE.

- **september_evidence:** Target mean 3,037.34 and median 2,115.57 differ; the project overview requires a mean model and MAE. These full-file statistics are descriptive only.
- **evidence_location:** [artifacts/target_summary.csv](../artifacts/target_summary.csv) — mean,p50; [Challenge-Project-Overview.md](../Challenge-Project-Overview.md) — Suggested Approach / Evaluation Metrics; [notebooks/data-understanding.ipynb](../notebooks/data-understanding.ipynb) — October Evaluation Plan (Draft)
- **rationale:** Methodological requirement: both baseline comparators contextualize held-out results; the median minimizes absolute error for a constant prediction.
- **recommendation_type:** validation_requirement
- **october_action:** For each training fold learn its mean loss and median loss, predict each constant on that fold’s validation rows, and compare candidate models on identical partitions.
- **validation_needed:** Original-loss-unit MAE for both baselines and each candidate, training/validation counts, and proof constants use only training targets; no full-dataset descriptive MAE labeled as performance.
- **status:** PROPOSED

## OCT-REC-004 — Enforce training-only preprocessing and safe unknown handling.

- **september_evidence:** Task #10 October categorical encoding considerations requires training-only encoders and unknown handling; FND-005 reports no current missingness but undocumented upstream scaling.
- **evidence_location:** [notebooks/data-understanding.ipynb](../notebooks/data-understanding.ipynb) — October categorical encoding considerations; [docs/findings_register.md](../docs/findings_register.md) — FND-005; [docs/anomaly_register.md](../docs/anomaly_register.md) — G3-WF-003
- **rationale:** Methodological requirement, not a discovered causal result: validation/test information must not influence learned preprocessing.
- **recommendation_type:** validation_requirement
- **october_action:** Keep all encoders, frequencies, grouping, target-derived transforms, imputers, scalers, feature selection and learned transforms inside fold-fitted pipelines. Validation/test/future rows are transform-only. Define missing/schema behavior and safe unseen-category fallback.
- **validation_needed:** Training membership audit, fitted-state provenance, unseen-category tests that do not crash, and confirmation validation/test values or targets never fitted preprocessing.
- **status:** PROPOSED

## OCT-REC-005 — Compare high-cardinality encoding candidates without removing fields.

- **september_evidence:** FND-004 and inventory: cat116 326, cat110 131, cat109 84; 17 fields exceed the inherited 10-level display cutoff. FND-003 records support-aware target differences.
- **evidence_location:** [artifacts/categorical_inventory.csv](../artifacts/categorical_inventory.csv) — cardinality; [artifacts/categorical_high_cardinality_evidence.csv](../artifacts/categorical_high_cardinality_evidence.csv) — all fields; [artifacts/categorical_target_evidence.csv](../artifacts/categorical_target_evidence.csv) — supported and low-support rows; [docs/findings_register.md](../docs/findings_register.md) — FND-003,FND-004
- **rationale:** Observed cardinality and uneven support motivate checking encoding cost and generalization, not declaring predictive value.
- **recommendation_type:** proposed_experiment
- **october_action:** Compare compatible encoders, such as one-hot with safe unknown handling, across the project candidate families. Ask whether high cardinality materially affects each family; keep source labels unchanged.
- **validation_needed:** Same-fold MAE versus both constants, memory/runtime, encoding configuration, unknown handling, and support-aware error slices; no final encoding decision before validation.
- **status:** PROPOSED

## OCT-REC-006 — Evaluate training-fitted rare-level grouping and unseen-level behavior.

- **september_evidence:** FND-002: support <100 identifies 469 levels in 35 fields; high-cardinality evidence separates rare tails. HYP-004 remains a hypothesis.
- **evidence_location:** [artifacts/categorical_low_support_evidence.csv](../artifacts/categorical_low_support_evidence.csv) — level_support,denominator,support_share; [artifacts/categorical_high_cardinality_evidence.csv](../artifacts/categorical_high_cardinality_evidence.csv) — rare tail; [docs/findings_register.md](../docs/findings_register.md) — FND-002,HYP-004
- **rationale:** Thin support can make descriptive target estimates uncertain; grouping may or may not improve held-out error.
- **recommendation_type:** proposed_experiment
- **october_action:** Compare retaining levels with frequency-based grouping fitted only on training partitions and an explicit unknown fallback. Choose thresholds within training data and confirm unseen categories in validation/inference are safe.
- **validation_needed:** Held-out MAE and subgroup counts, unseen-level tests, learned grouping provenance, and sensitivity to thresholds. The September EDA rare threshold is not automatically the October modeling threshold.
- **status:** PROPOSED

## OCT-REC-007 — Test correlated-predictor sensitivity separately from interpretation.

- **september_evidence:** FND-001 and the saved strongest-pairs table report Pearson cont11/cont12 0.994, cont1/cont9 0.930, cont6/cont10 0.883.
- **evidence_location:** [docs/findings_register.md](../docs/findings_register.md) — FND-001; [notebooks/data-understanding.ipynb](../notebooks/data-understanding.ipynb) — Gate 3 Task 4 strongest pairs table
- **rationale:** Strong predictor correlation can complicate linear-model coefficient interpretation; correlation alone does not justify dropping a feature.
- **recommendation_type:** proposed_experiment
- **october_action:** Start with all source predictors. If approved, compare retaining versus omitting correlated partners on identical partitions; contrast GLM sensitivity with tree/ensemble behavior.
- **validation_needed:** Held-out original-scale MAE deltas, fold variability and coefficient stability where applicable. Interpretability and predictive performance must be assessed separately; no removal based solely on correlation.
- **status:** PROPOSED

## OCT-REC-008 — Evaluate only the project-supported candidate model families.

- **september_evidence:** Project Algorithm examples lists GLM, random forest, GBM and XGBoost. FND-007 has weak marginal Pearson relationships (cont2 0.142, cont7 0.120, cont3 0.111); FND-008 has exploratory binned structure under an unapproved classification rule.
- **evidence_location:** [Challenge-Project-Overview.md](../Challenge-Project-Overview.md) — Algorithm examples; [artifacts/continuous_inventory.csv](../artifacts/continuous_inventory.csv) — pearson_raw,pattern_classification; [artifacts/continuous_bin_target.csv](../artifacts/continuous_bin_target.csv) — raw_median_loss; [docs/findings_register.md](../docs/findings_register.md) — FND-007,FND-008,HYP-002
- **rationale:** The supplied families permit comparisons of linear and flexible relationships; marginal correlation does not establish feature uselessness or a winner.
- **recommendation_type:** proposed_experiment
- **october_action:** After approval, test generalized linear model (GLM), random forest, gradient boosting machine (GBM), and extreme gradient boosting (XGBoost) with family-compatible training-only preprocessing.
- **validation_needed:** Identical split configuration, both baselines, original-scale MAE, model/preprocessing settings, dependencies/runtime and reproducible code. No ranking is established by September.
- **status:** PROPOSED

## OCT-REC-009 — Evaluate any target transformation in original loss units.

- **september_evidence:** FND-006: raw skewness 3.795, visualization log1p skewness 0.097; HYP-001 proposes a transformed-target experiment, not a demonstrated improvement.
- **evidence_location:** [artifacts/target_summary.csv](../artifacts/target_summary.csv) — skewness,log1p_skewness; [docs/findings_register.md](../docs/findings_register.md) — FND-006,HYP-001
- **rationale:** A readable visualization does not show that transforming the training target improves MAE.
- **recommendation_type:** proposed_experiment
- **october_action:** Ask advisor about transformation constraints; if approved, compare raw-target and transformed-target candidates on the same partitions and inverse-transform predictions for evaluation.
- **validation_needed:** Original-scale MAE versus both constants, documented inverse transformation and training-only fitting for any learned correction; no transformed-scale headline metric.
- **status:** PROPOSED

## OCT-REC-010 — Require error-distribution and high-loss diagnostics with support counts.

- **september_evidence:** FND-006 reports p95 8,508.54, maximum 121,012.25, and a long right tail; HYP-003 concerns concentration of associations among high-loss claims.
- **evidence_location:** [artifacts/target_summary.csv](../artifacts/target_summary.csv) — p95,max,top1pct_claims_share_of_total_loss; [docs/findings_register.md](../docs/findings_register.md) — FND-006,HYP-003; [artifacts/categorical_target_evidence.csv](../artifacts/categorical_target_evidence.csv) — support_class
- **rationale:** Aggregate MAE alone can obscure heterogeneous errors; rare-level estimates need denominators.
- **recommendation_type:** validation_requirement
- **october_action:** Report held-out residual/error distributions and high-loss and rare/unseen slices with counts. Predeclare slice definitions from training data; inspect diagnostics without retuning against held-out observations.
- **validation_needed:** Overall and slice MAE, denominators, fold variability and threshold provenance; retain high-loss observations absent documented invalidity.
- **status:** PROPOSED

## OCT-REC-011 — Preserve reproducibility and complete outstanding independent review.

- **september_evidence:** Gate 4 official run completed with warnings; alternative calculations match but five reviewer groups remain PENDING / independent=false. Gate 3 approvals, including the binned classification rule, are incomplete.
- **evidence_location:** [docs/gate3_signoff.md](../docs/gate3_signoff.md) — Independent review matrix / Decisions requiring team approval; [docs/gate4_signoff.md](../docs/gate4_signoff.md) — Gate 4 Run Receipt; [artifacts/artifact_manifest.json](../artifacts/artifact_manifest.json) — configuration,files; [docs/anomaly_register.md](../docs/anomaly_register.md) — pending reviews
- **rationale:** Calculated agreement is not independent human approval. Modeling handoff cannot silently close September gates.
- **recommendation_type:** unresolved_question
- **october_action:** Assign eligible reviewers, record review results/team decisions, and obtain handoff approval before modeling. Preserve the existing run receipts and bundle; record each future experiment’s commit, configuration and environment.
- **validation_needed:** Completed independent review matrix and recorded approvals/dissent; reproducible experiment receipt with source hash, dependency versions, runtime, seeds, sample counts and preprocessing audit.
- **status:** PROPOSED

## OCT-REC-012 — Resolve data structure, deployment context and deliverable expectations with the advisor.

- **september_evidence:** FND-009 records anonymous meanings and no separate test/future period; FND-005 notes undocumented upstream processing. The overview lists examples, not a field mapping or a mandated model winner.
- **evidence_location:** [docs/findings_register.md](../docs/findings_register.md) — FND-005,FND-009; [artifacts/data_dictionary_v1.1.0.csv](../artifacts/data_dictionary_v1.1.0.csv) — documented_meaning; [Challenge-Project-Overview.md](../Challenge-Project-Overview.md) — Dataset / Project Milestones / Algorithm examples
- **rationale:** Unknown time/group structure and scoring availability affect validation validity; absent future-period data limits generalization claims.
- **recommendation_type:** unresolved_question
- **october_action:** Confirm groups/time and prediction-time availability, upstream scaling provenance, external test availability, mandatory families, transform constraints, interpretation scope and October deliverables.
- **validation_needed:** Written advisor/team answers tied to questions Q1–Q6 in the handoff; update proposed design before any affected experiment is approved.
- **status:** PROPOSED
