# Allstate Oct Milestones

This guide is a draft for the October milestone of the Allstate project. Use it
to plan work with the team and Challenge Advisor; a checklist item is complete
only when its evidence is linked and reviewed.

**October Milestone:** Model Development -> Create data splits, train a baseline
model, experiment with approaches, optionally test feature inclusion or
exclusion if time permits, and iterate.

## Gate Handoffs

The October milestone has 4 [**Gates**][gate].

1. **Gate 1:** Modeling Plan and Splits Approved
1. **Gate 2:** Baselines and Preprocessing Verified
1. **Gate 3:** Model Experiments Reviewed
1. **Gate 4:** October Model Development Complete

Use the same handoff pattern as the
[September gates][september-gates]:

1. **Evidence owner prepares:** link each completed item to an exact committed
   [Artifact][artifacts] or verified [Artifact Bundle ID][artifact-bundle].
1. **Independent teammate verifies:** someone who did not produce the critical
   result reproduces it or checks it independently.
1. **Team Readiness Review:** demonstrate the evidence and record the decision,
   limitations, anomalies, disagreements, dissent, and open questions.
1. **Board updates:** mark dependent October work ready only after the gate
   decision is recorded. Carry unfinished September work into the October plan.

The October 6 lab calls for Milestone #2 Task Planning and a GitHub Projects
board update by October 11. Planning may record blocked work before its gate
passes; a planning entry does not authorize the dependent implementation.

Keep the working notebook and evidence accessible to every fellow, the coach,
and the Challenge Advisor in the team's shared Google Colab space. Commit
reproducible code or notebooks, configuration, approved result tables, reports,
and decision records to the repository. Record source, code, configuration,
environment, and [Workflow Run][workflow-run]
identities in each Artifact Bundle.

### October Scope Protections

- Begin implementation from the approved September Gate 4 handoff, including its
  source and field-role versions, findings, anomalies, and
  [October Recommendation Register][october-recommendation-register].
  If Gate 4 is still open, record the blocker and keep dependent October
  implementation work pending; this draft may still be used for planning.
- Use the approved source `data/allstate_claims_data.csv` unless a documented
  source change passes the affected review again.
- Use `loss` as the regression target and report Mean Absolute Error (MAE) on a
  named held-out partition in original `loss` units. A training score or a
  transformed-scale score is not held-out project performance.
- Use `id` only for integrity, partition membership, and prediction tracing.
  Treat `cat*` as nominal and `cont*` as continuous; do not invent meanings for
  anonymous fields.
- Fit every learned preprocessing step, feature-selection rule, and model on
  training data only. Keep validation targets out of fitting, encoding, and
  feature construction. Keep any reserved test partition untouched until its
  approved final-evaluation use.
- Keep valid high-loss claims in the analysis. Investigate suspected bad values
  through the anomaly register; do not remove them solely to improve MAE.
- Treat an internal split as evidence about this supplied file, not proof of
  future-period stability, causal effects, production readiness, or a suitable
  reserve for an individual claim. September EDA examined target relationships
  across the full file before October's split. A reserved internal test can be
  protected from October fitting and tuning, but it is not a fully blind new
  sample; a future-period or external sample would provide a fresher check.
  Closed claims without payment are excluded from the supplied data according
  to the project overview.
- The supplied field names do not establish whether an input is available when
  a claim is first filed. Unless the Challenge Advisor confirms field timing,
  describe modeling results as retrospective validation only.

## Gate 1 - Modeling Plan and Splits Approved

### September handoff and modeling contract

- [ ] By October 11, submit a week-by-week Milestone #2 task plan and update the
  GitHub Projects board with September carryover, owners, gate dependencies,
  split and baseline work, model experiments, one planned iteration, and reviews.
  Mark work blocked by September Gate 4 as planning-only until its handoff is
  approved; create detailed implementation tickets from the approved handoff.
