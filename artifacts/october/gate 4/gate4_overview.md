# October Gate 4: Model Development Complete

## Hector: clean rerun and artifact bundle

I reran both constant baselines and the retained depth-7 XGBoost candidate from
a clean committed copy. The candidate's validation predictions and saved model
match the Gate 3 evidence exactly. All 93 tests passed after fixing environment
fixtures in the workflow tests. The fitting code and settings are unchanged.

The bundle is `october-gate4-hector-20261122-v1`. See the
[rerun notes and reproduction instructions](../../../docs/october_gate4_reproduction.md),
[artifact manifest](artifact_manifest.json), and
[rerun receipt](rerun/reproduction_receipt.json).

**Status: conditional; exact environment check remains open.** The modeling
libraries match, but this run used Python 3.13.2 instead of 3.13.5. We need a
run with the recorded Python version before marking all of Hector's version
checks complete. The first attempt and its test failures are also retained.

The reserved test claims were not fitted, predicted, or scored. Krish's model
decision and report, Rachel's independent review, and Leng's team handoff still
need their own evidence. No team approval or overall Gate 4 pass is recorded here.
