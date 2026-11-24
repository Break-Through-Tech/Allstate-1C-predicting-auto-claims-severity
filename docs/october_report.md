# October model development report

## 1. Executive summary

The team investigated whether historical claim characteristics help estimate final paid loss. October milestone work (completed across October and November) established fixed data partitions, two constant benchmarks, a regularized linear model, a boosted-tree model, and a controlled tree-depth follow-up. The technical recommendation is **PROVISIONAL_CANDIDATE: XGBoost A2-C03**, pending team and Challenge Advisor review.

| Candidate | Validation MAE | Claims | Change vs mean | Change vs median | Improvement vs mean | Improvement vs median | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| Ridge GLM | 1250.453333 | 28248 | -709.177583 | -552.340521 | 36.189344% | 30.638030% | QUALIFIES |
| XGBoost A2-C03 | 1167.515314 | 28248 | -792.115603 | -635.278540 | 40.421673% | 35.238557% | PROVISIONAL_CANDIDATE |
| XGBoost A2-C06 | 1166.681104 | 28248 | -792.949812 | -636.112750 | 40.464243% | 35.284830% | NOT_RETAINED_BY_EXISTING_POLICY |

The retained candidate improves MAE by 40.42% against the mean and 35.24% against the median. These results support a provisional research candidate, not demonstrated operational usefulness. September EDA examined the full labeled file, including claims later assigned to validation and reserved test. These are retrospective results, not independent prospective confirmation. Filing-time inputs are an Advisor-authorized assumption; individual feature definitions, timestamps and lineage remain unverified. High-loss underprediction persists. Gate 4 reproduction matched predictions exactly but used Python 3.13.2 rather than 3.13.5, so exact environment confirmation remains conditional. Reproductions do not establish random-seed stability.

## 2. Business problem

The research question is whether claim information can help estimate a claim's final cost. This could inform future reserve research, but no improved reserving, handling speed, costs, customer outcomes or compliance has been demonstrated. The supplied population excludes claims closed without payment, so results do not establish performance for all incoming claims.

## 3. Data and evaluation approach

The authoritative historical file contains 188,318 claims and 132 columns: an ID, 116 anonymous categorical predictors, 14 anonymous continuous predictors, and `loss`. ID is a matching key, never a predictor. Split `october-split-v1` fixes 141,238 training, 28,248 validation and 18,832 reserved test claims (75/15/10). Source SHA-256: `74037cb248a1064e4d578692a4f4e5d8492ed1b2033daf643496e1b68b14ae03`; manifest SHA-256: `18e69673953fa61cbbabdd0421e83d31bd46b6f93356a2227793c6013e0850f1`.

Learned preprocessing and model fitting used training rows; five-fold cross-validation repeatedly held out one fifth of training to compare settings. Saved predictions were joined to validation truth by unique claim ID and independently rescored with the shared evaluator. No baseline was refitted or new model trained for this report. No additional internal test targets were inspected.

Mean absolute error (MAE) measures how far predictions are from recorded claim losses on average, without allowing overpredictions and underpredictions to cancel each other out. All numbers use original loss units; the available field documentation does not establish a currency denomination.

## 4. Baseline results

The training-mean baseline predicts 3038.297456 for every claim and has validation MAE 1959.630916. The training-median comparator predicts 2116.665000 and has MAE 1802.793854. Both constants were fitted only on training targets, according to their code and receipts, and their saved predictions were verified here. The newer Gate 4 baseline reproduction agrees.

The mean is the average training loss; the median is the middle training loss. A median minimizes absolute error among constant predictions on the fitting population, making it an essential reference. Beating the mean alone is insufficient.

## 5. Candidate models

The Ridge GLM combines encoded features with regularized coefficients to limit overly large effects; it predicts a transformed loss and converts back to original units. Its frozen penalty is 100, with 808 encoded inputs. XGBoost combines 300 small decision trees to capture nonlinear patterns; the retained model has maximum depth 7 and learning rate 0.05. The follow-up changed only depth to 8. The executive table displays rounded results; the decision CSV and JSON retain full-precision values used by the rule.

