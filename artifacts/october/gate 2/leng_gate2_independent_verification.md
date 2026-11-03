# Gate 2 — Independent Verification

**Owner:** Leng Lim · **Prepared:** November 1, 2026 (America/New_York)
**Task:** #41, independent baseline and preprocessing verification
**Teammate base:** `aa8a87a42e2353f78d38345ede2351c0a5ad36ee`
**Branch:** `leng/oct-gate2-task8`

**Technical status: ready for team readiness review. Formal Gate 1/Gate 2 approval
is not recorded.** These nine additions remain uncommitted. The base SHA identifies
the unchanged teammate code; receipt input hashes identify the executed verifier
and configuration versions. This prepared record is not a human approval signature.

## Proposed submission: exactly nine files

```text
scripts/verify_gate2_leng.py
scripts/verify_gate2_preprocessing_leng.py
tests/test_verify_gate2_leng.py
environments/gate2/requirements.txt
environments/gate2/README.md
artifacts/october/gate 2/leng_gate2_independent_verification.md
artifacts/october/gate 2/approach2_xgboost_config.json
artifacts/october/gate 2/leng_verification/independent_receipt.json
artifacts/october/gate 2/leng_verification/preprocessing/preprocessing_receipt.json
```

The [independent receipt](leng_verification/independent_receipt.json) and
[preprocessing receipt](leng_verification/preprocessing/preprocessing_receipt.json)
are the retained execution evidence. They need no excluded logs, copied notebook
or model binary. Notebook outputs are checked in memory. Fresh baseline outputs
are reproduced temporarily; their verified results/hashes are embedded in the
independent receipt and match already committed prediction files.

## Reproduction

Use the existing `allstate-btt` environment, or the separate
[pinned dependencies](../../../environments/gate2/requirements.txt) and
[setup instructions](../../../environments/gate2/README.md). Python 3.13.5,
NumPy 2.3.3, pandas 2.3.2, SciPy 1.18.1, scikit-learn 1.7.2, XGBoost 3.1.1,
nbformat 5.11.1, nbclient 0.11.0, ipykernel 7.4.0 and jupyter_client 8.10.0
were used. The existing macOS Conda environment has `llvm-openmp=19.1.7`.
No packages or existing environment were changed; a fresh installation was not tested.

From the repository root:

```bash
export PYTHONDONTWRITEBYTECODE=1
export GIT_OPTIONAL_LOCKS=0
GATE2_REPRO_DIR="$(mktemp -d "${TMPDIR:-/tmp}/leng-gate2-repro.XXXXXX")"

python -B -m unittest discover -s tests -v
python -B -O -m unittest discover -s tests -p 'test_verify_gate2_leng.py' -v

python -B -m scripts.run_baselines --output-root "$GATE2_REPRO_DIR/baselines"
python -B -m scripts.verify_gate2_leng \
  --baseline-run "$GATE2_REPRO_DIR"/baselines/baselines-* \
  --approach2-config "artifacts/october/gate 2/approach2_xgboost_config.json" \
  --receipt "$GATE2_REPRO_DIR/independent.json"
python -B -O -m scripts.verify_gate2_leng \
  --baseline-run "$GATE2_REPRO_DIR"/baselines/baselines-* \
  --approach2-config "artifacts/october/gate 2/approach2_xgboost_config.json" \
  --receipt "$GATE2_REPRO_DIR/independent-optimized.json"
python -B -m scripts.verify_gate2_preprocessing_leng \
  --receipt "$GATE2_REPRO_DIR/preprocessing.json"

python -B -m json.tool "artifacts/october/gate 2/approach2_xgboost_config.json" >/dev/null
python -B -m pip check
```

The Approach 2 flag requests an **optional static scaffold review**. Omit it for
Gate 2 baseline/CV verification alone. The preprocessing CLI never reads that config.
Receipt writers refuse existing destinations. New runs use new IDs/timestamps;
the published receipts are copies of successful runs, not edited PASS summaries.