- [ ] Link the approved September Gate 4 decision and exact Artifact Bundle IDs.
  Carry forward every unresolved anomaly, limitation, and Challenge Advisor
  question with an owner and handling decision.
- [ ] State the prediction task in plain language: estimate one claim's final
  paid amount from anonymous claim fields. Ask the Challenge Advisor which fields
  are available when the claim is first filed; record evidence and unanswered
  timing questions. Do not call the model an up-front estimator until the input
  availability needed for that use is verified.
- [ ] Freeze the eligible rows, source hash, field roles, target definition, and
  feature list for the first modeling run. Exclude `id` and `loss` from inputs.
- [ ] Confirm MAE in original `loss` units as the primary comparison metric.
  Name the partition, claim count, and evaluation code used for every reported
  score.
- [ ] Review the October Recommendation Register. Record which recommendations
  become October experiments, which are deferred, and which would reopen a
  frozen September gate if adopted.
- [ ] Record which split, feature, preprocessing, and model hypotheses came from
  September's full-file EDA. Disclose this prior exposure in the evaluation
  plan; do not describe a later internal test as wholly unseen evidence.

### Evaluation and split design

- [ ] Approve the train/validation design before fitting models. Record the
  split method, proportions, random seed, eligibility rules, and reason for the
  design. If using cross-validation, record fold construction and keep folds
  inside the training partition.
- [ ] Decide whether to reserve an internal test partition for November's final
  evaluation. If no test partition is reserved, record the resulting limit on
  final performance claims and the approved alternative evaluation plan.
- [ ] Freeze a machine-readable partition manifest keyed by `id`. Verify that
  every eligible claim belongs to exactly one partition and that partitions do
  not overlap or omit eligible claims.
- [ ] Before model comparison, check and record training and validation row
  counts, target summaries, high-loss support, and categorical level coverage.
  For a reserved test partition, verify membership and row count without
  newly inspecting test targets or computing test performance. Predeclare what
  would justify changing the split; do not try seeds until validation MAE looks
  favorable. Save a revised manifest and decision if a split changes.
- [ ] Decide how validation will be used for model selection and how any reserved
  test targets and scores will remain unused in October fitting and selection.
  Record the rule for stopping iterations so the team can interpret repeated
  validation comparisons honestly.

### Preprocessing and experiment plan

- [ ] Specify how nominal categories, rare levels, and previously unseen levels
  will be represented. Fit category vocabularies, frequencies, imputers,
  scalers, and other learned values on each training portion only.
- [ ] If target encoding is proposed, require cross-fitting within training
  folds and a training-only fallback for unseen or rare levels. Otherwise mark
  target encoding out of scope for the first comparison.
- [ ] Record the Challenge Advisor's required training-mean constant baseline
  and a training-median constant comparator. The median is useful because it
  minimizes absolute error for a constant prediction.
- [ ] Choose at least two distinct model approaches to test after the baselines,
  with a short hypothesis and practical reason for each. The project overview
  suggests GLM, random forest, GBM, and XGBoost as examples, not requirements to
  run every algorithm.
- [ ] Approve a compact experiment record containing hypothesis, feature set,
  partition manifest, preprocessing and model configuration, seed, code version,
  run receipt, resource cost, and planned comparison. Label feature inclusion
  or exclusion experiments optional if time permits.
- [ ] Have an independent teammate check the split manifest, leakage boundaries,
  metric code, and approved plan. Record team approval and the exact versions
  that pass Gate 1.

## Gate 2 - Baselines and Preprocessing Verified

### Reproducible baselines

- [ ] Run the required mean-constant baseline using the mean `loss` from the
  training partition only. Predict that one value for every validation claim.
- [ ] Run the median-constant comparator using the training median only. Report
  it beside the requested mean baseline rather than replacing that baseline.
- [ ] Report both validation MAEs in original `loss` units, with the partition
  manifest ID, claim count, fitted constant, code and source versions, and run
  receipt. Never present the full-file descriptive mean or median error as
  held-out model performance.
