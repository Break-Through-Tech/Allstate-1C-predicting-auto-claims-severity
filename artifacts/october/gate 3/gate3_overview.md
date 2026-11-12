# October Gate 3 Overview

## Approach 1: Regularized GLM

Owner: Rachel Cheung · Issue #44 · [Experiment record](approach1_glm_record.md) · [Plain-language explainer](approach1_glm_explainer.md)

The frozen configuration `approach1-glm-v1` (ridge regression on `log1p(loss)`, 130 predictors encoded as 808 columns) was tuned over six penalty values with 30 training-only CV fits. Penalty 100 was selected under the pre-agreed tie rule, with pooled CV MAE of 1,245.40. Refit on all 141,238 training claims and scored once, it has a **validation MAE of 1,250.45**, 709.18 below the training-mean baseline and 552.34 below the training-median comparator. The test partition was not used.

The run of record is `glm-20261103T055706Z-0748a4b5`. An independent reproduction, `glm-repro-20261110-rachel` ([notebook](../../../notebooks/gate3_approach1_glm.ipynb)), rebuilt all 30 fits and the final model with separate code. It matched the selection, every fold MAE within 0.011 loss units, and every validation prediction within 0.13 loss units, without reading any validation loss. The main limitation is that predictions are pulled toward the middle, so large claims are under-predicted. Approach 1 is frozen for the Gate 3 comparison.