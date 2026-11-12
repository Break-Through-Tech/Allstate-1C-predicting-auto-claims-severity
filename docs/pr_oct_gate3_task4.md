Title: Complete Gate 3 Task 4: XGBoost and one controlled depth iteration

Closes #45.

Adds the guarded XGBoost runner, scoped readiness record, automatic stage controller,
and independent saved-prediction audit using the frozen split, five saved folds,
fold-local preprocessing and shared original-unit MAE evaluator.

Five initial settings selected depth 7 at learning rate 0.05. The one justified
follow-up changed only depth to 8:

| Metric | Depth 7 | Depth 8 |
|---|---:|---:|
| Pooled OOF MAE | 1163.6753 | 1164.0852 |
| Validation MAE | 1167.5153 | 1166.6811 |

Retain **depth 7**: depth 8 worsened CV MAE by 0.4099 and missed
the pre-recorded 1.0 improvement threshold. Its slightly lower validation MAE
does not override the training-only keep rule. The retained model is
`initial_model.json`; the retained-model manifest identifies its preprocessing
and hashes.

Validation: 87 tests passed; independent recomputation matched all six pooled OOF
scores, 30 fold scores and both saved validation scores. Exactly 30 CV fits and
two full-training refits completed, with no failures/retries, in 4m55s. The
reserved test partition was excluded. No settings were chosen from validation.

Full results and artifacts:
`artifacts/october/gate 3/approach2_xgboost_record.md` and
`artifacts/october/gate 3/xgboost_results_20261112/`.

The recorded November 12 readiness decision names Leng as the only evidenced
approver. Earlier audits and blocked preflight evidence are preserved. The
original Gate 2 checkout and its untracked files remain in place.