- [ ] Check prediction-to-`id` alignment, one prediction per validation claim,
  finite predictions, and the MAE calculation against an independent simple
  calculation.

### Leakage-safe model inputs

- [ ] Implement the approved preprocessing as a reproducible training pipeline.
  Fit learned transformations on training rows or training folds, then apply
  them unchanged to validation rows.
- [ ] Treat September's full-file target relationships as hypotheses only. If a
  target-informed recommendation guides feature selection, grouping, or
  encoding, recalculate its supporting signal within October training data or
  training folds before fitting; do not reuse a full-file statistic as a fitted
  rule or threshold.
- [ ] Demonstrate how the pipeline handles rare and unseen categories. Record
  the number of validation claims affected, without using validation `loss` to
  set category rules.
- [ ] Confirm that `id`, `loss`, `log1p_loss`, target summaries, and
  validation-only information are absent from model inputs. Investigate any
  disputed field role before training.
- [ ] Record whether a target transformation is used. If so, save the
  inverse-prediction rule and compute the project MAE only after predictions
  return to original `loss` units. Record how non-finite or negative predictions
  are handled.
- [ ] Independently rerun the baseline and pipeline checks from the recorded
  source, code, split, and configuration. Resolve discrepancies and record the
  Gate 2 approval before comparing feature-based approaches.

## Gate 3 - Model Experiments Reviewed

### Controlled model comparison

- [ ] Train at least two approved, distinct approaches on the frozen training
  partition. Record the exact feature set, preprocessing pipeline, model
  settings, random seeds, software versions, runtime, and Workflow Run for each.
- [ ] Keep the split, eligibility rules, and original-unit MAE calculation
  comparable across the mean baseline, median comparator, and candidate models.
  Document and justify any experiment that cannot use the same comparison.
- [ ] Tune model settings within training data, using the approved folds or
  another recorded training-only procedure. Treat validation as a limited
  comparison and selection check, not as training data.
- [ ] Maintain an experiment register with the hypothesis, changed variable,
  result, interpretation, and next decision for each iteration. Preserve failed
  runs and negative results rather than showing only the best score.
- [ ] After the first comparison, run at least one evidence-driven iteration.
  Change one justified model setting, approach, or approved preprocessing rule;
  rerun it under the fixed evaluation design. Record the before-and-after MAE,
  what changed, and whether the result supports another iteration or stopping.
- [ ] Produce one comparison table with training or cross-validation MAE,
  validation MAE, validation claim count, improvement or regression against both
  the required mean baseline and median comparator, model complexity, and
  runtime. Label all partitions and keep units in the table.
- [ ] Examine absolute errors across the target distribution, including the
  high-loss tail, with support counts. Use these as diagnostics; explain any
  tradeoff between overall MAE and large-claim errors without turning a
  diagnostic into an unannounced selection metric.
- [ ] Check for overfitting, unstable results, failed predictions, and category
  handling differences. Record where a model's validation evidence is too weak
  to support a clear choice.
- [ ] Explain each compared model's input fields and encoding, key settings,
  prediction output in `loss` units, and basic learning approach in terms the
  team can use to explain its result to the Challenge Advisor.

### Optional feature experiments and review

- [ ] Record the feature inclusion or exclusion decision. If time permits, test
  a small, explicitly motivated hypothesis using the same training-only
  selection and validation rules; otherwise record the deferred hypothesis and
  reason in the November handoff. Do not remove a field merely because its
  September marginal correlation was weak or it was correlated with another
  field. Deferral does not block Gate 3.
- [ ] Interpret anonymous predictors only as anonymous predictors. A model
  coefficient or importance score does not establish a field's business meaning
  or causal effect.
- [ ] Have an independent teammate reproduce the comparison table and audit at
  least one candidate's split, preprocessing, predictions, and MAE from its run
  receipt. Record disagreements, limitations, and the exact Artifact versions
  used in the Gate 3 decision.

## Gate 4 - October Model Development Complete

### Completion and independent review

