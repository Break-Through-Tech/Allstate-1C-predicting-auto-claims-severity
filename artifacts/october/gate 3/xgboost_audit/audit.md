# Gate 3 Task 4 XGBoost audit

**Verdict: FAIL for readiness to run real training. Three implementation/test fixes
are needed, in addition to the outstanding team decisions.** The existing
readiness hold works. This audit did not change the runner or authorize training.

Prepared November 11, 2026 (America/New_York). Reviewed branch
`leng/oct-gate3-task4`, base `df557c41e23fa162b4bdfd00df8316e0b6e74f3a`.
Exact reviewed implementation/config/test hashes are in
[audit_receipt.json](audit_receipt.json). GitHub
[issue #45](https://github.com/Break-Through-Tech/Allstate-1C-predicting-auto-claims-severity/issues/45)
requires training Approach 2, one justified change and before/after MAE. The
configuration requires five initial candidates plus one follow-up on five saved
training folds, at most 30 CV fits, and readiness/release decisions before real
candidate fitting.

## Findings requiring fixes

### P1 — Read the ledger after acquiring the campaign lock

[`scripts/run_xgboost.py`, line 461](../../../../scripts/run_xgboost.py#L461)
reads and validates the receipt before acquiring the lock at line 469. A command
can read a 25-fit/FOLLOWUP_FROZEN receipt, pause while another command completes
the sixth configuration, then acquire the now-free lock and proceed using its
stale 25-fit receipt. The same gap applies to validation releases. The lock
excludes simultaneous writers but does not prevent this stale-reader schedule.
It can permit five extra fits or a repeated validation release while overwriting
the current ledger with stale counters.

A deterministic synthetic probe advanced the on-disk ledger to COMPLETE/30 fits
immediately before lock acquisition. The normal CLI still dispatched `followup`
with FOLLOWUP_FROZEN/25 fits in memory. The expensive stage was mocked; no real
claims were loaded or fitted. This proves the stale state reaches dispatch,
rather than claiming that an actual real-data overrun occurred.

**Fix:** acquire the campaign lock before loading, validating or modifying the
existing receipt. Revalidate stage, failures, counters, input hashes and readiness
under that lock. Add a regression test for an intervening writer, covering both
follow-up and validation-release dispatch. The stale command must reject the
completed/consumed stage without fitting or scoring anything.

### P2 — Enforce and record the environment for every stage

[`new_receipt`, line 405](../../../../scripts/run_xgboost.py#L405) records package
versions only at campaign creation. The continuation checks at lines 462–468
compare config, code and readiness but never compare the current interpreter or
libraries with the recorded environment. `check_readiness` also does not enforce
the config's environment pins before the first fit.

A synthetic continuation receipt with an explicitly different recorded XGBoost
version passed the normal continuation guards and reached follow-up dispatch.
Changing the actual environment between commands could mix model/library
behavior across the before/after experiment while retaining the initial versions
as the only environment record.

**Fix:** verify the initial environment against the adopted environment policy,
then verify interpreter and all relevant package versions on every subsequent
stage, under the campaign lock. Record each stage's actual environment and
invocation. Reject changes before preprocessing/fitting unless the team approves
and records an explicit amendment/reproduction policy. Add a mismatch regression
test that asserts zero fits and zero validation access.

### P2 — Give the smoke test a separate generated validation sample

[`release`, lines 350–352](../../../../scripts/run_xgboost.py#L350) copies the first
training row and changes its ID to the synthetic validation ID. Both smoke
receipts therefore score an in-sample feature/target pair labeled as validation.
The original generated row 201 is dropped by `synthetic_inputs`; it is never used
by the release. This weakens the evidence for validation separation even though
the real-data branch loads the frozen validation partition correctly.

A probe captured the evaluator's truth and model input: the ID was 201, while
both the features and target matched training row 1 exactly. This is a synthetic
test-design defect, not evidence that real validation or test data entered model
fitting.

**Fix:** retain a genuinely separate generated validation frame and pass it to
synthetic releases. Assert that its IDs, features and targets come from the held
out fixture, and verify that validation is transform-only. Keep synthetic test
features/targets inaccessible or poisoned. Rerun both smoke sequences and retain
new receipts after the fix; preserve the old receipts as historical evidence.

## Checks that passed

The complete existing suite passed: **76 tests**. See [tests.log](tests.log).
Fresh synthetic runs passed both release sequences, each with six
configurations and exactly 30 CV fits. Those happy paths do not cover the three
findings above.

| Requirement | Audited evidence / result |
|---|---|
| Frozen split and saved folds | Manifest/fold hashes match the config; 141,238 unique training IDs only; no validation/test IDs in CV. Fold sizes: 28,248, 28,248, 28,248, 28,247, 28,247. No real source CSV was opened for this check. |
| Preprocessing inside each fold | Instrumented actual notebook definitions on synthetic inputs: five distinct preprocessors, each fit on exactly its four fitting folds, held-out IDs disjoint. A heldout-only category becomes missing under the training-derived vocabulary. |
| Shared original-unit MAE | OOF uses `evaluate_training_mae`; validation uses the existing `evaluate_mae`. Finite negative predictions stay unchanged; nonfinite predictions fail. |
| Initial selection | Parent selected by pooled OOF MAE and the declared one-unit complexity/runtime tie rule. |
| Exactly one follow-up setting | Both saved receipts change only `n_estimators`; the saved plan hash matches, and the rationale timestamp precedes the sixth candidate's start. The runner records a human-supplied setting/rationale; it cannot independently certify the scientific justification or absence of external validation influence. |
| Saved synthetic scores | Independently recomputed all six OOF MAEs with `math.fsum` for each existing smoke campaign; values, ID coverage and prediction hashes match. |
| Model artifacts | Existing release artifact hashes match; fresh smoke model JSON round-trip predictions match. |
| Sequential budget/failure policy | Happy-path 25+5 fits and one/two refits pass. Failed attempts consume slots and automatic retries are disabled. Concurrent/stale continuation is the P1 exception above. |
| Current readiness hold | `python -B -m scripts.run_xgboost check` exits 1 with `training_authorized is false` before real source loading or campaign creation. |
| Test partition | Code skips nonrequested rows before feature/target conversion; the training scorer rejects validation/test IDs. Existing poisoned-target tests pass. No real test targets or metrics were accessed during this audit. |

Detailed check outputs are in [verification.json](verification.json) and
[probe_results.json](probe_results.json). Fresh smoke receipt paths, commands and
hashes are recorded in [audit_receipt.json](audit_receipt.json). The previous
synthetic MAEs remain workflow evidence only and do not satisfy issue #45's real
experiment requirement.

## Team decisions found and still missing

**Verified recorded evidence:**

- [`split_acceptance.json`](../../gate%201/split_acceptance.json) records Krish's
  report that the team agreed to the exact 75/15/10 split, seed 42, on October 24.
  Its explicit scope is baseline/shared-evaluator work; it excludes overall gate
  approval and candidate-model training.
- The [GLM receipt](../comparison_inputs/glm-20261103T055706Z-0748a4b5/run_receipt.json)
  records: Hector reported verbal team approval on November 2 and proceeded with
  Rachel's proposed **Approach 1** configuration. This audit verifies that the
  note exists, not the meeting itself. It does not document an Approach 2 release
  sequence, readiness record, resource deadline or iteration rule.

**Not found in the available records:**

1. Gate 1/Gate 2 approval explicitly covering XGBoost training, the saved folds,
   preprocessing/target rules and outstanding CV/group/time assumptions or risk
   acceptance. Gate 1 still says NOT YET APPROVED, and the Gate 2 independent
   record explicitly says formal approval is not recorded.
2. Resolution of `OCT-A2-RELEASE-SEQUENCE`: `gate1_two_releases` versus
   `amend_to_one_release`, including comparison/selection rules and confirmation
   that the one-release option would satisfy the iteration requirement if chosen.
   The Gate 1 proposal also has a larger historical iteration budget; the team's
   adopted record must reconcile it with the config's stricter five-plus-one /
   30-fit limit rather than silently combining budgets.
3. The training-evidence iteration hypothesis, minimum MAE improvement worth
   keeping, thread/resource limit, cumulative runtime limit and future deadline.
4. A corresponding actual readiness JSON and updated authorized config. Only the
   pending example exists; the config retains `training_authorized=false`, a
   null selected option/decision record, and an unresolved resource deadline.

An existing team chat/meeting decision can supply these records if its actual
text, date, participants and scope cover them. No new meeting or repeated vote is
intrinsically required. No such Approach 2 decision was available in the audited
repository or task messages. This audit does not infer approval from merged PRs,
synthetic receipts, or the GLM run.

The declared runtime limit is checked at fit boundaries and cannot interrupt an
in-progress native fit, as the guide already discloses. The team should adopt that
boundary explicitly or require a separately enforced hard wall-clock limit.

## Reproduction and next step

From this Task 4 worktree, activate `allstate-btt` and run:

```bash
python -B -m unittest discover -s tests -v
python -B -m scripts.run_xgboost smoke --output /private/tmp/task4-audit-repeat-one
python -B -m scripts.run_xgboost smoke --smoke-sequence gate1_two_releases --output /private/tmp/task4-audit-repeat-two
python -B -c "import runpy; runpy.run_path('artifacts/october/gate 3/xgboost_audit/reproduce_findings.py')"
```

Smoke output directories must be new. The findings probe mocks readiness only
inside its temporary synthetic fixtures, intercepts expensive CLI stages, and
does not authorize or invoke real-data training. Its successful assertions
demonstrate the current defects; it is an audit reproducer, not a regression test
claiming the defects are correct behavior.

Fix the three findings, add regression coverage and repeat this audit before
real execution. Record the team's existing applicable decisions or resolve the
remaining choices. Audit real saved predictions and before/after MAE after the
authorized experiment, before opening a PR. No source fix, approval, commit,
push, issue update or real training was performed by this audit.
