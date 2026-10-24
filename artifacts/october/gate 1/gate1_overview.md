# October Gate 1 Overview

### September Handoff

September Gate 4 was approved by the full team on October 6, 2026. October modeling work will use the approved September evidence rather than repeat the September analysis. The final decision, Artifact Bundle ID, Workflow Run ID, source hash, approvals, unresolved risks, and reproduction details are recorded in the [September Gate 4 sign-off](../../september/gate4_signoff.md).

### Frozen Data Contract
October inherits the approved source and field roles documented in the [September artifact manifest](../../september/artifact_manifest.json). The first modeling run starts with all 188,318 eligible rows and all 130 source predictors. `id` is reserved for integrity and prediction tracing, while `loss` remains the regression target; neither is a model input. Summaries and derived analysis fields are also excluded from the initial feature set.

### Open Issues
The main issues carried into October are handling of rare or unseen categories to avoid leakage, evaluation of errors among high-loss claims, and the limits created by anonymous fields and the lack of the following period data. Historical anomalies and their resolutions remain available in the [September anomaly register](../../september/anomaly_register.md).

### Prior Exploratory Data Analysis (EDA) Exposure
September examined target relationships across the full supplied file. Its modeling ideas must therefore be treated as prior hypotheses, not discoveries from a wholly unseen October sample. The supporting findings and hypotheses are recorded in the [September findings register](../../september/findings_register.md), and the proposed follow up work is summarized in the [October recommendation register](../../september/october_recommendation_register.md).

### Task 4 Status and Review Record

**Owner:** Leng Lim (D) · **Updated:** October 22, 2026 · **Gate 1 Status: NOT YET APPROVED.**

This Task 4 update incorporates Leng's supplied working draft. The source and implemented split passed the independent checks recorded in the [Gate 1 sign-off record](gate1_signoff.md). The split configuration, preprocessing proposal, CV design, experiment budget and team readiness decision still require agreement. Drafted documentation and merged implementations do not constitute gate approval.

### Plain-Language Prediction Task Statement

Estimate one auto insurance claim's final paid amount (`loss`) from the anonymous claim information assumed available when it is first filed. The supplied population contains paid claims; the [project overview](../../../Challenge-Project-Overview.md) states that closed claims without payment were excluded. All 188,318 supplied rows meet the frozen eligibility contract; October introduces no further exclusions.

The initial model inputs are the 130 original predictors: 116 nominal categorical fields (`cat1`–`cat116`) and 14 continuous fields (`cont1`–`cont14`). `id` identifies claims for integrity, partition membership and prediction tracing; `loss` is the target. Neither is an input. September summaries and derived fields are also excluded. Predictor availability is an Advisor-authorized assumption, not a verified interpretation of individual anonymous fields. Evaluate predictions using MAE in original `loss` units; internal evaluation does not establish future-period or production performance.

### Evaluation Metric Contract

The project requires **Mean Absolute Error (MAE) in original `loss` units**:

`MAE = sum(abs(actual_loss - predicted_loss)) / n`

Lower is better. Every reported score must identify:

- Model or baseline, experiment ID and configuration.
- Evaluation partition or CV fold, exact claim count and partition-manifest version/hash.
- Original-scale MAE, with transformed predictions returned to `loss` units before scoring.
- Model/preprocessing and evaluation-code commit identities, dependency versions and run receipt.
- For CV: fold construction, seed, each fold's claim count and MAE, pooled out-of-fold MAE, and mean/sample standard deviation across folds. CV scores describe development inside training; validation scores must be labeled separately.

Compare both constant predictors: the **training-mean baseline** and **training-median comparator**. Fit each constant on the applicable training rows only, including each CV training fold; do not use September's full-file descriptive mean or median. Check one finite prediction per claim and alignment by `id`. Do not drop failed predictions to improve a score. Any clipping or learned inverse-transformation correction must be declared before validation and learned within training.

The implemented [manifest](october_partition_manifest.csv), version `october-split-v1`, uses ID-only SHA-256 ranking with seed 42 and largest-remainder rounding:

| Partition | Proposed allocation | Implemented claims | Intended use |
| :--- | ---: | ---: | :--- |
| Training | 75% | 141,238 | Fitting and training-only CV/tuning |
| Validation | 15% | 28,248 | Limited comparison of frozen candidates |
| Internal test | 10% | 18,832 | Separately authorized November final evaluation |
| Total | 100% | 188,318 | Every eligible claim assigned once |

