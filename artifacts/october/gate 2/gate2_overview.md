## Task 1 Leakage-safe preprocessing

Implemented GLM and XGBoost preprocessing using `october-split-v1`, with 141,238 training claims and 28,248 validation claims. Source and partition manifest hashes matched the recorded metadata. Test claims were excluded from the working predictor data.

Inputs contain only the 116 categorical and 14 continuous predictors. Schema checks reject missing, renamed, duplicate, or unexpected columns, including `id`, `loss`, `log1p_loss`, and `partition`. Missing or nonfinite continuous values are rejected. Claim IDs remain available as row indices for alignment.

### Training-only fitting

Category frequencies, rare groups, encoding vocabularies, and GLM scaling statistics are learned from training inputs only. Separate cloned pipelines recomputed rare groups independently on illustrative training subsets. Validation transformation left fitted pipeline state unchanged.

A category is rare when its training count is below 30. Full training counts identified 352 rare levels across 30 fields. These levels are grouped into `__rare__`.

### GLM preprocessing

Categorical fields use rare grouping followed by one-hot encoding, retaining every learned category column. Unseen or missing labels map to the learned rare group where one exists; otherwise, their field’s encoding is all zeros. The encoder excludes the internal `__unseen__` placeholder from its vocabulary.

Continuous fields are standardized using training means and population standard deviations. The output contains 808 columns: 794 categorical columns and 14 continuous columns, stored as a sparse matrix.

### XGBoost preprocessing

Categorical fields use training derived rare groups and fixed, unordered categorical vocabularies. Unseen and missing labels become missing categorical values. Continuous values remain unchanged. The output retains 130 columns.

### Validation impact

Counts use predictor labels only, without validation loss:

- 490 claims contain at least one training rare label.
- 12 claims contain unseen labels, totaling 13 field occurrences.
- 3 claims belong to both groups.
- 499 distinct claims contain either condition.

### Verification

Both branches passed schema rejection, unseen label, missing label, independent fitting, and unchanged state checks. GLM processed values were finite; XGBoost categorical missing values matched the intended fallback behavior.

Small Ridge and XGBoost compatibility models used 1,000 training rows and artificial targets. Each produced one finite prediction per row for all 28,248 validation claims and both sets of 116 robustness examples. Shuffling 200 validation claims preserved predictions when realigned by claim ID.

These were compatibility checks, not performance evaluations. No validation MAE was computed, and target handling and model tuning remain separate team tasks.

### Environment and review status

Python 3.13.2; pandas 2.3.2; NumPy 2.3.3; SciPy 1.18.1; scikit-learn 1.7.2; XGBoost 3.1.1. XGBoost required the macOS OpenMP runtime, installed using `brew install libomp`.

Implementation checks passed in the interactive notebook. A clean notebook rerun, reproducible handoff receipt, and independent team verification remain pending. The local Gate 1 documents still mark the preprocessing plan and design approval as pending; this work does not constitute team approval.

## Task 3 Training folds and target handling

Owner: Rachel Cheung · Issue #40. Work and checks are in [`gate2_training_folds.ipynb`](../../../notebooks/gate2_training_folds.ipynb) (36 of 36 checks pass). The notebook is self-contained and imports nothing from `scripts/`.

### Cross-validation folds

The 141,238 training claims are split into 5 folds with `KFold(shuffle=True, random_state=42)` over IDs sorted by integer `id`, following policy `OCT-G1-T4-PROPOSAL-v1`. Assignment uses IDs only. Held-out folds contain 28,248, 28,248, 28,248, 28,247 and 28,247 claims. No validation or test claim appears in any fold.

The folds are saved as [`cv_folds/october_cv_folds.csv`](cv_folds/october_cv_folds.csv) (`id,fold` only; SHA-256 `82fb7f3d9899…`) with a [metadata file](cv_folds/october_cv_folds_metadata.json) recording the method, counts, manifest hash and environment. The notebook refuses to overwrite a saved fold file that differs. Rebuilding gives identical folds regardless of input order. The folds assume claims are exchangeable; group and time structure remain an open Advisor question.

