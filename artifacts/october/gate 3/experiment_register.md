# Gate 3 experiment register

Owner: Hector.

This register tracks the team's experiments and the evidence needed to review them. Existing results below came from saved Gate 2 comparison files. The baseline check below independently recalculates the constants and scores from the saved evidence. A missing local result does not establish that a teammate has not run it elsewhere.

## Recorded baseline runs

A mean baseline predicts the training average for every claim. A median comparator predicts the training middle value for every claim. MAE is the average absolute prediction error; lower is better.

Both executions used `october-split-v1`, 141,238 training claims and 28,248 validation claims. Scores are in original loss units. Each execution produced both predictors; the two rows for an execution are not separate workflow runs.

| Register ID | Saved run ID | Predictor | Predicted amount | Validation MAE | Claims | Evidence |
| :--- | :--- | :--- | ---: | ---: | ---: | :--- |
| BASE-001-MEAN | baselines-20261025T034722Z-10e9a301 | Training mean | 3038.297456137867 | 1959.6309163876397 | 28,248 | [Comparison](../gate%202/baselines/baselines-20261025T034722Z-10e9a301/baseline_comparison.csv) |
| BASE-001-MEDIAN | baselines-20261025T034722Z-10e9a301 | Training median | 2116.665 | 1802.7938540781647 | 28,248 | Same execution as BASE-001-MEAN |
| BASE-002-MEAN | baselines-20261025T034742Z-0e9ea822 | Training mean | 3038.297456137867 | 1959.6309163876397 | 28,248 | [Comparison](../gate%202/baselines/baselines-20261025T034742Z-0e9ea822/baseline_comparison.csv) |
| BASE-002-MEDIAN | baselines-20261025T034742Z-0e9ea822 | Training median | 2116.665 | 1802.7938540781647 | 28,248 | Same execution as BASE-002-MEAN |

The saved comparisons agree on both constants and both MAEs. This is a comparison of existing records, not a fresh reproduction.

### Baseline evidence locations

- Earlier execution: [receipt](../gate%202/baselines/baselines-20261025T034722Z-10e9a301/baseline_run_receipt.json), [mean predictions](../gate%202/baselines/baselines-20261025T034722Z-10e9a301/baseline_mean_predictions.csv), [median predictions](../gate%202/baselines/baselines-20261025T034722Z-10e9a301/baseline_median_predictions.csv).
- Later execution: [receipt](../gate%202/baselines/baselines-20261025T034742Z-0e9ea822/baseline_run_receipt.json), [mean predictions](../gate%202/baselines/baselines-20261025T034742Z-0e9ea822/baseline_mean_predictions.csv), [median predictions](../gate%202/baselines/baselines-20261025T034742Z-0e9ea822/baseline_median_predictions.csv).

The later receipt records code version, code and data hashes, software versions, fitted constants, prediction checks and automated test results. Runtime and original run owner are not supplied in the comparison tables; do not invent them. Consult the original evidence when completing detailed records.

### Worked record and baseline check

- **Status and purpose:** Both baseline workflows completed. The mean is the required simple benchmark; the median is a second benchmark because extreme claims pull the mean upward and the median minimizes absolute error among constant predictions on the fitting data.
- **Setup:** Fit each constant from the original loss values of the 141,238 training claims in `october-split-v1`. There are no input features, preprocessing steps, tuned settings or target transformations. Score the saved predictions on the same 28,248 validation claims. Do not convert or score any test losses.
- **Verification:** In a separate calculation, rebuild both constants from training losses. For each of the four prediction files above, match claims by ID, confirm exact validation coverage and one finite prediction per claim, and average the absolute differences from the actual validation losses. Check the split manifest and prediction file fingerprints against each receipt.
- **Result: PASS.** All four files matched their receipts and had exactly 28,248 predictions. Recalculated mean MAE was 1,959.630916387639 and median MAE was 1,802.793854078165 in both executions. Both constants and scores matched the saved results within numerical rounding. The median's error was about 156.84 loss units lower on this validation set.
- **Decision:** Keep both references for the candidate comparison. This verifies the baseline scores from saved predictions; it is not a new workflow execution or the required candidate audit.

## Existing Gate 2 preparation and verification

Closer inspection of the notebooks and Gate 2 receipts found completed preparation and technical verification in addition to the baseline executions. These support Gate 3 but are not candidate performance experiments:

