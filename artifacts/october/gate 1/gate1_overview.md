# October Gate 1 Overview

### September Handoff

September Gate 4 was approved by the full team on October 6, 2026. October modeling work will use the approved September evidence rather than repeat the September analysis. The final decision, Artifact Bundle ID, Workflow Run ID, source hash, approvals, unresolved risks, and reproduction details are recorded in the [September Gate 4 sign-off](../../september/gate4_signoff.md).

### Frozen Data Contract
October inherits the approved source and field roles documented in the [September artifact manifest](../../september/artifact_manifest.json). The first modeling run starts with all 188,318 eligible rows and all 130 source predictors. `id` is reserved for integrity and prediction tracing, while `loss` remains the regression target; neither is a model input. Summaries and derived analysis fields are also excluded from the initial feature set.

### Open Issues
The main issues carried into October are handling of rare or unseen categories to avoid leakage, evaluation of errors among high-loss claims, and the limits created by anonymous fields and the lack of the following period data. Historical anomalies and their resolutions remain available in the [September anomaly register](../../september/anomaly_register.md).

### Prior Exploratory Data Analysis (EDA) Exposure
September examined target relationships across the full supplied file. Its modeling ideas must therefore be treated as prior hypotheses, not discoveries from a wholly unseen October sample. The supporting findings and hypotheses are recorded in the [September findings register](../../september/findings_register.md), and the proposed follow up work is summarized in the [October recommendation register](../../september/october_recommendation_register.md).

### Preprocessing and Experiment Plan
Every learned preprocessing value (category vocabularies, frequencies, rare-level groups, scalers) will be fit on the training partition only, and refit inside each cross-validation fold. Categories stay as unordered labels: one-hot encoding for the GLM and native categorical splits for XGBoost. Levels seen fewer than 30 times in training are grouped into one rare level per field, and levels never seen in training are handled without errors. Target encoding is out of scope for the first comparison. The two proposed approaches are a regularized GLM and XGBoost, each compared against the training-mean baseline and training-median comparator by MAE in original `loss` units. All 12 recommendations were reviewed: none requires changing September work, but October decisions must not rely on the still-unapproved FND-008 binned-pattern rule, which would reopen September Gate 3. Details are in the [preprocessing and experiment plan](preprocessing_experiment_plan.md), and every run will use the [experiment record template](experiment_record_template.md).

### Independent Split Review
The proposed `october-split-v1` partition manifest (141,238 train, 28,248 validation, 18,832 sealed test claims) was independently reviewed and passed every check: it reproduces byte-for-byte, the assignment rebuilds from claim IDs alone, every eligible claim appears exactly once, and no test targets were inspected. The review recommends approving and merging the split, and recording that validation is used for comparing approaches while tuning stays inside training. See the [split manifest review](split_manifest_review.md).