### September signals recomputed within the folds

Only training targets are read: validation and test rows are skipped before `loss` is parsed. Each signal October relies on was recomputed on every fold's fit portion (the four folds used for fitting):

| Signal | Fold fit portions | All training | September full file |
| :--- | :--- | ---: | ---: |
| Mean `loss` | 3,032.40 to 3,046.47 | 3,038.30 | 3,037.34 |
| Median `loss` | 2,111.07 to 2,122.61 | 2,116.66 | 2,115.57 |
| p95 `loss` | 8,493.97 to 8,546.60 | 8,511.92 | 8,508.54 |
| Skewness of `loss` / `log1p(loss)` | 3.65 to 4.27 / 0.098 to 0.107 | 4.006 / 0.102 | 3.795 / 0.097 |
| Pearson with `loss`: cont2, cont3, cont7 | 0.142 to 0.143, 0.108 to 0.111, 0.116 to 0.121 | — | 0.142, 0.111, 0.120 |

September's findings hold inside every fold. Gate 3 high-loss slices should use the training p95 of **8,511.92** (or each fold's own p95 inside CV), not the September value; every held-out fold has 1,334 to 1,464 claims above its fit portion's p95. Categorical level-to-target differences (FND-003) and FND-008 labels were not recomputed because no October decision uses them.

### Target transformation

**Decision: Approach 1 trains on `log1p(loss)`.** MAE rewards the median, and a least-squares fit on the nearly symmetric log scale converts back to a median-type estimate. Training-fold evidence without fitting any model: constants learned on each fit portion and scored on its held-out fold (pooled out-of-fold MAE, original `loss` units) give 1,808.99 for the median, 1,809.78 for `expm1(mean of log1p)` and 1,965.90 for the mean. The log-scale constant beat the mean in all 5 folds. These fold-matched constants are saved in [`cv_folds/cv_constant_baselines.csv`](cv_folds/cv_constant_baselines.csv) as the CV reference for Gate 3.

**Inverse rule** (`LogTargetRegressor` in the notebook): the model's log-scale output is clipped to `[log1p(min loss), log1p(max loss)]` learned from the rows it was fit on, then converted with `expm1`. Every prediction is therefore finite and positive, so no negative prediction reaches the evaluator. A non-finite model output raises an error and the run is logged as failed; predictions are never dropped or filled. No mean-bias correction is applied.

### Approach 1 configuration

[`approach1_glm_config.json`](approach1_glm_config.json) (`approach1-glm-v1`, written by the notebook) defines the regularized GLM for Gate 3 (#44): Hector's GLM preprocessing (rare grouping below 30, one-hot, standardized continuous), Ridge regression with the `lsqr` solver on `log1p(loss)`, and six `alpha` values from 1 to 100,000 (30 CV fits, within the 6-configuration cap). Selection uses the lowest pooled out-of-fold MAE in `loss` units, with ties within 1 unit going to the larger `alpha`. Only the selected configuration is scored on validation, once.

A smoke test fit every configuration on 2,000 training claims with artificial targets: each gave one finite, positive prediction per claim, handled made-up labels in all 116 fields, and kept predictions matched to claim IDs. No GLM was fit on real targets and no tuning budget was used.

Hector's GLM preprocessing classes are copied unchanged into the notebook. Fitted on the full training partition, they reproduce his results: 808 output columns and 352 rare levels across 30 fields.

### Environment and review status

Python 3.13; pandas 2.3.2; NumPy 2.3.3; SciPy 1.18.1; scikit-learn 1.7.2. scikit-learn and XGBoost are not yet pinned in `requirements.txt`.

Independent verification by Leng (#41) and team approval of the folds, target rule and configuration remain pending. No validation or test target was read.