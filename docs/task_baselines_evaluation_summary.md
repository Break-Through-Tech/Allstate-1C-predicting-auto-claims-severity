# October baselines and evaluation

Shared ID-aligned MAE, training-only constants, strict coverage checks, synthetic tests, and reproducible artifacts are complete.

| Baseline | Fitted constant | Validation MAE | Claims |
|---|---:|---:|---:|
| mean | 3038.297456137867 | 1959.630916387640 | 28248 |
| median | 2116.665000000000 | 1802.793854078165 | 28248 |

Manifest: `october-split-v1`. Training claims: 141238. Run: `baselines-20261025T034742Z-0e9ea822`.

Files: `scripts/__init__.py`, `scripts/evaluation.py`, `scripts/run_baselines.py`, `tests/test_baselines_evaluation.py`, `docs/october_evaluation_guide.md`, this summary, `artifacts/october/gate 1/split_acceptance.json`, and the addendum in `artifacts/october/gate 1/gate1_signoff.md`.

Artifacts in `artifacts/october/gate 2/baselines/baselines-20261025T034742Z-0e9ea822`: `baseline_mean_predictions.csv`, `baseline_median_predictions.csv`, `baseline_comparison.csv`, `baseline_run_receipt.json`. See receipt for exact hashes, environment, code revision and test output.

Reproduce from repository root: `python3 -m scripts.run_baselines`. Every run creates a new directory; existing evidence is preserved.

Validation includes exact ID coverage, one-to-one joins, finite predictions, partition consistency, training-only fitting, independent MAE calculation and repeat execution.

Limitations: constant baselines, not feature-based ML models. Results apply to frozen validation only; validation MAE is not an untouched final-test estimate. No internal test targets were inspected. Overall Gate 1 signoff remains separate from the confirmed split agreement.

Next: fit future models and learned preprocessing on training only, then use the shared evaluator to compare validation MAE with both benchmarks.

Validation checklist:

- Frozen manifest verified: PASS
- Source version verified: PASS
- Train/validation separation verified: PASS
- Shared MAE evaluator implemented: PASS
- MAE calculated in original loss units: PASS
- Prediction IDs aligned correctly: PASS
- Exactly one prediction per validation claim: PASS
- No missing predictions: PASS
- No extra predictions: PASS
- All predictions finite: PASS
- Training-mean baseline evaluated: PASS
- Training-median comparator evaluated: PASS
- Both fitted constants use training data only: PASS
- Baseline comparison generated: PASS
- Versions and hashes recorded: PASS
- Automated tests pass: PASS
- Reproducibility confirmed: PASS
- Test targets remain untouched: PASS
- Evaluation documentation created: PASS
- Task completion summary created: PASS
- Run receipt generated: PASS

All 22 repository tests passed (13 evaluator/baseline tests and 9 existing partition tests). Two complete workflow executions produced identical constants, MAEs and prediction hashes. The earlier run `baselines-20261025T034722Z-10e9a301` is retained alongside the final run as historical evidence. Receipts record the precommit Git revision, working-tree state and exact executable source hashes.
