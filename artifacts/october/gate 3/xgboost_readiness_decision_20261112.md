# XGBoost readiness decision — November 12, 2026

**Status: APPROVED for the bounded Approach 2 experiment described below.**
**Recorded approver:** Leng Lim, through explicit instructions in the Codex conversation.
**Decision date:** November 12, 2026 (America/New_York).

Leng directed: “Use the exchange above as the team’s readiness decision for XGBoost.”
Leng also directed Codex to use the saved technical plan, update readiness, rerun
preflight, start automatically if it passes, complete the follow-up, verify saved
prediction MAEs and prepare the PR. This is the recorded team decision at Leng's
direction. Leng is the only person whose agreement is evidenced in this exchange;
no agreement or signature is attributed to Rachel, Hector or Krish.

## Scope of Gate 1 and Gate 2 acceptance

This decision accepts Gate 1 and Gate 2 readiness specifically for Approach 2:
the frozen source/field roles, october-split-v1 assignments, five saved training
folds, training-only preprocessing, identity loss target, shared original-unit
MAE evaluator, pinned environment and the technically re-audited runner. It
supersedes the pending readiness prerequisite for this bounded XGBoost run.
Historical sign-offs remain dated history; unrelated tasks and global gate
completion are not asserted.

The documented limitations remain accepted for this experiment: claim-level
folds assume exchangeability, no group/time key has been confirmed, predictors
are anonymous, and September EDA used the full labeled file. No unresolved
Advisor question is represented as answered. The reserved test is neither used
nor described as historically unseen. No new test release is authorized.

## Adopted experiment plan

Use Leng's saved technical plan in
[xgboost_preflight_20261112/leng_plan_approval.json](xgboost_preflight_20261112/leng_plan_approval.json).
Retain all original model settings and five initial configurations, seed 42,
116 native categoricals plus 14 continuous predictors, rare threshold 30 learned
inside each fold, no early stopping, and the five saved training folds. Exclude
ID, loss, partition and derived labels from predictors.

The budget is five initial configurations plus exactly one follow-up: at most
30 CV fits and two full-training refits. This stricter 5+1 budget controls this
run and supersedes the larger historical Gate 1 proposal's iteration allowance.
Failures consume slots; no retries, new searches or budget extension are approved.

Resolve OCT-A2-RELEASE-SEQUENCE as **gate1_two_releases**: select the initial
candidate by pooled OOF MAE with the checked-in one-unit complexity/runtime tie
rule; release that candidate once on validation; freeze one justified, previously
untested tree depth at its selected learning rate using training CV only; run
its five folds; release that follow-up once on validation. Retain the follow-up
only if unrounded pooled OOF MAE decreases by at least **1.0**. Validation outcomes
must not choose the changed depth or alter that keep decision. Record both
before/after OOF and validation MAE. The overall family/baseline comparison is
reported as evidence, without reopening the frozen GLM or asserting a test result.

Use four threads and a cumulative three-hour fitting-compute cap checked between
fits; the runner's documented accounting and inability to interrupt an in-progress
native fit are accepted. The deadline is **November 12 at 11:59 p.m. EST**,
**2026-11-13T04:59:00+00:00**. Do not start another fit after a limit is reached.
Use caffeinate -i, retain logs/receipts/predictions/models and report progress.
Local commits and preparation of PR review material are authorized; publication
or merging is not implied by preparing the PR.

## Provenance

The earlier technical-only approval and blocked preflight remain unchanged as
historical evidence. This later, explicit readiness instruction supplies the
previously missing Approach 2 gate decisions. It does not backdate approval.
