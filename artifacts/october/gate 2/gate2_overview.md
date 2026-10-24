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
