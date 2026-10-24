# October Preprocessing and Experiment Plan

**Gate 1 · Preprocessing and experiment plan** · Owner: Rachel Cheung · Drafted 2026-10-19 · **Status: PROPOSED, pending team approval at the Gate 1 review.** Model approaches also need agreement from the Approach 2 owner.

This plan sets the rules that the Gate 2 pipeline must implement. Nothing here fits a model, encoder, or baseline. It builds on the [Gate 1 data contract](gate1_overview.md) (all 188,318 eligible claims, all 130 source predictors, `id` and `loss` excluded from inputs) and the proposed `october-split-v1` partitions (75% train, 15% validation, 10% sealed test).

## 1. Fitting boundary

Every learned value is fit on the **training partition only**, and refit on the training portion of each cross-validation fold. Validation and test rows are transform-only. Each approach is built as one pipeline object (preprocessing plus model) so that fitting the pipeline fits everything inside the boundary at once.

| Learned value | Fit on | Applied to |
| :--- | :--- | :--- |
| Category vocabulary per `cat*` field | Training rows (each CV training fold) | Validation, test, CV held-out fold |
| Category frequencies and the rare-level grouping they imply | Training rows | Same |
| Continuous scaling (GLM only: mean and standard deviation) | Training rows | Same |
| Any target transformation correction, if adopted in Week 2 | Training rows | Predictions only |
| Model parameters and tuned settings | Training rows, tuned with CV inside training | Same |

Not used as inputs: `id`, `loss`, `log1p_loss`, September bin labels, target summaries, and any value computed from validation or test rows.

## 2. Nominal categories

- Keep all 116 `cat*` fields as **string labels**. Never convert labels to integers that imply an order; the source codes (A, B, …, AA, …) carry no meaning.
- **GLM:** one-hot encoding of the training vocabulary, including every level (no dropped reference level, since the penalty in Section 5 handles the redundancy).
- **XGBoost:** native categorical splits, with each field cast to a categorical type whose categories are fixed to the training vocabulary. This lets trees split on groups of levels without an artificial order. If native categorical support fails for the installed version, fall back to the same one-hot encoding as the GLM and record the change.

## 3. Rare levels

- A level is **rare** if it appears fewer than **k = 30** times in the training rows being fit. Within each field, all rare levels are grouped into one `__rare__` level. Source labels in the data file are never changed.
- **Why 30, and not September's 100:** September's `support < 100` rule was an EDA display rule on the full file and is not automatically the modeling threshold (OCT-REC-006). k = 30 is a moderate starting point. A training-only sizing check shows that in the training partition, 352 levels across 30 fields fall below 30, and one-hot width drops from 1,116 columns to about 794.
- k is a **declared starting value, not a tuned one.** Comparing k ∈ {10, 30, 100} with training-only CV is a ready candidate for the Week 3 one-change iteration.
- Grouping is recomputed on each CV training fold, so a level that is rare in one fold may not be rare in another. That is expected.

## 4. Unseen levels

A level is **unseen** if it never appears in the training rows that were fit. In the current split, 13 validation claims have an unseen level (8 in `cat116`; 1 each in `cat105`, `cat107`, `cat109`, `cat110`, `cat114`), from Krish's coverage file and confirmed in the [split review](split_manifest_review.md).

- **GLM:** an unseen level is mapped to that field's `__rare__` column. If a field has no rare levels, all of its one-hot columns are zero, which means the prediction uses only the penalized intercept and other fields.
- **XGBoost:** an unseen level becomes missing and follows the default branch the tree learned for missing values.
- Unseen levels must never raise an error or drop a row. The Gate 2 pipeline includes a test that feeds made-up labels into every field and checks one finite prediction per claim.
- Gate 2 reports how many validation claims were affected, using counts only and never validation `loss`.

## 5. Continuous fields and missing values

- `cont1`–`cont14` are kept as supplied (already on a 0–1 scale). For the GLM only, they are standardized using training mean and standard deviation so the penalty treats them evenly. Trees need no scaling.
- The correlated pairs `cont11`/`cont12` (0.994) and `cont1`/`cont9` (0.930) are **retained**. The GLM's L2 penalty spreads weight across correlated fields instead of making coefficients unstable, and tree importance for those pairs is reported as shared, not individual (OCT-REC-007).
- The source has no missing values. The pipeline checks the schema at entry and **stops with an error** if a column is missing, renamed, or has missing continuous values. A missing category label is treated as unseen.

## 6. Target encoding: out of scope for the first comparison

**Decision: target encoding is not used in the first model comparison.**

- One-hot with rare grouping (GLM) and native categorical splits (XGBoost) already handle the high-cardinality fields (`cat116` has 312 training levels, `cat110` 130, `cat109` 83) without using the target.
- Target encoding uses `loss` to build inputs, which is the leakage risk the October scope protections warn about, and September already examined level-to-target relationships across the full file.
- **If it is proposed later** (for example, if `cat116` handling clearly limits the GLM), it must use K-fold cross-fitting inside each training fold, smooth toward the training-fold mean, and send rare and unseen levels to the training-fold mean. That would be logged as a separate experiment against the same split.

## 7. Model approaches

