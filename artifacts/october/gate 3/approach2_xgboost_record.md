# Approach 2: XGBoost experiment record

**Task 4 / issue #45: real experiment and independent saved-prediction audit complete.**
Owner: Leng Lim. Run date: November 12, 2026 (America/New_York).
GitHub #45 is titled “Task 12: Train Approach 2 and run one iteration.”

**Retain A2-C03: max_depth=7, learning_rate=0.05.** The depth-8 follow-up did not
reach the agreed 1.0 pooled OOF MAE improvement. No further configuration was run.

## Verified before and after

| Evidence | Initial A2-C03, depth 7 | Follow-up A2-C06, depth 8 |
|---|---:|---:|
| Pooled training OOF MAE | 1163.675269514285 | 1164.085199824779 |
| Validation MAE | 1167.515313650092 | 1166.681104191661 |
| Learning rate | 0.05 | 0.05 |
| Boosting rounds | 300 | 300 |

Depth 8 **increased** pooled OOF MAE by 0.409930310494, so the
change is not kept. Its validation MAE decreased by 0.834209458430;
that observation does not override the pre-recorded training-CV keep rule.
Validation did not choose the setting or the retained depth.

## Initial search and training-only rationale

Five settings used the same five saved training folds, with a fresh preprocessor
fit inside each four-fold fitting portion. Selection used unrounded pooled OOF
MAE and the checked-in one-unit simplicity/runtime tie rule.

| Candidate | Depth | Learning rate | Pooled OOF MAE | Fold mean MAE | Fold sample SD | CV runtime seconds |
|---|---:|---:|---:|---:|---:|---:|
| A2-C01 | 3 | 0.05 | 1189.972449 | 1189.972480 | 10.994128 | 35.67 |
| A2-C02 | 5 | 0.05 | 1169.361674 | 1169.361706 | 10.827412 | 39.65 |
| A2-C03 | 7 | 0.05 | 1163.675270 | 1163.675318 | 10.600038 | 41.25 |
| A2-C04 | 3 | 0.1 | 1178.651833 | 1178.651857 | 11.483206 | 36.33 |
| A2-C05 | 5 | 0.1 | 1166.852746 | 1166.852781 | 10.769628 | 39.36 |
| A2-C06 | 8 | 0.05 | 1164.085200 | 1164.085247 | 10.020553 | 46.69 |

Initial training-only evidence at learning_rate=0.05: A2-C01 depth 3 pooled OOF MAE 1189.972448927673; A2-C02 depth 5 pooled OOF MAE 1169.361674111248; A2-C03 depth 7 pooled OOF MAE 1163.675269514285. Parent A2-C03 uses depth 7. The deepest depth at this learning rate was selected; test one deeper level for additional nonlinear structure. Change only max_depth to 8; all other settings stay fixed. Validation is not an input.

The controller saved this recommendation **before the first validation release**.
After that release, the runner froze the identical setting/rationale in
[followup_plan.json](runs/xgboost-task4/followup_plan.json) before the sixth configuration.
Only `max_depth` changed. Seed, learning rate, folds, target, preprocessing and all
other model settings remained fixed.

## Comparison using the same validation IDs

| Model | Independently verified validation MAE |
|---|---:|
| training_mean_baseline | 1959.630916387640 |
| training_median_baseline | 1802.793854078165 |
| frozen_glm | 1250.453333128099 |
| xgboost_initial | 1167.515313650092 |
| xgboost_followup | 1166.681104191662 |

The retained depth-7 model improves validation MAE over the frozen GLM by
82.938019 original loss units.
The table reports frozen comparison evidence; it does not release the test set
or authorize a new tuning round. No GLM or baseline was refit.

## Data, model and approval