Checks ran in an isolated checkout of the same base with only these nine proposed
additions and none of the 17 excluded files. Preprocessing was also rerun with the
optional config physically absent; that successful run supplied its retained receipt.
The exact local invocations are recorded in the receipts' `execution_command`.
Their temporary output locations are not required inputs for another checkout.

## Results and frozen identities

| Check | Observed result |
|---|---|
| Repository tests | 35 passed: 13 evaluator, 9 partition, 13 verifier |
| Verifier tests under `python -O` | 13 passed |
| Full repository suite with modeling/notebook imports blocked | 35 passed |
| Independent baseline/CV verification | Passed in normal and optimized Python |
| Hector notebook | 34 code cells, zero errors, fresh kernel |
| Independent preprocessing and target inverse | Passed, including config-absent run |
| Optional config and XGBoost constructors | Static checks passed; five constructors at 3.1.1; zero candidate fits |
| JSON, Python syntax, dependency pins and `pip check` | Passed |
| Integrity | 78 tracked files, HEAD, branch, staging entries and both original stashes unchanged |

The added tests use the existing NumPy/pandas dependencies. They do not import
modeling/notebook packages during discovery. Scikit-learn is loaded lazily by the
full CV CLI check; notebook dependencies belong to the separate preprocessing CLI.

| Input | SHA-256 |
|---|---|
| Source, 188,318 rows | `74037cb248a1064e4d578692a4f4e5d8492ed1b2033daf643496e1b68b14ae03` |
| Partition manifest, `october-split-v1` | `18e69673953fa61cbbabdd0421e83d31bd46b6f93356a2227793c6013e0850f1` |
| CV membership, `october-cv-v1` | `82fb7f3d9899af71a61f3e3f1b0117f88ac97b0255070253fd8190ec2c7bfcd1` |
| Hector notebook | `75f9a385d59316e84b09c99bfdb0cb8ed3d2f4595b15768f75ba1a739c0b8f10` |
| Restored proposed Approach 2 config | `0aa4dd5f848ad09eebf3b12730219fda9130c21481ffc53f5e42cbc5edb670e2` |

Full verifier/environment/input hashes are in each receipt's `input_sha256`.
The independent receipt additionally records this config's hash and pending status.
The preprocessing receipt intentionally has no config dependency.

## Numerical and preprocessing evidence

Training/validation/test membership is **141,238 / 28,248 / 18,832**.
The verifier rebuilds the ID-only split, independently loads development targets,
fits constants with `math.fsum`/`statistics.median`, and scores saved predictions
by claim ID before comparison with the shared evaluator.

| Baseline | Training constant | Validation MAE | Claims |
|---|---:|---:|---:|
| Mean | 3038.297456137867 | 1959.630916387639 | 28,248 |
| Median | 2116.665000000000 | 1802.793854078165 | 28,248 |

Both committed runs, `baselines-20261025T034722Z-10e9a301` and
`baselines-20261025T034742Z-0e9ea822`, are verified from their existing tracked
receipts/CSVs. Fresh run `baselines-20261102T020455Z-313e8d4d` reproduces their
prediction hashes using the unchanged current runner. Its compact verified
results are embedded under `baseline_reproduction`; no new prediction CSV is
required in this submission. All reruns are repeated validation access and add
no tuned configuration.

Checks cover exact prediction coverage, canonical IDs, duplicates/missing/extra
claims, finite values, receipt/artifact hashes, shuffled alignment and original-unit
MAE. A nonconstant synthetic example gives **17/3**, including a finite negative
prediction scored unchanged. **26 invalid evaluator cases** are rejected.
Explicit exceptions remain active under optimization. Failure-path regression
tests also cover poisoned test labels, duplicate source rows and changed artifacts.

