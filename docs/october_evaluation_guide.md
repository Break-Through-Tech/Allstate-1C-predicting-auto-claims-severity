# October shared MAE evaluation

Run commands from the repository root using the project's Python environment (NumPy and pandas required). Import the shared function; do not copy it into notebooks.

The accepted split is `october-split-v1`: 141,238 training, 28,248 validation, 18,832 sealed test claims (75/15/10, seed 42). `load_frozen_split()` checks source, dictionary, September manifest, partition hashes, source IDs, counts, and the dated split acceptance. Historical proposed metadata stays unchanged. Overall Gate 1 approval remains separate.

## Contract

Ground truth must be a DataFrame with exactly `id,loss`; predictions exactly `id,prediction`. Each must cover the frozen validation IDs exactly once. IDs must be positive integers or canonical decimal strings; floats, booleans and nulls are rejected. Values must have real numeric dtypes and be finite; numeric strings are rejected. Loss must be positive, consistent with the source contract. Empty, duplicate, missing or extra claims raise `EvaluationError`; no partial scores or automatic filling are allowed.

The evaluator joins one-to-one on claim ID, checks the resulting count, and returns MAE, count, validation partition ID, source/manifest hashes, caller metadata and alignment checks. Row order does not matter. MAE is the average absolute residual in original loss units. Invert any target transformation before calling it: numeric values alone cannot reveal a wrong scale. Finite negative predictions are scored unchanged; no clipping is applied.

## Executable example

```python
from scripts.evaluation import load_frozen_split, load_partition_targets, evaluate_mae
from scripts.run_baselines import fit_constants, predict_constant

split = load_frozen_split()
training, validation = load_partition_targets(split)
constant = fit_constants(training, split)['median']
predictions = predict_constant(constant, split)
result = evaluate_mae(validation, predictions, split=split,
                      run_metadata={'model': 'training-median'})
print(result)
```

For a future model, replace `predictions` with its `id,prediction` DataFrame. Preserve the IDs belonging to each prediction; never assign IDs by assuming independent arrays have the same order.

## Reproduction and evidence

```bash
python3 -m scripts.run_baselines
python3 -m unittest discover -s tests -p 'test_baselines_evaluation.py'
```

Each execution creates an immutable run directory under `artifacts/october/gate 2/baselines/` containing mean and median prediction CSVs (no truth), comparison CSV and JSON receipt. Use `--output-root /tmp/baseline-check` for a separate rerun. Constants and MAEs reproduce; run IDs and timestamps deliberately differ. `--write-summary` explicitly updates the task summary. The receipt captures actual versions, Git revision and working-tree state, code hashes, artifact hashes, tests and computed checks. Numeric CSV output round-trips at full precision.

Fit models and all learned preprocessing only on training rows; use cross-validation within training if needed. Validation supports model comparison but must never fit transformations or constants. IDs are join keys, not predictive features. Internal test targets remain sealed until final evaluation, preventing iterative selection from contaminating the final estimate.

The source is a shared CSV: verification hashes its bytes and projects IDs; target loading traverses records but skips test rows before numeric loss conversion. No test target is retained, validated, printed, summarized or scored. A synthetic poisoned test-target test verifies this boundary. Do not run the older full-data splitter merely to reproduce baselines.