- Training: 141,238 claims. Validation: 28,248 claims. Test IDs: 18,832 reserved.
- Frozen split: `october-split-v1`; manifest SHA-256 `18e69673953fa61cbbabdd0421e83d31bd46b6f93356a2227793c6013e0850f1`.
- Source SHA-256: `74037cb248a1064e4d578692a4f4e5d8492ed1b2033daf643496e1b68b14ae03`.
- Fold SHA-256: `82fb7f3d9899af71a61f3e3f1b0117f88ac97b0255070253fd8190ec2c7bfcd1`.
- Inputs: 116 native categorical and 14 continuous predictors; exclude ID, target, partition and derived labels.
- Preprocessing: Hector's actual notebook definitions; fit-local rare threshold 30, training-derived categorical vocabulary, unknown/missing default branch; continuous features unscaled.
- Model: CPU histogram XGBoost 3.1.1, identity target, `reg:absoluteerror`, 300 trees, seed 42, four threads. Full parameters and versions are in the receipt.
- Approval: the [November 12 scoped readiness decision](xgboost_readiness_decision_20261112.md), recorded at Leng's direction. Leng is the only evidenced approver; no other teammate signature is inferred.
- Sequence: five initial CV settings, one initial full-training refit/validation release, one frozen depth-only follow-up on five folds, one follow-up full-training refit/validation release. No early stopping, retry, extra candidate or test prediction.

The earlier technical-only approval, blocked preflight, original audit and
[three-fix re-audit](xgboost_reaudit/report.md) remain historical evidence.

## Budget and provenance

Training ran from 2026-11-12 02:16:50 EST to 2026-11-12 02:21:45 EST.
Elapsed time: **294.80 seconds (4 minutes 55 seconds)**.
Recorded fitting-compute time: **198.31 seconds**, below
10,800 seconds. Every fit began before the November 12 11:59 p.m. EST deadline.
Exactly **30 CV fits and 2 full-training refits** completed; **0 failures/retries**.
The fitting code is the unchanged re-audited runner. Training commit:
`98a437544ced5f504ead1cd9740c2f94248a644b`. Actual interpreter/packages and commands are recorded
for every stage; `caffeinate -i` covered the campaign.

## Independent verification and artifacts

The [saved-prediction audit](xgboost_results_20261112/results_audit.json) passes.
It independently recomputed all six pooled OOF scores and all 30 fold MAEs using
`math.fsum`, checked fold membership/ID coverage, fold mean/sample SD, one-setting
change, pre-validation recommendation, frozen rationale timing, keep threshold,
all saved validation scores and the baseline/GLM comparison. Artifact hashes and
model JSON round trips match. Verification rescored existing predictions; it
introduced no model fit or new candidate.

The reserved test partition was skipped before numeric loss conversion and was
never fitted, tuned, predicted or evaluated. Source-byte hashing/ID checks do not
compute test target results. September full-file EDA is prior exposure, so this
partition is not claimed to be historically unseen.

**Retained artifact:** [initial_model.json](runs/xgboost-task4/initial_model.json),
with [initial_preprocessing.json](runs/xgboost-task4/initial_preprocessing.json).
The `final_*` files describe the recorded follow-up release, not the retained
model. Use the [retained-model manifest](xgboost_results_20261112/retained_model_manifest.json)
for exact paths and hashes.

- [Run receipt](runs/xgboost-task4/run_receipt.json)
- [Campaign log](xgboost_execution_20261112/campaign.log)
- [Controller receipt](xgboost_execution_20261112/automation_receipt.json)
- [CV results](xgboost_results_20261112/cv_results.csv)
- [Comparison CSV](xgboost_results_20261112/model_comparison.csv)
- [Artifact inventory](xgboost_results_20261112/artifact_inventory.json)
- [Plain-language explainer](approach2_xgboost_explainer.md)

Validation reuses the planned development partition, not a final test estimate.
Fold variability is not a repeated-seed confidence interval. High-loss claims,
rare categories, anonymous fields and unconfirmed grouping/time structure remain
limitations. Stop here under the approved budget and retain depth 7.