Integrity and reproducibility passed; formal acceptance of this configuration remains pending. The [split design](../../../docs/october_split_design.md) defines eligibility, limits and criteria for approving a new version. Keep the exact assignments; do not independently resplit or search seeds.

### Validation Use and Stopping Rules

**Policy ID:** `OCT-G1-T4-PROPOSAL-v1` · **PROPOSED — pending team agreement before fitting or tuning.**

Use one pipeline per approach. Refit all learned preprocessing within each CV training portion, including vocabularies, frequencies, rare grouping, scaling and any learned target correction. Validation and eventual test inputs are transform-only. Early stopping, if used, gets an inner holdout within the CV training portion, with preprocessing fitted only on the corresponding fitting rows; it must not use the external validation partition or the CV scoring fold for fitting or stopping.

| Budget component | Proposed limit and rule |
| :--- | :--- |
| CV construction | Five shuffled folds, seed 42, built from the training IDs sorted by integer `id`. Persist fold membership in Gate 2; confirm group/time assumptions before adopting claim-level folds. |
| Initial search | At most 6 configurations for Rachel's regularized GLM and 6 for Leng's XGBoost: at most 60 CV model fits. Freeze estimators, objectives, search spaces and complexity order before running. Choose one candidate per approach by pooled original-scale out-of-fold MAE. |
| Required controlled iteration | After the initial comparison, Leng runs one justified XGBoost iteration for #45. Change one factor, such as the rare-frequency cutoff, keeping other selected settings fixed. Compare at most 3 configurations with the same training folds: at most 15 additional CV fits. Freeze the iteration hypothesis/search before it runs and choose its single validation candidate using training CV only. |
| Final training fits | At most 3 refits on the full training partition: initial GLM, initial XGBoost and the iteration winner. Total cap: 75 CV fits plus 3 final refits. Baseline constants and unchanged independent reproduction runs are logged separately and cannot introduce new configurations. |
| Validation exposure | Two planned releases, at most 5 model/baseline score sets on the same 28,248 claims: initial mean, median, GLM and XGBoost, followed by the single CV-selected iteration candidate. Freeze each candidate before release. Do not score every tuning trial on validation. |
| Resource/schedule boundary | This small search is intended for the four-person October plan. Hardware capacity/runtime has not been benchmarked. Owners must confirm feasible resource settings and the Gate 3 deadline before adoption; the draft October 30 target is unconfirmed. Stop when the fit budget or agreed deadline is reached. |

Use unrounded scores for decisions. A candidate is eligible for provisional selection only if its validation MAE is strictly lower than **both** baselines. Eligible candidates within 1 original loss unit of each other are treated as a practical tie: prefer the GLM across families; within a family use the simpler configuration under the predeclared complexity order, then lower recorded runtime. This tolerance is a proposed decision rule, not a claim of statistical significance. A tie with a baseline does not qualify.

Log every attempt, including failures, configuration choices, CV results, runtime, changed factor and every validation access. Failed attempts consume their allocated configuration/fit slots; retries are logged and count toward the limits. An invalid run cannot become selection evidence. Independent reruns must reproduce an unchanged configuration and disclose repeated validation access.

Stop after reviewing the controlled iteration if no further experiment is authorized, or earlier for exhausted budget/deadline or a blocking integrity/pipeline defect. If required approaches or the iteration are incomplete, record that Gate 3 remains incomplete. If no valid candidate beats both constants, record **no selection** and a proposed next experiment. Any extra search or validation comparison needs a written team-approved amendment, independent review, a training-evidence/defect rationale and disclosure of prior exposures before execution. Never use test outcomes to justify an amendment.

Keep internal-test target results unused throughout October development and selection. November release requires a frozen candidate, preprocessing, metric code and selection procedure, plus separate team authorization. September already examined the full file, so this internal test cannot be described as historically unseen evidence.

### Challenge Advisor Questions and Responses