- [Hector's preprocessing notebook](../../../notebooks/gate2_preprocessing.ipynb) implements both preprocessing branches and tests Ridge and XGBoost with artificial targets on 1,000 training rows. Saved outputs show finite predictions for all 28,248 validation inputs and the unseen/missing-label examples. No real validation loss or model MAE is used.
- [Rachel's training-fold notebook](../../../notebooks/gate2_training_folds.ipynb) saves five training-only folds, evaluates three constant predictors within those folds, implements the log-target inverse rule, and tests six Ridge settings with artificial targets. Its saved summary reports 36 of 36 checks passed and zero real-target GLM fits.
- [Fold-matched constant baselines](../gate%202/cv_folds/cv_constant_baselines.csv) provide training CV references. The saved notebook reports pooled out-of-fold MAE of 1,965.90 for the mean, 1,808.99 for the median and 1,809.78 for the inverse-log-mean constant. These are different evaluation rows from the validation benchmarks above and must remain separately labeled.
- [Leng's independent receipt](../gate%202/leng_verification/independent_receipt.json), run `leng-gate2-20261102T021120.871783Z`, records PASS for baseline/CV verification and embeds a fresh baseline reproduction, `baselines-20261102T020455Z-313e8d4d`, with matching prediction hashes. That rerun's standalone temporary files are not present here; the retained receipt is the available evidence.
- [Leng's preprocessing receipt](../gate%202/leng_verification/preprocessing/preprocessing_receipt.json), run `leng-gate2-20261102T021208.120836Z`, records PASS, 34 notebook code cells executed without errors, and independent preprocessing/target-inverse checks. It explicitly excludes real-candidate performance evaluation.

These are prior recorded checks by teammates, not fresh verification performed while starting this register. Leng's receipts report no formal gate approval. Their existence does not complete Hector's separate Gate 3 candidate audit.

## Pending evidence

These are work-tracking entries, not completed experiments. Assign a new experiment ID to each actual model run and retain failed runs and negative results.

| Item | Owner | Local evidence found | Still needed |
| :--- | :--- | :--- | :--- |
| Approach 1 regularized linear model | Rachel | [Completed candidate receipt](runs/glm-20261103T055706Z-0748a4b5/run_receipt.json) | Compare against Krish's reported table when available |
| Approach 2 XGBoost | Leng | [Proposed configuration](../gate%202/approach2_xgboost_config.json) | Actual run records and results; configuration records unresolved readiness and release-sequence decisions |
| Required model iteration | Leng | Reserved in Approach 2 configuration | One justified change, before/after evidence, and continue/stop decision |
| Model comparison table | Krish | No completed table found in this checkout | Table and the underlying run IDs and evidence used to build it |
| Optional feature inclusion/exclusion test | Hector | No run or deferral recorded here | Decide whether to run a motivated test or record a reason for deferral |
| Independent Gate 3 audit | Hector | GLM candidate audit signed off by Hector | Reproduce and compare against Krish's table |

## How to add the next experiment

Use the [experiment record template](../gate%201/experiment_record_template.md) for the detailed record. Before execution, state the hypothesis, changed variable and planned comparison. After execution, record the actual setup, results, evidence and next decision. Give reruns new IDs and preserve earlier records.

Do not treat proposed configurations or synthetic compatibility checks as real-target model results. Keep validation MAE separate from training CV scores, and report MAE in original loss units. Preserve claim IDs for prediction alignment. The internal test partition remains reserved under the current project evaluation rules.

## Independent comparison worksheet

Use the later saved baseline execution as the reference. Fill in the candidate rows from the team's evidence and compare this worksheet with Krish's table. Record the run ID and any discrepancy alongside each row. Keep the training CV metric and validation MAE in separate columns. The mean and median training CV values below are pooled across held-out training folds and come from Leng's Gate 2 verification receipt.

| Model | Training CV MAE | Validation MAE | Validation claims | Improvement over mean | Improvement over median | Complexity | Runtime |
| :--- | ---: | ---: | ---: | ---: | ---: | :--- | :--- |
| Training mean | 1,965.90 | 1,959.63 | 28,248 | 0.00 | −156.84 | One constant | Unrecorded |
| Training median | 1,808.99 | 1,802.79 | 28,248 | 156.84 | 0.00 | One constant | Unrecorded |
| Rachel's linear model | 1,245.40 | 1,250.45 | 28,248 | 709.18 | 552.34 | Ridge with penalty 100 | 89 seconds |
| Leng's XGBoost | Pending | Pending | Pending | Pending | Pending | Pending | Pending |

Improvement is benchmark validation MAE minus candidate validation MAE, computed before rounding. A positive value means the candidate reduced average error. Add an iteration row if Krish's comparison reports a separate validation release for it.

## Candidate audit checklist

Choose a candidate with a run receipt, a saved validation prediction file, and code or fitting records for that same run. Record its run ID and mark each check Pass, Discrepancy, or Evidence missing.

1. **Split.** Match the receipt to the saved split and training folds. Check that model fitting and tuning used training claims, that evaluation used the 28,248 designated validation claims, and that the test claims stayed reserved.
2. **Preprocessing.** Follow the fitting code or records. Check that category rules and any scaling were learned from the fitting claims in each fold and reused when predicting on the claims held out from that fit. Check that claim ID and actual loss were excluded from model inputs.
3. **Predictions.** Match the saved file to the receipt using its file fingerprint when provided. Check for one finite prediction per validation claim, with no missing, extra or duplicate IDs. Check how the model converted predictions back to original loss units if it trained on a transformed target.
4. **MAE.** Match predictions and actual amounts by claim ID. Average the absolute errors and compare with the receipt and table. Record the recomputed score, claim count and any difference.

The GLM prediction file passed an additional ID coverage, file fingerprint, and MAE calculation from saved predictions. Hector can use its run code and receipt to review fitting and preprocessing. Krish's table is needed to compare the independently assembled rows against the team's reported comparison.

## First candidate run

**Status: completed on November 2, 2026** The run used Rachel's proposed configuration. The [run receipt](runs/glm-20261103T055706Z-0748a4b5/run_receipt.json) records that basis for proceeding.

- **Owner and configuration:** Rachel, issue #44, [regularized linear model `approach1-glm-v1`](../gate%202/approach1_glm_config.json).
- **Question:** Can the model use the 130 approved inputs to reduce validation MAE below both constant benchmarks?
- **Training:** Use the five saved training folds. Fit the preprocessing and model inside each fold for the six proposed penalty settings. Compare all 30 fits by pooled held-out MAE in original claim units. Under the proposed tie rule, choose the strongest penalty within one loss unit of the lowest pooled MAE.
- **Validation:** Refit the selected setting on all 141,238 training claims. Convert predictions from the log scale back to original loss units using the configured inverse rule. Save one prediction per validation claim and score the selected model on the 28,248 validation claims according to the team's approved release sequence. Reserve the test claims.
- **Evidence:** Keep the fold scores, failed attempts, selected settings, validation prediction file, runtime and run receipt. Record source, split, fold and configuration fingerprints and software versions in the receipt.
- **Review:** Add the run and its evidence to the comparison worksheet. Hector can then check the split, fitting code, prediction coverage and recomputed MAE against the receipt.

All 30 fits completed. Penalty strength 100 gave the lowest pooled training CV MAE and was selected under the one-unit tie rule. The final candidate was scored once by the shared evaluator. Its validation MAE was 1,250.45. The later check from the saved predictions reproduced that score without fitting or selecting another model.

Saved evidence: [fold results](runs/glm-20261103T055706Z-0748a4b5/cv_results.csv), [validation predictions](runs/glm-20261103T055706Z-0748a4b5/validation_predictions.csv), and [runner](../../../scripts/run_glm_candidate.py). An initial launch stopped before creating a run because the verifier imported an optional notebook dependency. Moving that import into the notebook execution function let the candidate runner reuse the definition loader.

## GLM candidate audit findings

Reviewed run `glm-20261103T055706Z-0748a4b5` using its receipt, saved artifacts and the code identified by the receipt.

| Check | Finding |
| :--- | :--- |
| Split | Pass. The source and split fingerprints matched. Rebuilding the five folds from the sorted training claim IDs and seed 42 matched every saved assignment. Fold fitting groups contained 112,990 or 112,991 claims. Their held-out groups contained 28,248 or 28,247 training claims. |
| Preprocessing | Pass by code inspection. The runner creates fresh preprocessing for each fold and learns rare categories, encodings and scaling from the four fitting groups. It applies those rules to the held-out group. The final pipeline fits on all training claims. Claim ID identifies rows and actual loss supplies the answer to learn. The model inputs contain only the 130 predictors. |
| Predictions | Pass. The saved file fingerprint matches the receipt and covers every validation ID exactly once with finite predictions. The recorded target wrapper converts its log-scale output back to original loss units. |
| MAE and setting | Pass. The saved predictions reproduce validation MAE of 1,250.453333128099 to rounding. The 30 saved fold results cover all training claims for each setting. Reapplying the tie rule selects penalty 100, with pooled training CV MAE of 1,245.404448458671. |

Hector independently ran the prediction and MAE checks and reported a pass for all 28,248 validation claims. His recalculated and reported MAE both displayed as 1,250.45333313. On November 2, 2026, Hector also confirmed the split and preprocessing checks and signed off on all four checks for this GLM candidate. The comparison against Krish's table is pending.
