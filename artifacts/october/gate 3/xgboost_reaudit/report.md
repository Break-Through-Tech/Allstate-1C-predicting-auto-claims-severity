# Gate 3 Task 4 — fixes and re-audit

**Technical verdict: PASS for all three reported findings. Real training remains
blocked.** The defects came from the initial Codex implementation of Leng's
XGBoost runner and synthetic test. This change fixes that implementation.

Branch: `leng/oct-gate3-task4`; base:
`df557c41e23fa162b4bdfd00df8316e0b6e74f3a`. Exact final code/config/test identities,
receipt hashes and preservation checks are in
[verification_summary.json](verification_summary.json).

The [original audit](../xgboost_audit/audit.md), reproducer, outputs and old smoke
artifacts are preserved unchanged. Its verdict identifies the earlier code hash.
This report supersedes that technical verdict for the fixed runner; it supplies
no team approval and does not complete issue #45's real experiment.

## Finding 1: campaign lock — FIXED

Every continuation acquires the lock before reading the receipt. Under the lock,
it reloads configuration/readiness and validates code/config hashes, readiness,
environment, failed/interrupted attempts, counter bounds, counters against the
completed five-fold results, candidate IDs, frozen input identities, stage/release
order, follow-up plan hash, deadline and runtime limit. Source, manifest and fold
byte hashes are rechecked under that lock before execution; hashing parses no
target values.

The race probes advance the on-disk ledger before the second command acquires
its lock. The second `followup` rejects the completed six-configuration/30-fit
state; the second `release` rejects the consumed validation release. Neither
reaches data, fitting or validation dispatch, or overwrites the current ledger.

Regression tests:

- `test_intervening_writer_prevents_duplicate_followup_and_validation`
- `test_continuation_rechecks_counters_failures_and_input_hashes_under_lock`
- `test_source_manifest_and_fold_byte_changes_are_rejected`

## Finding 2: environment — FIXED

Before the first real fit, Python and NumPy/pandas/SciPy/scikit-learn/XGBoost
versions must match the config's environment pins. Those pins become approved
only when the team adopts the config and records readiness.

On every continuation, the actual environment is captured under the lock and
compared with both the config and the campaign receipt. Python version,
implementation, resolved executable and all five package versions are frozen
for that campaign. Each executed stage records its actual environment, exact
invocation, start/end, runtime and status. Older receipts without this provenance
cannot authorize continuation.

Regression tests cover all six initial version pins and eight continuation
identity/version fields for both follow-up and release, with zero fitting or
validation access on mismatch. `test_stage_records_actual_environment_and_invocation`
also verifies the successful stage record. The adapted independent version-drift
probe rejects both commands before any data/fit/validation dispatch.

## Finding 3: synthetic holdout — FIXED

`synthetic_inputs` returns separately generated validation row 201 alongside
training IDs 1–200. A validation-only category probes the learned missing-value
branch. Synthetic test ID 202 remains reserved; its features/target are never
generated or returned. Releases reject missing, training and poisoned test
fixtures before fitting.

`test_synthetic_release_uses_generated_holdout_and_never_fits_it` checks exact
fitting/transform IDs, features and targets; unchanged fitted vocabularies;
validation-only categories becoming missing; and no source reader access.
`test_synthetic_release_rejects_missing_or_test_fixture_before_fit` covers invalid
fixtures. The adapted independent holdout probe confirms that row 201's own
features and target are used transform-only, while fitting stays on IDs 1–200.

## Final evidence

| Check | Result |
|---|---|
| Full suite | **84 passed** — [tests.log](tests.log) |
| Runner safeguards under optimized Python | **23 passed** — [optimized_tests.log](optimized_tests.log) |
| Three adapted original audit scenarios | PASS — [probe_results.json](probe_results.json) |
| One-release smoke | 6 configurations, 30 CV fits, 1 separate synthetic validation release; 4 stage environment records |
| Two-release smoke | 6 configurations, 30 CV fits, 2 separate synthetic validation releases; 5 stage environment records |
| Independent arithmetic | All saved OOF and validation MAEs match `math.fsum`, with exact IDs and artifact hashes |
| Follow-up | Only `n_estimators` changes, 4 to 6; plan/rationale saved before the sixth fit |
| Model JSON | Actual XGBoost save/load predictions match exactly in both fresh workflows |
| Original Gate 2 checkout | Branch, HEAD, tracked/index state and 17 untracked file hashes unchanged |
| Original audit | All file hashes unchanged, retained in verification summary |
| Training hold | Config hash unchanged, `training_authorized=false`; `check` exits 1; no real campaign created |

Complete fresh artifacts are retained in [smoke_one/](smoke_one/) and
[smoke_two/](smoke_two/): receipts, OOF predictions, frozen plan, generated
validation fixture, validation predictions, models and preprocessing mappings.

Artificial pooled OOF MAE is **100.297622 → 84.519568**. Corrected separate-fixture
validation MAE in the two-release smoke is **50.574717 → 40.568248**. These are
software checks, not real claims performance or real experiment slots.

The documented runtime boundary remains: checks cannot interrupt an in-progress
native fit. No additional technical finding was identified in this scoped
re-audit. All three reported findings are closed for the hashed implementation.

## Reproduction and team decisions

With `allstate-btt` active, from this worktree:

```bash
python -B -m unittest discover -s tests -v
python -B -O -m unittest discover -s tests -p test_xgboost_runner.py -v
python -B -m scripts.run_xgboost smoke --output /private/tmp/task4-fixes-review-one
python -B -m scripts.run_xgboost smoke --smoke-sequence gate1_two_releases --output /private/tmp/task4-fixes-review-two
python -B "artifacts/october/gate 3/xgboost_reaudit/reprobe.py" --output /private/tmp/task4-fixes-review-probes.json
python -B -m scripts.run_xgboost check
```

Output destinations must be new. The final `check` is expected to exit 1. The
adapted probe uses temporary synthetic ledger fixtures and in-process readiness
mocks; it cannot authorize or invoke real-data training. The original defect
reproducer is preserved for its earlier code identity, not rewritten to pass.

The [original decision inventory](../xgboost_audit/audit.md#team-decisions-found-and-still-missing)
still applies: Approach 2 Gate 1/Gate 2 readiness, validation sequence/comparison
rules, iteration hypothesis/keep threshold, resource limits and deadline need
applicable recorded team decisions. The baseline split acceptance and reported
Approach 1 approval retain their stated scope.

No approval was inferred, authorization changed, or real training/test evaluation
run. Changes are uncommitted in the Task 4 worktree; no push, PR or team message
was sent. After decisions are recorded, follow the
[runner guide](../../../../docs/october_xgboost_guide.md), then audit the real saved
predictions and before/after MAE before opening a PR.
