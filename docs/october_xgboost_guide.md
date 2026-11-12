# October Approach 2 runner

**November 12 result: the approved campaign is complete and independently
verified. Retain depth 7.** The depth-8 follow-up missed the 1.0 CV improvement
threshold. The allocated 30 CV fits and two refits are fully consumed; this guide
does not authorize another campaign or a reset. See the
[final experiment record](../artifacts/october/gate%203/approach2_xgboost_record.md)
and [saved-prediction audit](../artifacts/october/gate%203/xgboost_results_20261112/results_audit.json).

Owner: Leng Lim. GitHub [issue #45](https://github.com/Break-Through-Tech/Allstate-1C-predicting-auto-claims-severity/issues/45)
is titled **Task 12: Train Approach 2 and run one iteration**; this is the work
described as Gate 3 Task 4 in the task conversation.

**November 12 update: scoped XGBoost readiness is approved at Leng's direction.**
The [decision](../artifacts/october/gate%203/xgboost_readiness_decision_20261112.md)
and [readiness file](../artifacts/october/gate%203/xgboost_readiness.json) adopt the
saved technical plan. Leng is the only evidenced approver in the exchange.

Historically, at base `df557c41e23fa162b4bdfd00df8316e0b6e74f3a`, Gate 1 was NOT YET APPROVED,
the independent Gate 2 record says formal approval is not recorded, and
`OCT-A2-RELEASE-SEQUENCE` is pending. Rachel's merged GLM results do not grant
approval to train Approach 2. That historical split acceptance covers baseline
work only; the new scoped decision separately supplies XGBoost readiness.

The three initial audit findings are fixed. The
[re-audit report](../artifacts/october/gate%203/xgboost_reaudit/report.md) records
84 passing tests, 23 optimized runner tests and passing targeted probes. The
original audit and old receipts remain historical evidence of the earlier code.

## Verify without training on claims

Use the existing `allstate-btt` environment; no environment/package changes are
needed on this Mac. Run these commands from this worktree:

```bash
conda activate allstate-btt
python -B -m unittest discover -s tests -v
python -B -m scripts.run_xgboost check --readiness "artifacts/october/gate 3/xgboost_readiness.json"
```

`check` must validate the actual recorded decision/config/environment before any
real campaign. Pending or missing decisions still fail before source loading;
the tests preserve the historical proposed config as a fixture. No `--force` or
bypass flag exists.

Synthetic end-to-end probes use generated IDs, all 130 generated predictors and
artificial targets. They never open the claims CSV. Each destination must be new:

```bash
python -B -m scripts.run_xgboost smoke --output /private/tmp/task4-smoke-one
python -B -m scripts.run_xgboost smoke --smoke-sequence gate1_two_releases --output /private/tmp/task4-smoke-two
```

Each smoke campaign exercises five initial candidates, a frozen one-setting
change, all five follow-up folds, the keep decision, and model/preprocessor export.
Smoke uses 4 trees initially, 6 in its follow-up and one thread. These scores are
workflow evidence only. They say nothing about real claims accuracy and consume
no real experiment slots. The second flow also exercises the separate initial
validation release. Current complete smoke artifacts are under
[`xgboost_reaudit/`](../artifacts/october/gate%203/xgboost_reaudit/). Validation
uses separately generated row 201; reserved test ID 202 has no generated features
or target. The old `xgboost_smoke/` receipts used a relabeled training sample for
artificial validation and are retained only as historical workflow evidence.

## Decisions required before real training

The November 12 decision now records the scoped readiness, two-release sequence,
depth-only iteration, 1.0 keep threshold, four threads, 10,800-second fit-compute
cap and November 12 11:59 p.m. EST deadline. The earlier blocked preflight is
historical evidence and has not been overwritten.

The team must record actual Gate 1/Gate 2 readiness, including CV assumptions and
outstanding risks; choose a validation sequence and comparison rules; approve an
iteration hypothesis based on training evidence; and set the keep threshold,
thread limit, cumulative runtime limit and future UTC deadline. This change
records none of those approvals on the team's behalf.

Use [`xgboost_readiness.example.json`](../artifacts/october/gate%203/xgboost_readiness.example.json)
as the schema for `artifacts/october/gate 3/xgboost_readiness.json`. The example's
PENDING/null fields deliberately cannot authorize training. Each evidence path
must be tracked in this worktree and pinned by SHA-256. The config must also be
updated by the team to record `execution.training_authorized=true`,
`policy_review.status=APPROVED`, `selected_option`, `decision_record`, and the
same `experiment_budget.resource_deadline`. Pin the updated config's SHA-256 in
the readiness record. Its validation evidence path must equal `decision_record`.
Record and review these changes in Git before execution. The old Gate 2 static
verifier describes the proposed, unapproved config; review that historical
expectation when the team adopts a new config version.

The runner checks recorded paths, hashes, statuses and limits. It cannot
authenticate human signatures or establish unrecorded approvals.

For the approved automatic run, use `scripts.run_xgboost_campaign` with the same
readiness path and a new `--output` directory. It calls the unchanged re-audited
runner for each stage, logs progress, refuses retries and freezes its training-CV
depth recommendation before the first validation release. If the selected depth
is the shallowest/deepest at its learning rate, it tests one step shallower/deeper;
for an interior depth it interpolates toward the better neighboring depth,
preferring shallower on a tie. All proposed depths must be previously untested.
The log confirms a real fit only after a real held-out fold score is saved.

Once those decisions are recorded, the exact next command on this Mac is:

```bash
/opt/anaconda3/envs/allstate-btt/bin/python -B -m scripts.run_xgboost initial --readiness "artifacts/october/gate 3/xgboost_readiness.json"
```

It runs only the five initial candidates on the five saved folds (25 fits).
All real stages use the single ledger at
`artifacts/october/gate 3/runs/xgboost-task4/run_receipt.json`. Repeating `initial`
refuses the existing campaign directory. Continuing requires identical config,
readiness and implementation hashes. Every continuation reads and validates its
receipt after acquiring the lock, including stage, counters, failures, readiness
and input/code hashes. Frozen source/manifest/fold bytes are rechecked under the
lock before execution. Byte hashing does not parse target values.

Python and all five fitting-library versions must match the config before the
first fit. Every continuation also checks Python implementation, resolved
executable and package versions against the campaign receipt under the lock.
Each stage records its actual environment and invocation. Missing provenance,
version drift and failed/interrupted stages require review rather than automatic
continuation; historical receipts are not silently upgraded.

## Freeze and execute the follow-up

Inspect the initial receipt's pooled OOF MAE, each fold's count/MAE, sample SD,
and runtime. Selection applies the config's one-unit tie rule: lower depth,
fewer trees, lower learning rate, then lower runtime. OOF scoring uses the shared
evaluator's new training-only entry point; validation scoring keeps its existing
interface and behavior.

For `gate1_two_releases`, first run:

```bash
python -B -m scripts.run_xgboost release --readiness "artifacts/october/gate 3/xgboost_readiness.json"
```

That refits the initial winner on all training claims and makes its one allowed
validation release. For `amend_to_one_release`, skip this initial release.

Next use `freeze-followup --parameter NAME --value JSON_NUMBER --rationale TEXT`
with `--readiness "artifacts/october/gate 3/xgboost_readiness.json"`. Choose the
setting and write the reason using initial **training CV evidence only**. The
runner freezes its parent, old/new value, rationale, keep threshold, before MAE
and timestamp in `followup_plan.json`. It refuses a second plan or an unchanged,
invalid or disallowed setting. The follow-up cannot change seed, folds, target,
preprocessing or multiple hyperparameters.

```bash
python -B -m scripts.run_xgboost followup --readiness "artifacts/october/gate 3/xgboost_readiness.json"
python -B -m scripts.run_xgboost release --readiness "artifacts/october/gate 3/xgboost_readiness.json"
```

`followup` consumes the final five CV fits and records before/after pooled MAE,
improvement, and whether it meets the pre-recorded positive keep threshold.
The final `release` performs the authorized full-training refit and validation
score. For two releases it releases the sixth candidate so the receipt contains
before/after validation evidence as required; the training-only keep decision
remains recorded independently. For one release it releases the retained
candidate and makes no separate before/after validation claim. No setting is
chosen from validation outcomes. Baseline/GLM comparisons remain in the team's
existing comparison workflow; this change does not alter historical comparisons.

## Provenance, limits and isolation

The runner verifies the existing source/manifest hashes and saved fold hash,
exact training-only fold membership, five balanced folds and unique IDs. It
loads Hector's actual schema/native categorical class definitions from the
notebook without executing notebook data loads or writes. Every fold gets a
new preprocessor fit on its four training folds. No new split or fold assignment
is generated for real experiments. All 116 categoricals and 14 continuous
features are used; ID, target, partition and derived labels stay out of features.

Each receipt records code/config/data hashes, settings, seed, actual versions,
per-fold runtime/count/MAE, mean/sample SD, pooled OOF MAE, prediction alignment
checks, runtime and failures. Each candidate saves ID-aligned OOF predictions.
Each released model saves JSON, exact schema, rare mappings and fixed category
vocabularies, plus validation predictions and artifact hashes. Nonfinite
predictions fail; finite negative predictions are counted and scored unchanged.

Failed/interrupted attempts retain consumed slots. Automatic retries and campaign
reset are disabled; recovery requires team review and a written amendment, with
the old ledger preserved. Runtime/deadline checks occur between fits and again
after preprocessing. They cannot interrupt an in-progress native XGBoost fit;
a single fit may overrun the limit, after which another fit is blocked. Resource
planning must account for that boundary. Fold variability is not a confidence
interval or repeated-seed stability estimate.

Training reads skip every non-training row before feature/target conversion.
Only an explicitly sequenced validation release loads validation rows. Test
rows are always skipped before conversion. Source hashing and the shared frozen
split's ID-only membership checks traverse bytes/IDs without scoring test claims.
The completed campaign performed the two approved validation releases. Subsequent
verification rescored saved predictions without fitting new models. No test
target evaluation was performed. The original implementation/audit records that
predate real training remain historical evidence.