Rachel sent the filing-time availability question on the team's behalf on **October 11, 2026**. Krystal Smuda replied in writing on **October 12**. Leng's Task 4 contribution is to incorporate and verify this guidance. The [recommendation register](../../september/october_recommendation_register.md) dates the guidance to October 13; the [sign-off record](gate1_signoff.md#advisor-evidence) identifies the primary email and chronology.

The Advisor confirmed that supplied fields may be assumed available at claim filing/model use and recommended reserving a test set for final evaluation with CV inside training. These answers do not approve the exact 75/15/10 proportions, seed 42, five CV folds, model families or experiment budget. The Advisor also raised collinearity concerns for GLMs and cautioned that correlated predictors can make tree feature importance unreliable.

Remaining questions concern shared policyholder/vehicle/group structure, temporal dependencies, upstream continuous-feature scaling/processing, external or future-period evaluation data, target-transformation constraints and interpretation/deliverable expectations. Leng coordinates the question record with Krish on split implications and Rachel on modeling implications. Record answers or explicit team acceptance of remaining assumptions before affected work proceeds. No repeat Advisor message is needed for the answered filing-time question.

### October Work Plan and Task Tracking

The [coach's October guide](https://github.com/Break-Through-Tech/Allstate-1C-predicting-auto-claims-severity/blob/d19ccbf7bd9258d13a62fad13ef618f5bb76e674/docs/coach/october-execution/Allstate-Oct-Milestones.md) requires week-by-week planning, carryover and board updates by October 11. It does not establish the gate dates below. These are **planning targets from Leng's draft, pending team confirmation**, not verified board deadlines. As of October 22 the Gate 1 target has passed; rebaseline remaining dates explicitly and do not backdate approval.

| Gate / draft target | Hector (A) | Krish (B) | Rachel (C) | Leng (D) | Dependency and completion evidence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 — October 16 | #34: freeze contract/handoff | #35: split and manifest | #36: preprocessing and two approaches | #37: plan, metric, Advisor record and review | September handoff approved. Data/split checks pass; PR #52 corrections and recorded team decisions remain. |
| 2 — October 23 | #38: implement pipeline | #39: shared MAE and both baselines | #40: training CV folds/target handling | #41: independent baseline/pipeline review | Requires approved Gate 1 design; persist folds, pin dependencies, verify unknown handling and original-scale scoring. |
| 3 — October 30 | #42: experiment register/model audit | #43: comparison/error analysis | #44: train/tune GLM | #45: train/tune XGBoost and one iteration | Requires Gate 2 verification; compare frozen candidates with both baselines, log attempts/exposures and report high-loss support/errors. |
| 4 — November 6 | #46: clean rerun/artifact bundle | #47: provisional/no-selection report | #48: independent results verification | #49: November handoff/presentation | Requires Gates 1–3; preserve receipts, review exact versions and record team handoff. Test release is a separate November decision. |

Issue numbers refer to the [repository issues](https://github.com/Break-Through-Tech/Allstate-1C-predicting-auto-claims-severity/issues). Owners above follow the supplied A–D assignment; live issue assignees have not been reconciled. Each issue needs evidence, a reviewer and its gate dependency before it is represented as accepted work.

### September Carryover and Open Decisions

The accountable owners below are proposed from the task assignments; confirm them during board reconciliation.

| Carryover / decision | Intended handling | Accountable owner / task |
| :--- | :--- | :--- |
| High-cardinality, rare and unseen categories | Fit mappings within training folds; proposed support <30; verify fallback without dropping claims. | Hector #38; Rachel reviews plan #36 |
| Sparse high-loss claims | Retain valid claims; define error slices from training and report slice support with overall MAE. | Krish #43 |
| Correlated continuous predictors | Retain initial inputs; document L2 treatment for GLM and limits on individual tree importance. Any sensitivity experiment stays within the budget. | Rachel #44; Leng #45 |
| Anonymous fields / supplied paid-claim population | Do not assign business meanings or claim performance on unpaid/future claims without evidence. | Krish #47; all model owners |
| Full-file September EDA exposure | Treat model ideas as prior hypotheses; derive fitted rules within training and disclose limits of the internal test. | Leng #37; Krish #47 |
| Unknown group/time structure and scaling provenance | Seek Advisor clarification; approve constraints or document residual assumptions before affected modeling. | Leng #37 with Krish #35 and Rachel #40 |
| Historical pending-review notes / FND-008 | Follow the later September Gate 4 approval for the handoff. The specific classification-rule decision remains unreconciled; do not adopt its labels as a confirmed modeling rule. | Hector #34; Leng #37 |
| Reproducibility, migrated paths and version drift | Preserve frozen evidence; assign a separate current-path/validator follow-up. Pin and record the Gate 2 environment. | Hector #38/#46; repository follow-up owner to be agreed |

Rachel's PR #52 proposes handling all 12 recommendations: adopt the source, metric, training boundary and evaluation obligations; scope the first comparison to GLM/XGBoost; defer a broader encoder/family comparison and optional feature-removal experiments. Leng supports this scope as a proposal. Team adoption remains pending; frozen September decisions are unchanged.

### GitHub Task Tracking

The [Allstate 1C Projects board](https://github.com/orgs/Break-Through-Tech/projects/49) could not be inspected: the connected GitHub tools have no Projects capability and no browser is connected. **No board or issue update has been made.** The [sign-off record](gate1_signoff.md#board-reconciliation-checklist) contains an issue-by-issue checklist for an authorized manual update.

On October 22, all issues #34–#49 were open and unassigned; only #34 had a milestone. PRs #50 and #51 were merged; PR #52 remained open. These are repository/issue facts, not verified board statuses. Keep merged implementation, independent verification and team approval distinct. [Issue #37](https://github.com/Break-Through-Tech/Allstate-1C-predicting-auto-claims-severity/issues/37) remains incomplete until board reconciliation and the readiness decision are evidenced.

### Task Ownership and Model Approaches

A/Hector owns the contract, implementation pipeline, experiment audit and bundle; B/Krish owns splitting, baseline evaluation, comparisons and reporting; C/Rachel owns the preprocessing proposal, CV, Approach 1 and independent Gate 4 verification; D/Leng owns gate coordination, independent review, Approach 2/iteration and the November handoff.

- **Approach 1 — regularized GLM, Rachel:** a simple penalized linear reference using one-hot categories and standardized continuous fields. Hypothesis: it improves over constants while exposing whether nonlinear complexity adds value.
- **Approach 2 — XGBoost, Leng:** Leng confirms support for XGBoost as the proposed second approach in this Task 4 update. Hypothesis: nonlinear relationships/interactions improve validation MAE over the GLM. This model-owner confirmation does not approve Gate 1 or select a winning model.

Both proposals draw on September full-file EDA and need training-only evaluation. Exact estimator/objective, search settings, version pins and resource limits must be recorded before running.

### Independent Review — September Handoff and Data Contract

**Executed integrity checks: PASS.** The source hash, 188,318 eligible rows, 132 ordered columns, field roles, nonmissing/unique IDs, target validity, 130-input feature contract and archived reference hashes were independently rechecked. The split also rebuilt byte-for-byte from IDs alone. Exact identities, scope and a repeatable standard-library check are in the [sign-off record](gate1_signoff.md#executed-independent-checks).

The final September sign-off records full-team approval on October 6 and supersedes older pending-review narratives for the handoff. Ten historical anomalies have recorded resolutions; some retain historical pending-review wording. This review neither reruns September EDA nor changes those records. The FND-008 rule's specific approval remains unreconciled. No pipeline implementation or model-performance approval follows from these integrity results.

### Independent Review — Preprocessing and Experiment Plan

Reviewed [PR #52](https://github.com/Break-Through-Tech/Allstate-1C-predicting-auto-claims-severity/pull/52) at `68abeea8c9f9e2169fe79e11d68e03ac00b191db`. The proposal documents fold-local fitting, unordered categories, training-frequency grouping at support <30, GLM one-hot encoding, XGBoost native categories with a one-hot fallback, safe unknown handling, GLM-only standardization, retained correlated predictors, exclusion of target encoding and original-scale MAE. These are **document-only assessments**, not executed pipeline tests.

Independent category checks found **13 field-level unseen occurrences affecting 12 distinct validation claims**; PR #52 currently says 13 claims. Its notebook check labeled as verifying test diagnostics checks policy-text wording instead of the actual artifact. Training-only sizing agrees with the proposal: 352 rare levels across 30 fields and one-hot width 1,116 to 794.

Rachel's files remain unchanged. [Prepared review comments](gate1_signoff.md#prepared-pr-52-comments) identify corrections for her. Version pins, native-category/missing fallback, finite predictions, CV implementation and the shared metric code remain Gate 2 verification work. **Gate 1 stays NOT YET APPROVED** until findings and team decisions are resolved or explicitly accepted in a recorded readiness review.
