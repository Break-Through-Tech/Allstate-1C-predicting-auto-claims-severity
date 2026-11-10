# October comparison and diagnostics

Run from the repository root with Python 3, NumPy, pandas and Matplotlib:

```bash
python3 -m scripts.model_comparison
python3 -m unittest discover -s tests
```

`--output-root /tmp/comparison-check` creates a separate reproducibility run. `--write-summary` explicitly updates the completion summary. Each invocation writes a new run directory under `artifacts/october/gate 3/comparisons/`. Existing evidence is not overwritten. No estimator is imported or fitted; no constants are refitted, splits changed, or hyperparameters selected.

## Evidence and evaluation contract

The source is `data/allstate_claims_data.csv`, SHA-256 `74037cb248a1064e4d578692a4f4e5d8492ed1b2033daf643496e1b68b14ae03`: 188,318 rows and 132 columns. `id` identifies claims, `loss` is the original-scale target, and MAE is primary. `scripts.evaluation.load_frozen_split` verifies the source, roles, split acceptance and exact manifest. `october-split-v1` has 141,238 training and 28,248 validation claims, plus a sealed test partition. Manifest hash: `18e69673953fa61cbbabdd0421e83d31bd46b6f93356a2227793c6013e0850f1`.

Every valid full-population score uses the existing `scripts.evaluation.evaluate_mae`. Truth is `id,loss`; predictions are `id,prediction`. One-to-one ID joins, exact validation coverage, numeric finite values and positive source losses are enforced. Candidate source hash, manifest ID/hash, validation count, metric, scale, receipt status and prediction hash must match. Recorded and recomputed MAE must agree (`rel_tol=1e-10`, `abs_tol=1e-8`). CSVs use round-trip float parsing; no predictions are repaired or dropped.

Both baseline predictions and their constants are verified against the existing receipt `baselines-20261025T034742Z-0e9ea822`. Constants are never refitted. Baseline training error is left unavailable because the original receipt does not report it.

The current candidate adapter reads Ridge experiment directories under `artifacts/october/gate 3/comparison_inputs/`: original `run_receipt.json`, `validation_predictions.csv`, `cv_results.csv`, plus `provenance.json` with immutable source commit and file hashes. The GLM evidence was copied verbatim from Hector's unmerged branch with Krish's permission; this does not merge its training code or claim it is on main. The selected alpha comes from that existing receipt, never from new selection. CV assignments, fold supports, error sums, pooled MAE and fold statistics are cross-checked. A future model adapter must normalize its provenance into the same contract before using `score_existing`; do not place arbitrary model formats into the Ridge adapter. XGBoost is explicitly incomplete until a completed receipt and predictions are supplied.

## Comparison table

`model_comparison.csv` contains valid candidates and both baselines. It includes run/source/manifest identity, separate in-sample training, CV mean and pooled CV fields, validation MAE/count, configurations, complexity, runtime, environment and artifact references. Unavailable metrics are blank, not zero. `train_or_cv_mae` uses the fold mean only when available and is labeled accordingly.

- Delta = candidate validation MAE minus baseline MAE; negative means lower error.
- Improvement (%) = 100 × (baseline MAE − candidate MAE) / baseline MAE; positive means lower error. Zero baseline denominators yield an unavailable percentage.

Complexity labels identify units and limitations. One baseline scalar is not interchangeable with a model's coefficient count or tree count. Ridge's 130 source predictors are not a post-encoding feature count; that count is unavailable. The existing GLM runtime covers validation, preprocessing, all 30 CV fits and scoring, and final refit. Isolated fit/predict times and hardware are unavailable. Library environments are recorded, so no fair runtime ranking is claimed.

## Error diagnostics

Signed error is prediction minus actual loss; negative means underprediction. Absolute error is its magnitude. Diagnostic slice MAE is the mean of these absolute errors after the shared evaluator has verified the complete population; it is not a competing full-population evaluator. Percentage error is not used.

Quantile cuts are calculated once from training loss, using linear interpolation at 25%, 50%, 75%, 90%, 95% and 99%. Intervals are `(lower, upper]`; the outer bounds extend to infinity to include validation values outside the training range. Ties stay in the lower interval; duplicate cuts may produce empty bins, with unavailable metrics. The seven supports must sum to 28,248. Every slice reports count, full-validation denominator, share, actual-loss mean/median, MAE, signed mean error, median absolute error, prediction mean/median, max error and sample error SD.

High-loss slices use strict `loss > training p95` and `loss > training p99`. This follows Gate 1's `split_manifest_review.md` recommendation for Gate 3. September's full-file p95 remains historical context and is not used to derive these slices. Small bins (<30 observations) carry a descriptive low-support flag; this is a reporting convention, not a statistical significance test or rejection rule. Upper-tail slices overlap and must not be added together. See plots and CSV supports together.

## Overfitting and stability

Validation minus true training MAE is a generalization gap. Validation minus CV mean is reported separately, and pooled OOF MAE is retained separately from the unweighted fold mean. No in-sample training MAE is available for this GLM run, so no training gap is fabricated and no universal overfitting threshold is applied.

Fold variability reports count, mean, sample SD (`ddof=1`), minimum, maximum and range for the receipt's already-selected configuration only. Search configurations are not random-seed repeats. Random-seed/repeated-training stability is `NOT_ASSESSED — insufficient repeated-run evidence`. Five folds do not prove repeated-training stability.

## Failures, reproducibility and limitations

`model_prediction_failures.csv` audits available candidate predictions even when provenance fails. It records missing/extra/duplicate/invalid IDs, null/nonnumeric/nonfinite predictions, missing artifacts, and provenance/scale/hash/metric mismatches with reasons and example IDs. Invalid candidates receive no valid comparison MAE. `candidate_inventory.csv` distinguishes VALID, INCOMPLETE and INELIGIBLE. No numerical prediction test can prove whether a producer forgot an inverse target transformation; the original-unit receipt is essential.

The comparison receipt records code hashes, Git revision/working-tree state, input/output hashes, source and manifest, baseline/candidate run IDs, environment, thresholds, tests and computed checks. Repeated runs should yield identical CSV contents; run IDs/timestamps intentionally differ. Two PNG figures show primary MAE and descriptive bin/tail/CV patterns. MAE remains primary; diagnostics do not select a winner.

Source hashing traverses bytes, and the existing target loader skips test rows before numeric target conversion. No internal test target is retained, scored, summarized, or plotted. Previously conducted September full-file EDA means the reserved test partition is not historically unseen. This task creates no additional test exposure.
