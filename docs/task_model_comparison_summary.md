# October model comparison and diagnostics

Implemented shared-evaluator comparison, exact prediction validation, baseline verification, training-derived target bins and tails, descriptive CV gaps, stability summaries, failure reporting and reproducible plots. No models were fitted, tuned or selected.

Run: `comparison-20261107T175139Z-d1372e77`. Frozen manifest: `october-split-v1`; 28,248 validation claims. Artifacts: `artifacts/october/gate 3/comparisons/comparison-20261107T175139Z-d1372e77`.

| Model | Run ID | Validation MAE | Delta vs mean | Delta vs median | Improvement vs mean | Improvement vs median |
|---|---|---:|---:|---:|---:|---:|
| Training mean | baselines-20261025T034742Z-0e9ea822 | 1959.630916 | 0.000000 | 156.837062 | 0.00% | -8.70% |
| Training median | baselines-20261025T034742Z-0e9ea822 | 1802.793854 | -156.837062 | 0.000000 | 8.00% | 0.00% |
| Ridge GLM | glm-20261103T055706Z-0748a4b5 | 1250.453333 | -709.177583 | -552.340521 | 36.19% | 30.64% |

Diagnostic findings (original loss units):

| Training-derived bin | Validation support | MAE | Mean signed error |
|---|---:|---:|---:|
| 0–25% | 7,041/28,248 | 677.30 | 660.53 |
| 25–50% | 7,053/28,248 | 546.61 | 251.50 |
| 50–75% | 7,152/28,248 | 938.00 | -325.35 |
| 75–90% | 4,180/28,248 | 1859.08 | -1259.89 |
| 90–95% | 1,419/28,248 | 2987.48 | -2235.91 |
| 95–99% | 1,109/28,248 | 4651.60 | -3378.96 |
| 99–100% | 294/28,248 | 9596.42 | -8438.42 |

Ridge overpredicts the lower-loss half on average and underpredicts the upper-loss half. Error increases strongly in the upper tail; these slices describe behavior and do not select a model.

- loss > training p95, threshold 8511.919000: 1,403/28,248 claims (4.97%); MAE 5687.79, mean signed error -4439.18, median absolute error 5164.69, maximum absolute error 49269.89. Negative signed error indicates underprediction.
- loss > training p99, threshold 13900.776800: 294/28,248 claims (1.04%); MAE 9596.42, mean signed error -8438.42, median absolute error 8836.32, maximum absolute error 49269.89. Negative signed error indicates underprediction.
- Ridge GLM: validation minus CV fold-mean MAE is 5.048837; pooled OOF MAE 1245.404448. In-sample training MAE is unavailable, so a training generalization gap cannot be established.
- Ridge GLM: 5 CV folds, mean 1245.404496, sample SD 12.641633, range 1231.839843–1261.085593. This measures fold variability, not seed or repeated-training stability.

Failures and unavailable evidence:

- XGBoost: INCOMPLETE — Only proposed configuration available; no candidate MAE assigned

GLM predictions passed exact coverage and numeric checks. Target-bin support reconciles to the full validation population; see `model_target_bin_diagnostics.csv` for all seven bins. No seed/repeated-run evidence is available. The GLM receipt measures 89.03 seconds for the whole workflow, not isolated training/prediction; hardware and post-encoding coefficient count are unavailable. Runtimes do not support a computational ranking.

Evidence: GLM receipt, CV table and predictions are verbatim snapshots from Hector’s unmerged branch at commit `ab331538eba349e19a326ff6d87c395ccdb1a742`, explicitly authorized by Krish. `comparison_inputs/.../provenance.json` records original paths and hashes. XGBoost remains incomplete. Numeric predictions alone cannot prove target scale; the producer’s original-unit evaluator receipt supplies that evidence.

Files: `scripts/model_comparison.py`, `tests/test_model_comparison.py`, `docs/october_model_comparison_guide.md`, this summary, four evidence snapshot files under `artifacts/october/gate 3/comparison_inputs/`, and the run directory containing comparison, bins, tails, overfitting, stability, failures, candidate inventory, two plots and a run receipt.

Reproduce from repository root: `python3 -m scripts.model_comparison`. Tests: `python3 -m unittest discover -s tests`.

Next review questions: confirm integration of the GLM evidence; obtain the completed XGBoost receipt and predictions; request in-sample metrics, measured fit/predict runtimes and hardware details; review upper-tail underprediction. Diagnostics remain descriptive; overall original-scale validation MAE is primary. No winning model is selected and no hyperparameter changes are approved. Test targets remain untouched.

Validation checklist:

- Frozen source verified: PASS
- Frozen manifest verified: PASS
- Shared evaluator reused: PASS
- Baseline comparability verified: PASS
- Candidate artifacts discovered: PASS
- Prediction IDs validated: PASS
- All valid models evaluated on identical claims: PASS
- Original-scale validation MAE calculated: PASS
- Baseline deltas calculated: PASS
- Complexity documented: PASS
- Runtime documented or explicitly unavailable: PASS
- Target-distribution diagnostics generated: PASS
- High-loss diagnostics generated: PASS
- Support counts documented: PASS
- Overfitting diagnostics generated: PASS
- Stability assessed or explicitly unavailable: PASS
- Prediction failures identified: PASS
- Automated tests passed: PASS
- Documentation generated: PASS
- Internal test targets untouched: PASS
- Completion summary generated: PASS
- Run receipt generated: PASS

Automated validation: all 61 repository tests passed, including 26 comparison tests. Two independent complete executions produced byte-identical output for all seven CSV tables. Receipt artifact hashes were verified. Plots were visually reviewed.
