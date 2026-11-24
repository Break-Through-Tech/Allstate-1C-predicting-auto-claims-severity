# October candidate decision

Status: **PROVISIONAL_CANDIDATE**. Provisional candidate: **XGBoost A2-C03**.

Lowest validation MAE among policy-retained eligible candidates, strictly below both constants. Review status: Generated technical recommendation; team and Challenge Advisor approval not recorded.

## Rule and evidence

Strictly lower original-scale validation MAE than both constants on the same 28,248 IDs from `october-split-v1`; invalid predictions/provenance are excluded. Source and manifest hashes, baseline identities and all candidate run IDs are in the machine-readable record.

| Candidate | Validation MAE | Claims | Change vs mean | Change vs median | Improvement vs mean | Improvement vs median | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| Ridge GLM | 1250.453333 | 28248 | -709.177583 | -552.340521 | 36.189344% | 30.638030% | QUALIFIES |
| XGBoost A2-C03 | 1167.515314 | 28248 | -792.115603 | -635.278540 | 40.421673% | 35.238557% | PROVISIONAL_CANDIDATE |
| XGBoost A2-C06 | 1166.681104 | 28248 | -792.949812 | -636.112750 | 40.464243% | 35.284830% | NOT_RETAINED_BY_EXISTING_POLICY |

A2-C03 is the lowest-error policy-retained family candidate and strictly beats both constants. A2-C06 also beats both and has a 0.834209 lower validation MAE, but it failed the adopted training-only retention rule: pooled out-of-fold MAE worsened by 0.409930 instead of improving by at least 1.0. Reversing that decision using validation would reopen the experiment. The Gate 1 across-family one-unit tie proposal was not independently approved globally; no across-family tie affects this result (A2-C03 is 82.938019 below GLM).

Candidate runs:

- Ridge GLM: `glm-20261103T055706Z-0748a4b5`; evaluation ELIGIBLE.
- XGBoost A2-C03: `xgboost-task4-20261112T071650.896576Z:A2-C03`; evaluation ELIGIBLE.
- XGBoost A2-C06: `xgboost-task4-20261112T071650.896576Z:A2-C06`; evaluation ELIGIBLE.

Baseline run: `baselines-20261025T034742Z-0e9ea822`. Diagnostic concerns:

| Candidate | Threshold | Claims / 28,248 | MAE | Mean signed error |
|---|---:|---:|---:|---:|
| Ridge GLM | 8511.919 | 1403 | 5687.79 | -4439.18 |
| XGBoost A2-C03 | 8511.919 | 1403 | 5137.64 | -4965.47 |
| XGBoost A2-C06 | 8511.919 | 1403 | 5097.90 | -4931.72 |

September EDA examined the full labeled file, including claims later assigned to validation and reserved test. These are retrospective results, not independent prospective confirmation. Filing-time inputs are an Advisor-authorized assumption; individual feature definitions, timestamps and lineage remain unverified. High-loss underprediction persists. Gate 4 reproduction matched predictions exactly but used Python 3.13.2 rather than 3.13.5, so exact environment confirmation remains conditional. Reproductions do not establish random-seed stability.

No in-sample XGBoost error or repeated-seed evidence exists. Fold variability and reproduction findings are documented in the October report. All released predictions pass integrity checks; the follow-up is evaluation-eligible but not retained under the approved policy.

## Next confirmation

- **observed problem**: Historical EDA exposure, anonymous predictor timing, no independent prospective evidence; large-loss underprediction.
- **hypothesis**: The frozen A2-C03 configuration retains improvement over both frozen constants on genuinely independent claims with verified filing-time inputs.
- **change**: Evaluate the unchanged retained model on newly supplied, temporally separated claims after agreeing a protocol; do not tune on that cohort.
- **controls**: Freeze depth 7, 300 trees, seed 42, preprocessing, existing baseline constants, original-unit MAE and training-derived diagnostic thresholds; preserve existing partitions.
- **metric**: Original-scale MAE on identical new cohort IDs; high-loss diagnostics reported separately.
- **success criterion**: Strictly lower MAE than both frozen constants; exact claim coverage and valid filing-time provenance. Pre-register uncertainty and business criteria before results are seen.
- **dependencies**: Advisor/team-approved protocol, feature definitions and lineage, prediction/outcome timestamps, independent data access, governance review and execution resources.
- **risks**: Temporal/group dependence, distribution shift, limited high-loss support and business relevance remain unresolved. Further validation-driven tuning requires a revised team-approved evaluation strategy.
- **execution status**: PROPOSED_ONLY_NOT_EXECUTED

## Evidence references

- `artifacts/october/gate 2/baselines/baselines-20261025T034742Z-0e9ea822/baseline_run_receipt.json`
- `artifacts/october/gate 3/comparison_inputs/glm-20261103T055706Z-0748a4b5/run_receipt.json`
- `artifacts/october/gate 3/comparison_inputs/glm-20261103T055706Z-0748a4b5/provenance.json`
- `artifacts/october/gate 3/runs/xgboost-task4/run_receipt.json`
- `artifacts/october/gate 3/xgboost_readiness_decision_20261112.md`
- `artifacts/october/gate 3/xgboost_results_20261112/model_comparison.csv`
- `artifacts/october/gate 3/comparisons/comparison-20261107T175139Z-d1372e77/model_high_loss_diagnostics.csv`
- `artifacts/october/gate 4/candidate_decision/decision-20261124T070336Z-7db5f673/october_candidate_decision.json`
- `artifacts/october/gate 4/candidate_decision/decision-20261124T070336Z-7db5f673/development_evidence.json`

Full explanation: [October report](october_report.md). Decision JSON: `artifacts/october/gate 4/candidate_decision/decision-20261124T070336Z-7db5f673/october_candidate_decision.json`. No team/Advisor approval is inferred; the next experiment is proposed, not executed.
