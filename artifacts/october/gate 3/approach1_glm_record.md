# Approach 1 Experiment Record: Regularized GLM

Owner: Rachel Cheung · Issue #44 · Configuration [`approach1-glm-v1`](../gate%202/approach1_glm_config.json) · Plain-language summary: [Approach 1 explainer](approach1_glm_explainer.md)

**Result:** the ridge model on `log1p(loss)` with penalty 100 has a validation MAE of **1,250.45** on 28,248 claims. That is 709.18 loss units (36.2%) below the training-mean baseline and 552.34 (30.6%) below the training-median comparator. Its training CV MAE (1,245.40) is close to the validation score, and an independent reproduction matched the run.

## EXP-20261102-01 — Approach 1 ridge GLM, frozen search

**Owner:** Rachel Cheung (configuration and reproduction); run executed by Hector Baeza · **Date:** 2026-11-02 (run), 2026-11-10 (reproduction) · **Status:** completed
**Type:** candidate
**Compared against:** training-mean and training-median baselines `baselines-20261025T034742Z-0e9ea822`, and Krish's [model comparison](comparisons/comparison-20261107T175139Z-d1372e77/model_comparison.csv)

### Plan (frozen before running)
- **Hypothesis:** September found weak, mostly additive signals. A penalized linear model on the log scale should beat both constant predictors on held-out MAE, but will miss nonlinear effects and interactions.
- **Changed variable:** first run of Approach 1. The only tuned setting is the penalty strength `alpha`.
- **Planned comparison:** pooled out-of-fold MAE in `loss` units across the 5 training folds selects `alpha`. Ties within 1 loss unit go to the larger `alpha`. Only the selected model is scored on validation, once.

### Setup
- **Partition manifest:** `october-split-v1` · manifest SHA-256 `18e69673953f`
- **Fit on:** training partition (141,238 claims) · **CV:** [`october-cv-v1`](../gate%202/cv_folds/october_cv_folds.csv), 5 folds, seed 42, SHA-256 `82fb7f3d9899`
- **Scored on:** validation partition (28,248 claims), once · **Test partition used:** no
- **Feature set:** all 130 source predictors (`cat1`–`cat116`, `cont1`–`cont14`); `id` and `loss` excluded
- **Preprocessing (refit inside every fold and for the final model):** categorical levels seen fewer than 30 times in the fit rows grouped into one rare level per field (352 levels in 30 fields on the full training set); unseen levels go to the rare column; one-hot encoding of every learned level (794 columns); `cont1`–`cont14` standardized (14 columns). **808 model columns in total.**
- **Target handling:** `log1p(loss)`; inverse `expm1(clip(z, log1p(min fit loss), log1p(max fit loss)))`; non-finite output fails the run. No prediction needed clipping.
- **Model and settings:** scikit-learn `Ridge`, `solver="lsqr"`, `tol=1e-6`, `fit_intercept=True`. Search space `alpha` ∈ {1, 10, 100, 1,000, 10,000, 100,000}; **selected `alpha` = 100**.
- **Random seeds:** 42 for fold assignment only. Ridge with `lsqr` has no randomness.
- **Code version:** run at commit `404532c` with `scripts/run_glm_candidate.py` (SHA-256 `ea3d2e9e4146`) using the definitions in `notebooks/gate2_training_folds.ipynb` (SHA-256 `41b97634986d`). That script is on Hector's branch `hector/Oct-gate3-task1` (commit `ab33153`, PR #58, closed without merging) and matches the receipt hash; it is not on `main`. The run's files used here are the identical copies in [`comparison_inputs/`](comparison_inputs/glm-20261103T055706Z-0748a4b5/provenance.json) from PR #59.
- **Environment:** Python 3.13; pandas 2.3.2; NumPy 2.3.3; SciPy 1.18.1; scikit-learn 1.7.2

