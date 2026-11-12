# Approach 2 implementation and readiness record

Prepared November 11, 2026 (America/New_York), for Leng Lim, issue #45.
Branch: `leng/oct-gate3-task4`. Base:
`df557c41e23fa162b4bdfd00df8316e0b6e74f3a`, Rachel's merged PR #66.

**Status: runner implemented and synthetically verified; real experiment blocked.**
No real candidate model was trained, and no real validation release or test
evaluation was performed. Gate 3 Task 4 / issue #45 remains incomplete until the
team records readiness and executes the authorized real experiment and follow-up.

The checked-in XGBoost configuration remains unchanged and holds
`execution.training_authorized=false`. Gate 1 still says NOT YET APPROVED;
Gate 2's independent verification records technical readiness for review without
formal gate approval. The release sequence and resource deadline are unresolved.
`python -B -m scripts.run_xgboost check` exits 1 at the authorization hold before
source loading. The readiness example deliberately contains no approvals.

The implementation reuses Hector's preprocessing definitions, the frozen split,
five saved training folds and shared MAE checks. It implements the five-candidate
search, immutable one-setting follow-up plan, sixth-candidate CV, training-only
keep threshold, and both proposed validation sequences. Receipts retain settings,
seed, versions, hashes, runtime, counts, MAE and failures; exports retain model
JSON, preprocessing schema/mappings and ID-aligned predictions.

Verification on the existing `allstate-btt` environment:

| Check | Result |
|---|---|
| Existing suite before changes | 61 passed |
| Final suite including runner safeguards | 76 passed |
| Runner safeguards under optimized Python | 15 passed |
| Synthetic one-release sequence | 6 configurations, 30 CV fits, 1 artificial release; PASS |
| Synthetic two-release sequence | 6 configurations, 30 CV fits, 2 artificial releases; PASS |
| Independent OOF arithmetic | All six scores matched `math.fsum` in each sequence |
| Model serialization | Released model JSON reproduced predictions exactly |
| Original checkout preservation | Gate 2 branch, HEAD, tracked/index state and 17 untracked file hashes unchanged |

Both synthetic workflows selected A2-C04, then changed only `n_estimators`
from 4 to 6 after saving a synthetic probe rationale. Artificial pooled OOF MAE
went from **100.297622** to **84.519568**; improvement **15.778054**, above the
artificial 0.01 keep threshold. These are generated-data workflow results, not
claims performance or the required real experiment's before/after result.

Full synthetic settings, versions, runtimes, scores, before/after comparison and
code identities are in [`xgboost_smoke/`](xgboost_smoke/), including an independent
[verification summary](xgboost_smoke/verification_summary.json). The temporary
model/OOF files referenced by hashes can be regenerated with the guide's smoke
commands; only the compact receipts are retained here.

See the [runner guide](../../../docs/october_xgboost_guide.md) for the pending
decision schema, exact next command, stage order and resource-limit behavior.
The [plain-language explainer](approach2_xgboost_explainer.md) describes inputs,
learning and prediction meaning. Changes are prepared in the separate worktree;
no commit, push, issue update or team approval was performed.

## Re-audit after runner fixes

All three findings from the initial audit are fixed: locked receipt reload and
stage/budget/input checks, interpreter/package checks with stage provenance, and
a separately generated synthetic validation fixture. The final suite passes
84 tests; 23 runner safeguards also pass under optimized Python. Both fresh
synthetic sequences and all three adapted probes pass. Real training remains
blocked by the unchanged config and missing Approach 2 decisions.

See the [re-audit report](xgboost_reaudit/report.md) and
[verification summary](xgboost_reaudit/verification_summary.json). Complete fresh
receipts/predictions/models are retained in `xgboost_reaudit/smoke_one/` and
`xgboost_reaudit/smoke_two/`. Earlier receipts and the original audit remain
unchanged. Their relabeled-sample synthetic validation scores are historical;
the corrected generated holdout gives artificial before/after validation MAE
50.574717 and 40.568248 in the two-release smoke. No real-claims score is claimed.