Both fold reconstructions match all saved training assignments: held-out sizes
**28,248; 28,248; 28,248; 28,247; 28,247**. No validation/test IDs enter CV.
The 15 fold-matched constant results reproduce within their CSV rounding tolerance.
Pooled OOF MAEs are about **1965.895085** (mean), **1808.991980** (median) and
**1809.777464** (log-scale constant).

Hector's self-tests were reproduced separately from the independent oracles.
Independent checks cover all 116 training vocabularies/rare mappings, threshold
29 versus 30, native labels across all validation rows, unknown/missing fallbacks,
unchanged fitted state, GLM scaling and shuffled row alignment.
There are **352 rare levels across 30 fields**; output widths are **808 GLM**
and **130 native**. Validation has **490** rare-affected claims, **12** unseen
claims, **13** unseen occurrences, **3** in both groups and **499** in either.
The GLM value oracle samples 180 validation rows, not every matrix entry.

Rachel's notebook is not executed because it writes team artifacts. Its actual
target-wrapper definition passes separate synthetic `log1p`/inverse/clipping,
per-fit-bound and invalid-value checks. No real-target candidate CV loop or
feature-model performance is claimed. Compatibility fits in Hector's notebook
use artificial targets.

## Proposed Approach 2 safeguards

The earlier config/report mismatch is repaired. The config retains the same
model parameters, five initial candidates, target and library versions.
It explicitly holds `execution.training_authorized=false`;
`OCT-A2-RELEASE-SEQUENCE` remains `PENDING_TEAM_DECISION`, with
`selected_option=null` and `decision_record=null`.

Its two options describe the exact conflict with the existing
[Gate 1 proposal](../gate%201/gate1_overview.md): adopt an initial comparison plus
separate iteration release, or explicitly amend the proposal to a training-only
iteration followed by one release. Neither is selected. Five initial configurations
plus one reserved iteration remain within **30 fits on five folds**. Before training,
the team must resolve the release/selection policy, readiness, resources/deadline
and iteration hypothesis. This is a declarative safeguard; no training runner or
formal approval is supplied by Task 8.

## Excluded local files — preserve, do not include in the proposed PR

All paths below are under `artifacts/october/gate 2/leng_verification/`.
These 17 files remain locally unchanged. They are historical/superseded output,
not current evidence or dependencies of this nine-file submission.

```text
baselines/baselines-20261102T011547Z-350d4c5c/baseline_comparison.csv
baselines/baselines-20261102T011547Z-350d4c5c/baseline_mean_predictions.csv
baselines/baselines-20261102T011547Z-350d4c5c/baseline_median_predictions.csv
baselines/baselines-20261102T011547Z-350d4c5c/baseline_run_receipt.json
file_manifest.json
independent.log
independent_optimized.log
independent_optimized_receipt.json
notebook_startup_blocked.log
optimized_tests.log
pip_check.log
preprocessing.log
preprocessing/gate2_preprocessing_executed.ipynb
preprocessing/synthetic_xgboost.json
repository_integrity.json
tests.log
validation_summary.json
```

## Limits and readiness

Test rows are skipped before loss conversion; preprocessing requests no loss.
No internal-test targets were scored, summarized or exported. Hashing source bytes
does not compute test metrics. September's full-file EDA remains prior exposure;
this review cannot establish every person's historical label access.

The earliest historical baseline has unreconstructed precommit runner bytes;
the receipt discloses its differing runner hash. The later historical/current
runner and fresh reproduction provide current executable evidence. Dependency
pins are direct pins, not a transitive cross-platform lock.
Historical commit availability is reported rather than required, so shallow
checkouts can still verify the saved artifacts and hashes.

**Ready for team readiness review, not formally approved.** The team still owns
Gate 1/Gate 2 decisions, CV/group/time assumptions, remaining Advisor questions or
explicit risk acceptance, stopping/release policy and the board record. Only the
nine listed paths form the proposal. No tracked teammate file, historical artifact
or stash was modified; no staging, commit, push, branch switch or PR was performed.