Both follow the required training-mean baseline and training-median comparator, and are scored by MAE in original `loss` units on the same validation claims. Whether to train on `loss` or a transformed target is decided in Week 2; either way, predictions are converted back to `loss` units before scoring.

| | Approach 1: Regularized GLM | Approach 2: XGBoost |
| :--- | :--- | :--- |
| **Owner** | Rachel Cheung (Week 3) | Approach 2 owner (Week 3) — to confirm |
| **Model** | Linear model with an L2 (ridge) penalty, on one-hot categories and standardized continuous fields | Gradient-boosted decision trees (`hist` method) with native categorical splits |
| **Hypothesis** | September found weak, mostly additive marginal signals. A penalized linear model should beat both constant predictors, but will miss nonlinear effects and interactions between fields. | September's binned views suggest nonlinear patterns, and 116 categorical fields invite interactions. Boosted trees should reach a lower validation MAE than the GLM. |
| **Practical reason** | Fast, simple to explain to the Challenge Advisor, and a structured reference point for judging whether added complexity pays off. Handles correlated predictors through its penalty. | Explicitly named in the project overview, fits 141,238 claims quickly, handles categories without an imposed order, and can optimize absolute error directly. |
| **Tuning (training only)** | Penalty strength, chosen with CV inside the training partition | Learning rate, depth, number of trees, and regularization, chosen with CV inside training. Early stopping uses an inner training fold, never the validation partition. |

**Deferred:** random forest (heavy on memory with about 800 one-hot columns, and overlaps with XGBoost as a tree ensemble) and scikit-learn's GBM (the same family as XGBoost). Both remain valid November options. The Gate 2 environment must add `scikit-learn` and `xgboost` to `requirements.txt` with pinned versions; neither is pinned today.

## 8. October Recommendation Register review

Classification of all 12 entries in the [register](../../september/october_recommendation_register.md):
**Adopt** = becomes October work · **Defer** = not in October · **Reopens September** = would change a frozen September gate if adopted.

| ID | Topic | Decision | October handling |
| :--- | :--- | :--- | :--- |
| OCT-REC-001 | Frozen source and field roles | **Adopt** | Done in Gate 1 Task 1. Schema and hash checked at every experiment's entry. |
| OCT-REC-002 | Validation design | **Adopt** | Implemented as `october-split-v1` (75/15/10, seed 42) by Krish; pending team approval. CV folds are built inside training in Week 2. |
| OCT-REC-003 | Both constant baselines, original-scale MAE | **Adopt** | Gate 2: training mean and training median, scored on validation and on each CV fold. |
| OCT-REC-004 | Training-only preprocessing, safe unknowns | **Adopt** | Sections 1–5 of this plan. |
| OCT-REC-005 | High-cardinality encoding comparison | **Adopt, scoped** | Each approach uses one family-appropriate encoding (Section 2). A full encoder comparison is **deferred**. |
| OCT-REC-006 | Rare-level grouping and unseen levels | **Adopt** | k = 30 training-frequency grouping plus unseen fallback; k sensitivity is a Week 3 iteration candidate. |
| OCT-REC-007 | Correlated-predictor sensitivity | **Adopt, scoped** | Retain all fields; GLM uses an L2 penalty. A retain-versus-omit comparison is **deferred** as an optional feature experiment. |
| OCT-REC-008 | Project model families | **Adopt, scoped** | GLM and XGBoost now; random forest and GBM **deferred** (Section 7). |
| OCT-REC-009 | Target transformation | **Adopt** | Decided in Week 2 (training-fold setup and target handling). MAE is always computed in original units. |
| OCT-REC-010 | Error and high-loss diagnostics | **Adopt** | Week 3 comparison. The high-loss slice uses the **training** p95 (8,511.92), not the September full-file p95. |
| OCT-REC-011 | Reproducibility and September review | **Adopt**, with one item that **reopens September** | Gate 4 sign-off records completed independent review, so October keeps the receipt practice. But the FND-008 binned-pattern rule is still unapproved in the Gate 3 sign-off. **No October decision may rely on FND-008 "non-monotonic" labels**; doing so would reopen September Gate 3. |
| OCT-REC-012 | Open Challenge Advisor questions | **Adopt** (partly resolved) | Oct 13 answers recorded (fields available at filing; reserve a test set; CV in training). Group/time structure, scaling provenance, and target-transform constraints stay open; owned by the Advisor-questions task. |

No recommendation requires changing a September artifact, field role, or approved method. The only reopening risk is relying on the unapproved FND-008 rule, and this plan does not.

## 9. Experiment record

Every run, including failed runs and baselines, gets a filled-in copy of the [experiment record template](experiment_record_template.md). Feature inclusion or exclusion experiments are marked **optional, if time permits**.

## 10. Prior EDA exposure

These plan choices draw on September's full-file EDA: the rare-level concern (FND-002), high-cardinality fields (FND-004), correlated pairs (FND-001), weak marginal relationships (FND-007), and nonlinear binned patterns (FND-008, unapproved rule). They are treated as hypotheses. Any target-informed choice is recalculated inside training data before it is used, and no September full-file statistic is reused as a fitted value.