The previously published November 7 comparison marked XGBoost incomplete. That was correct then; the November 12 committed campaign now supplies its predictions, receipts and audit. This report uses the newer evidence without rewriting historical artifacts.

## 6. Candidate decision

A provisional candidate must have valid evaluation evidence and validation MAE strictly below **both** constants on the exact same claims. A tie with either baseline fails. A2-C03 is the lowest-error policy-retained family candidate and strictly beats both constants. A2-C06 also beats both and has a 0.834209 lower validation MAE, but it failed the adopted training-only retention rule: pooled out-of-fold MAE worsened by 0.409930 instead of improving by at least 1.0. Reversing that decision using validation would reopen the experiment. The Gate 1 across-family one-unit tie proposal was not independently approved globally; no across-family tie affects this result (A2-C03 is 82.938019 below GLM).

This is a generated technical recommendation, not a recorded team or Advisor approval. It does not release the test set or authorize deployment. Run IDs and full-precision decision flags are in the formal record.

## 7. Diagnostic findings

| Candidate | Threshold | Claims / 28,248 | MAE | Mean signed error |
|---|---:|---:|---:|---:|
| Ridge GLM | 8511.919 | 1403 | 5687.79 | -4439.18 |
| XGBoost A2-C03 | 8511.919 | 1403 | 5137.64 | -4965.47 |
| XGBoost A2-C06 | 8511.919 | 1403 | 5097.90 | -4931.72 |

These high-loss slices use the training 95th-percentile threshold, not a threshold chosen from validation results. Negative signed error means underprediction. The 1,403 claims represent 4.97% of validation; the training-p99 slice has 294 claims (1.04%). The latter is a much smaller slice, so conclusions about rare extremes remain limited. Bin tables cover all 28,248 claims and show overprediction toward the low end and underprediction at the high end. Slice diagnostics describe weaknesses; they do not replace overall MAE as the selection metric.

The retained XGBoost CV pooled MAE is 1163.675270; its five fold scores have sample standard deviation 10.600038. Its validation score is about 3.84 above its CV fold mean. No in-sample XGBoost MAE is available, so a true training-to-validation gap cannot be computed. GLM's pooled CV MAE is 1245.404448; the reproduction reports training MAE 1240.423079, with a roughly 10.03 difference from the original validation score. That is a cross-run descriptive comparison, not the original fit's exact generalization gap. These small differences do not prove absence of overfitting.

Rachel's GLM reproduction receipt reports near-identical predictions (maximum difference about 3.64e-12); the narrative record uses looser bounds and attributes variation to solver tolerance. We use the machine-readable receipt for exact numeric assertions. Hector's XGBoost reproduction matches saved predictions and model bytes but has the Python patch mismatch described above. Reproduction agreement is distinct from random-seed or prospective stability; no repeated-seed assessment exists.

All three released candidate prediction files passed coverage, numeric and recorded-score checks; no rows were repaired or dropped. XGBoost reports zero campaign failures/retries. GLM's 89-second measurement covers its whole search/refit workflow; XGBoost's 294.80-second campaign covers 30 CV fits and two releases, with 198.31 seconds of recorded fitting compute. These workloads and environments differ, so runtime does not support a fair speed ranking.

## 8. September EDA exposure

September EDA used the **full labeled historical dataset** before the split was frozen. In `notebooks/data-understanding.ipynb`, zero-based cell 5 loads the full CSV; zero-based cells 15, 34 and 48 inspect loss and predictor-target relationships without an October partition filter. Saved September target, categorical and continuous summaries and the Recommendation Register confirm that findings informed the later preprocessing, model-family and diagnostic plans.

Thus later validation and reserved-test observations and targets had already contributed to exploration. Training-only preprocessing does not erase that exposure. Three issues must be distinguished: (1) direct fitting leakage, for which the reviewed code/receipts enforce training-only boundaries and do not establish a violation; (2) prior exploratory exposure, which is established; and (3) repeated validation-based selection, whose risk grows with reuse. GLM and two XGBoost releases, baseline scoring, diagnostics and reproduction audits reuse the validation population. Rescoring fixed predictions is not a new experiment, but neither does it create independent evidence.