**Completion rule:** Require approved Gates 1 through 3, including the splits,
mean baseline, at least two approaches, and one documented iteration. Keep Gate
4 open while a blocking data, split, leakage, metric, reproducibility, or
model-comparison defect remains unresolved. Gate 4 does not pass merely because
one model has the lowest displayed MAE or because October ends.

- [ ] Confirm the October Artifact Bundle contains the approved September
  handoff, modeling contract, source and split manifests, evaluation plan,
  baseline outputs, preprocessing code, experiment register, comparison tables,
  validation predictions or reproducible means to generate them, anomaly
  register, run receipts, review records, and reproduction instructions.
- [ ] From a clean committed version, rerun the baselines and at least one
  compared candidate through the final validation results. If a provisional
  candidate is named, include it in that rerun. Confirm that the recorded source,
  split, code, configuration, and dependency versions match the approved bundle.
- [ ] Independently verify the required mean baseline, prediction alignment,
  original-unit MAE, no train/validation overlap, training-only preprocessing,
  and at least one candidate comparison. Correct confirmed defects and repeat
  affected reviews before passing the gate.
- [ ] Name a provisional candidate for November only if the comparison supports
  one. State its validation MAE relative to both constant predictors and its
  limitations. Do not claim an MAE improvement over simple constant predictors
  unless it beats both on the same validation claims. If none improves
  convincingly, record that result and the next test rather than forcing a
  winner.
- [ ] Preserve any reserved test partition for its approved November use. Do not
  report an internal validation or test score as independent future-period
  performance. Note the September full-file EDA exposure when interpreting it.

### November handoff and communication

- [ ] Prepare a plain-language October report covering the split design,
  baseline scores, approaches tested, validated comparison, main error patterns,
  provisional or no-selection decision, and limits of the evidence. Explain the
  input fields and encoding, key model settings, how the compared models produce
  predictions, and what their outputs mean. Distinguish retrospective validation
  from verified usefulness at first filing, and disclose the prior full-file EDA
  exposure when interpreting internal test results.
- [ ] Give November's Evaluation and Presentation milestone the approved
  experimental pipeline and preprocessing versions, any provisional candidate
  or documented no-selection decision, evaluation code, split manifest,
  outstanding anomalies, optional feature experiments completed or deferred,
  and questions for the Challenge Advisor.
- [ ] Record the plan for final evaluation, key-predictor interpretation if time
  permits, presentation, and result documentation. Preserve the distinction
  between anonymous statistical predictors and confirmed business concepts.
- [ ] Present the handoff to the full team. Record approvals, dissent, unresolved
  risks, and the exact Artifact Bundle and Workflow Run IDs used to pass Gate 4.
- [ ] Update the GitHub Projects board with the gate decision, completed work,
  carried-over blockers, and November tasks based on the approved handoff.

[gate]: https://github.com/Break-Through-Tech/Allstate-1C-predicting-auto-claims-severity/blob/main/docs/coach/september-execution/Glossary.md#gate
[september-gates]: https://github.com/Break-Through-Tech/Allstate-1C-predicting-auto-claims-severity/blob/main/docs/coach/september-execution/Allstate-Sept-Milestones.md#gate-handoffs
[artifacts]: https://github.com/Break-Through-Tech/Allstate-1C-predicting-auto-claims-severity/blob/main/docs/coach/september-execution/Glossary.md#artifacts
[artifact-bundle]: https://github.com/Break-Through-Tech/Allstate-1C-predicting-auto-claims-severity/blob/main/docs/coach/september-execution/Glossary.md#artifact-bundle
[workflow-run]: https://github.com/Break-Through-Tech/Allstate-1C-predicting-auto-claims-severity/blob/main/docs/coach/september-execution/Glossary.md#workflow-run
[october-recommendation-register]: https://github.com/Break-Through-Tech/Allstate-1C-predicting-auto-claims-severity/blob/main/docs/coach/september-execution/Glossary.md#october-recommendation-register