### Workflow Runs
| Workflow Run | What it did | Runtime | Evidence |
| :--- | :--- | ---: | :--- |
| `glm-20261103T055706Z-0748a4b5` (run of record, Hector, Mac) | 30 CV fits, selection, final refit, one validation score | 89 s total | [receipt](comparison_inputs/glm-20261103T055706Z-0748a4b5/run_receipt.json), [CV results](comparison_inputs/glm-20261103T055706Z-0748a4b5/cv_results.csv), [validation predictions](comparison_inputs/glm-20261103T055706Z-0748a4b5/validation_predictions.csv) |
| `glm-repro-20261110-rachel` (independent reproduction, Rachel) | Same 30 CV fits and final refit, written separately; predictions compared, **no validation loss read** | see receipt | [receipt](runs/glm-repro-20261110-rachel/reproduction_receipt.json), [CV results](runs/glm-repro-20261110-rachel/cv_results.csv), [coefficients](runs/glm-repro-20261110-rachel/coefficients.csv), [notebook](../../../notebooks/gate3_approach1_glm.ipynb) |

An earlier launch of the run of record stopped before creating a run because of an import problem in the verifier; it produced no results (recorded in Hector's experiment register on PR #58).

### Results
**Tuning (pooled out-of-fold MAE, training only):**

| `alpha` | Pooled CV MAE | SD across folds | Outcome |
| ---: | ---: | ---: | :--- |
| 1 | 1,246.09 | 13.02 | tied (within 1 unit) |
| 10 | 1,245.72 | 13.18 | tied |
| **100** | **1,245.40** | **12.64** | **best and largest tied value: selected** |
| 1,000 | 1,246.58 | 11.40 | 0.17 units outside the tie window |
| 10,000 | 1,269.34 | 10.36 | worse |
| 100,000 | 1,470.87 | 12.26 | much worse |

Fold MAEs at `alpha` = 100 were 1,236.60, 1,261.09, 1,231.84, 1,256.15 and 1,241.36.

**Selected model:**

| Partition | Claims | MAE (loss units) | vs mean baseline | vs median comparator |
| :--- | ---: | ---: | ---: | ---: |
| Training fit (in-sample) | 141,238 | 1,240.42 | — | — |
| Training CV (pooled; mean ± sd across folds) | 141,238 | 1,245.40 (1,245.41 ± 12.64) | −720.50 vs CV mean constant (1,965.90) | −563.59 vs CV median constant (1,808.99) |
| Validation | 28,248 | **1,250.45** | **−709.18** (1,959.63) | **−552.34** (1,802.79) |

### Interpretation and next decision
- **What happened:** the hypothesis is supported. The model beats both constant predictors by about 30–36% on validation, and the validation score is within 5 units of training CV.
- **Overfitting:** little. Training-fit MAE (1,240.42) is only 5 units below CV MAE.
- **Penalty sensitivity:** `alpha` from 1 to 1,000 performs within 1.2 units, so the result does not depend on the exact penalty; only very strong penalties (10,000 and up) hurt.
- **Known weakness:** predictions are pulled toward the middle. Out-of-fold, 90% of predictions fall between 987 and 6,634, while the training 95th percentile of actual losses is 8,511.92, so large claims are under-predicted. Krish's high-loss diagnostics should confirm this on validation.
- **Reproduction:** the independent rerun matched every fold MAE within 0.011 loss units, the pooled CV MAE within 0.002, and every validation prediction within 0.13 loss units (0.0006%). The differences come from the iterative solver's tolerance on different computers and cannot change the selection (the nearest untied value is 0.17 units outside the tie window).
- **Issues:** none blocking. The run of record was both executed and audited by Hector; this reproduction gives a second, independent check of the training, tuning and refit.
- **Next decision:** **stop.** Freeze `alpha` = 100 as the Approach 1 candidate for the Gate 3 comparison. No further GLM configurations or validation releases. The required iteration belongs to Approach 2.
- **Reviewed by:** reproduction by Rachel Cheung, 2026-11-10; candidate audit by Hector Baeza, 2026-11-02.