The reserved test remained uninspected during this report and October modeling according to receipts, but it is not historically unseen. Its future authorized evaluation cannot undo September exposure. Genuinely independent data is needed for stronger confirmation.

## 9. Retrospective validation and filing-time use

The October results provide retrospective evidence of predictive performance on historical claims. They **do not establish** reliable or useful estimates at first filing, because availability and timing of individual anonymized predictors have not been independently verified.

The Advisor's October 12 written response, documented in Gate 1 signoff (the recommendation register uses October 13), permits assuming fields are available at filing/model use. This is a project assumption, not verified field-by-field lineage or timestamps. Some historical fields could have been recorded or updated after filing; this is a potential risk, not proof of post-filing leakage.

Future claims may differ in mix, inflation, repair costs, underwriting or reporting processes. Those are potential distribution-shift risks, not observed findings in this evaluation. Independent or temporally separated data, defined prediction/outcome timestamps, prospective validation and an operational workflow assessment are needed before usefulness can be established.

## 10. Responsible use and next confirmation

Unknown field meanings and group/time structure limit interpretation, dependence checks and fairness assessment. Anonymization does not establish fairness or remove all privacy concerns. No evidence here supports claims of bias-free behavior, compliance, production readiness, or automated claim/payment decisions. Business success criteria and appropriate governance, fairness and privacy review must precede operational use.

Proposed next test: Evaluate the unchanged retained model on newly supplied, temporally separated claims after agreeing a protocol; do not tune on that cohort. Hypothesis: The frozen A2-C03 configuration retains improvement over both frozen constants on genuinely independent claims with verified filing-time inputs. Controls: Freeze depth 7, 300 trees, seed 42, preprocessing, existing baseline constants, original-unit MAE and training-derived diagnostic thresholds; preserve existing partitions. Success criterion: Strictly lower MAE than both frozen constants; exact claim coverage and valid filing-time provenance. Pre-register uncertainty and business criteria before results are seen. Dependencies: Advisor/team-approved protocol, feature definitions and lineage, prediction/outcome timestamps, independent data access, governance review and execution resources. Risks: Temporal/group dependence, distribution shift, limited high-loss support and business relevance remain unresolved. Further validation-driven tuning requires a revised team-approved evaluation strategy. This proposal was not executed. Exact Python-version reproduction remains a separate team prerequisite; it was not rerun here because that would refit a model.

## Verification scope

All 80 relevant decision, evaluator, comparison, partition and Gate 2 verification tests pass, including 19 new decision tests. The broader repository suite was attempted (106 tests) but produced 29 error entries in existing XGBoost-runner tests because `xgboost` is not installed in the reporting interpreter. This report evaluates saved predictions using pandas/NumPy; it does not claim an exact training environment or a passing full training-workflow suite. No unrelated tests or environments were changed.

## Evidence and reproduction

- `artifacts/october/gate 2/baselines/baselines-20261025T034742Z-0e9ea822/baseline_run_receipt.json`
- `artifacts/october/gate 3/comparison_inputs/glm-20261103T055706Z-0748a4b5/run_receipt.json`
- `artifacts/october/gate 3/comparison_inputs/glm-20261103T055706Z-0748a4b5/provenance.json`
- `artifacts/october/gate 3/runs/xgboost-task4/run_receipt.json`
- `artifacts/october/gate 3/xgboost_readiness_decision_20261112.md`
- `artifacts/october/gate 3/xgboost_results_20261112/model_comparison.csv`
- `artifacts/october/gate 3/comparisons/comparison-20261107T175139Z-d1372e77/model_high_loss_diagnostics.csv`
- `artifacts/october/gate 4/candidate_decision/decision-20261124T070336Z-7db5f673/october_candidate_decision.json`
- `artifacts/october/gate 4/candidate_decision/decision-20261124T070336Z-7db5f673/development_evidence.json`

Generated run: `decision-20261124T070336Z-7db5f673`. Reproduce verification and documents with `python3 -m scripts.candidate_report --write-docs`. Run decision tests with `python3 -m unittest discover -s tests -p test_candidate_decision.py`. The receipt records input, report and decision hashes, actual library versions, generation Git revision and dirty-tree state separately from the eventual report commit.
