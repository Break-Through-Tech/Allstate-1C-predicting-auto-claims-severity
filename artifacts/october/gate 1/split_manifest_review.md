# Independent Review: Split Manifest and Leakage Boundaries

**Reviewer:** Rachel Cheung · **Date:** 2026-10-19 · **Reviewed work:** Krish Patel's `october-split-v1`, branch `task-split-design-manifest`, commit `6ca1d39` (not yet merged to `main`) · **Reviewer independent of the work:** yes

**Verdict: PASS. No defects found. Recommend the team approve `october-split-v1` and merge it before Gate 2 work begins.** Four items below need a recorded team decision or a note in the Gate 2 plan; none blocks approval.

## How it was checked

1. **Reran the author's workflow** (`scripts/create_partition_manifest.py`) into a separate folder in a different environment (Python 3.13.16, pandas 3.0.5, NumPy 2.5.3; the author used pandas 2.3.2, NumPy 2.3.2). All three output files were **byte-identical** to the committed versions. The author's 9 unit tests passed.
2. **Wrote a separate check**, the [`verify_partition_manifest.ipynb`](../../../notebooks/verify_partition_manifest.ipynb) notebook, that does not reuse the author's code. It rebuilds the documented assignment rule from claim IDs alone and loads no `loss` values.

## Results

| Check | Result |
| :--- | :--- |
| Source SHA-256 matches frozen contract (`74037cb2…`) | PASS |
| Manifest SHA-256 matches split metadata (`18e69673…`) | PASS |
| Manifest contains only `id` and `partition` (no targets or predictors) | PASS |
| Manifest IDs unique; all 188,318 eligible claims present; none extra | PASS |
| Each claim in exactly one partition; no overlap | PASS |
| Counts 141,238 / 28,248 / 18,832 match the 75/15/10 largest-remainder rule | PASS |
| Assignment rebuilt from IDs alone matches all 188,318 rows (0 mismatches) | PASS |
| Unseen-level counts match `october_categorical_coverage.csv` for all 116 fields | PASS |
| Test diagnostics limited to row count and share | PASS |

## Leakage boundaries

- **Assignment uses IDs only.** Because the assignment rebuilt exactly from a hash of each claim ID, no target or predictor value could have influenced which claims landed in which partition, and no seed search was possible.
- **Test targets stay sealed.** The script skips test rows before converting `loss`, the exported diagnostics contain only test counts, and a unit test confirms that corrupting test `loss` values leaves the diagnostics unchanged.
- **Train and validation look similar.** Training mean `loss` is 3,038.30 and validation is 3,032.02; medians are 2,116.67 and 2,120.02. These are the author's diagnostics, recomputed here for train and validation only.
- **Downstream rules are documented.** The design requires every encoder, frequency, scaler, and model to fit on training data only, with cross-validation kept inside the training partition. The [preprocessing plan](preprocessing_experiment_plan.md) follows these rules.

## Items for the team

1. **Approve and merge.** The split is labeled PROPOSED and lives on an unmerged branch. Gate 1 approval should name commit `6ca1d39` and manifest SHA-256 `18e69673953fa61cbbabdd0421e83d31bd46b6f93356a2227793c6013e0850f1`.
2. **Record the validation partition's role.** The Challenge Advisor suggested a train/test split with cross-validation inside training. The added 15% validation partition is compatible, but the team should record its use: tuning happens with CV inside training, validation is used to compare approaches and judge the iteration, and test stays sealed until November. The cost is that models train on 75% of claims instead of 90%.
3. **Use a training-based high-loss threshold later.** The split diagnostics use September's full-file p95 (8,508.54) as a labeled historical reference, which is fine for a diagnostic. Gate 3 high-loss error slices should use the training p95 (8,511.92) instead.
4. **Unseen levels exist in validation.** 13 validation claims have a category level never seen in training (8 in `cat116`). The Gate 2 pipeline must handle them without errors (covered in the preprocessing plan, Section 4).

**Minor note:** `requirements.txt` pins NumPy 2.3.3, while the split was produced with 2.3.2. Because outputs were byte-identical on much newer versions, this is low risk, but Gate 2 should record its exact environment.

## Reproduce this review

After the split branch is merged, from the repository root:

    python3 scripts/create_partition_manifest.py --output-dir /tmp/split-rerun   # then compare file hashes
    python3 -m unittest discover -s tests -p 'test_partition_manifest.py'

Then open `notebooks/verify_partition_manifest.ipynb` and run all cells. The last cell should print "11 of 11 checks passed".