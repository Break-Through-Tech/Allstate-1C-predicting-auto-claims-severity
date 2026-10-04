# September Data Understanding Report

**Project:** Allstate — Predicting Auto Claims Severity  
**Milestone:** September Data Understanding  
**Gate:** Gate 4 — September Complete  
**Author:** Leng Lim — Task 2: September report and limitations

## 1. Dataset and Unit of Analysis

The September analysis uses the supplied Allstate auto insurance claims dataset. The dataset contains **188,318 rows and 132 columns**. Each row represents one auto insurance claim and includes the total paid amount for that claim along with anonymized claim and vehicle characteristics.

The fields are organized into four main groups:

- `id` is the unique identifier for each claim record, used for integrity checks rather than predictor interpretation.
- `cat1` through `cat116` are **116 anonymous categorical predictors**. Their values are nominal categories: labels with no assumed order. The actual business meanings of the fields and category labels are not provided.
- `cont1` through `cont14` are **14 anonymous continuous predictors**. Their observed values fall within the range **[0, 1]**, but their original meanings and units are unknown.
- `loss` is the target variable and represents the **total paid amount for the claim**. The project goal is to predict this final claim cost from information available in the other fields.

Because the predictors are anonymous, the September analysis focuses on their distributions, support, relationships with `loss`, and relationships with one another rather than assigning business meanings to individual fields.

The [project overview](../Challenge-Project-Overview.md) states that claims closed without payment are excluded. The delivered file has only positive losses; that observation does not independently establish why any individual claim was included. Field roles and handling are documented in the [data dictionary v1.1.0](../artifacts/data_dictionary_v1.1.0.csv).

## 2. Target Distribution

The target variable, `loss`, is the final paid claim amount. Its distribution matters because the project will eventually train regression models to predict this value, and the shape of the target affects how model performance should be interpreted. Amounts below are reported in the original loss units recorded in the file.

The distribution of `loss` is strongly right-skewed:

- Mean loss: **3,037.34**
- Median loss: **2,115.57**
- 95th percentile: **8,508.54**
- 99th percentile: **13,981.20**
- Maximum loss: **121,012.25**
- Raw skewness: **3.795**

The mean is about **1.44 times the median**, showing that a relatively small number of large claims pull the average upward. The largest 1% of claims account for approximately **6.07% of total paid loss**, while the largest 5% account for approximately **19.85%**.

In plain language, most claims have much smaller losses than the largest claims, while a thin group of expensive claims creates a long right tail. These large claims are sparse, but they are economically meaningful because they represent a substantial amount of the total paid loss.

A `log1p(loss)` transformation was also examined to make the main body of the distribution easier to visualize. Its skewness is approximately **0.097**, compared with **3.795** for the raw target. This transformed view is exploratory only. It does not show that a model trained on the transformed target will perform better.

Evidence: [target summary](../artifacts/target_summary.csv) and the raw and transformed target figures in the [notebook](../notebooks/data-understanding.ipynb), Gate 2 Task 1 and Gate 3 Task 1.

## 3. Data-Quality Findings

The supplied dataset is clean at the basic structural level.

September checks found:

- **188,318 unique `id` values** across 188,318 rows;
- **0 missing cells**;
- **0 exact duplicate rows**;
- all continuous predictor values within **[0, 1]**; and
- all `loss` values finite and positive.

These results mean that major repair steps such as missing-value imputation or duplicate removal are not required for the supplied September data.

However, structural cleanliness does not prove that every value is semantically correct. The meanings of the anonymous predictors and the upstream processing used to generate or scale them are undocumented. The project therefore cannot verify whether an unusual value is reasonable from a business perspective based on this file alone.

The September workflow also identified and corrected several documentation, reproducibility, and processing issues. These included executable notebook code, deterministic sorting, dependency-version checking, continuous-field evidence coverage, source-hash documentation, continuous-range wording, anomaly-check logic, derived-field documentation, machine-readable target summaries, the Artifact Manifest, and the official reproducible workflow run.

The recorded corrections did not change the established headline target statistics. Their purpose was to improve evidence coverage, traceability, documentation, and reproducibility. Reasons and handling decisions are recorded in the [anomaly register](anomaly_register.md).

Two corrections affected how findings were described or supported. G3-DOC-006 corrected the continuous-range wording to the inclusive **[0, 1]** because `cont10` includes zero and `cont7` includes one; no source values or range checks changed. G3-EDA-004 completed continuous evidence that was missing at code revision `c5aa654`. The completion and findings-register revision to **v2.0.0** were committed in `e893e2e`; FND-007 and FND-008 now have evidence for all 14 continuous fields. This was a coverage correction rather than a revision to target statistics.

The corrected official run, **`WR-SEPT-G4-20261002T205412Z-03140d1`**, used code revision `03140d1` and produced bundle **`SEPT-BUNDLE-78876ab8c12d`**. Its source, code, configuration, and artifact hashes are recorded in the [Artifact Manifest](../artifacts/artifact_manifest.json) and [Gate 4 sign-off](gate4_signoff.md); its executed notebook outputs were committed in `ab17125`. The receipt reports **COMPLETED WITH WARNINGS** because independent human review remains pending. The [Gate 3 sign-off](gate3_signoff.md) contains matching alternative-calculation results, but reviewers are still marked `PENDING` and `independent: false`. The required independent recheck must be completed and recorded before final gate approval.

Evidence for structural checks: [source profile](../artifacts/source_profile.csv) and the [notebook](../notebooks/data-understanding.ipynb), Gate 3 Task 1.

## 4. Categorical Predictor Findings

The dataset contains **116 categorical predictors** with a mixture of low and high cardinality. Cardinality means the number of distinct category labels in a field; support means the number of claims carrying a particular label. For September display purposes, fields with more than 10 levels are called high-cardinality.

Most categorical fields contain relatively few levels:

- **72 fields are binary**;
- **88 fields contain four or fewer levels**; and
- **17 fields contain more than 10 levels**.

Some fields have substantially higher cardinality. For example:

- `cat116` contains **326 levels**;
- `cat110` contains **131 levels**; and
- `cat109` contains **84 levels**.

Support also varies substantially across category levels. Using the September exploratory definition of fewer than 100 claims as low support, **35 fields contain a total of 469 rare levels**.

An extreme example is `cat101` level `H`, which appears in only **1 of 188,318 claims**. At the opposite extreme, `cat70` level `A` appears in **188,295 of 188,318 claims**, or approximately **99.99%** of records.

These patterns matter because target statistics calculated from extremely small groups can be unstable. A very large or small average loss for a category represented by only a handful of claims should not be treated as strong evidence.

Some categorical levels meeting the September support rule also show substantial differences in their observed loss distributions. For example, `cat57` has two such levels, selected as an exploratory example because of its large supported median-loss difference:

- `cat57 = A`: 185,296 claims, median loss approximately **2,081.93**
- `cat57 = B`: 3,022 claims, median loss approximately **9,532.34**

This is a substantial observed difference, but it does not establish that `cat57` causes higher losses or that the field will necessarily improve a predictive model. The field is anonymous, and relationships with other predictors have not yet been separated.

High cardinality, low support, or dominance alone also do not justify deleting a field. The September support threshold is an EDA rule, not an approved modeling threshold. Encoding and rare-level handling must be fitted using training data and evaluated on held-out validation data during October modeling.

Evidence: [categorical inventory](../artifacts/categorical_inventory.csv), [high-cardinality evidence](../artifacts/categorical_high_cardinality_evidence.csv), [low-support evidence](../artifacts/categorical_low_support_evidence.csv), [dominance evidence](../artifacts/categorical_dominance_evidence.csv), and [categorical target evidence](../artifacts/categorical_target_evidence.csv).

## 5. Continuous Predictor Findings

The continuous predictors share a delivered scale within **[0, 1]**, but their distributions differ. Their means range from approximately **0.485 to 0.507**, while their medians range from approximately **0.364 to 0.556**. Some fields contain many repeated values: `cont2` has **33 distinct values**, compared with **18,740** for `cont14`. These summaries describe the delivered values; the original units and scaling procedures remain unknown. Per-field histograms and boxplots are preserved in the notebook, Gate 3 Task 4.

For target comparisons, each field was divided into up to ten groups based on its value quantiles, with support and raw mean, median, and interquartile range of loss recorded for each group. Repeated values prevent ten distinct groups for every field: `cont2` has **nine bins** and `cont5` has **eight**. These bins describe patterns in the supplied file; they are not fitted modeling transformations.

The 14 continuous predictors generally show weak marginal linear relationships with `loss`, meaning each field's relationship is examined separately.

The strongest absolute Pearson correlations with raw `loss` are:

- `cont2`: approximately **0.142**
- `cont7`: approximately **0.120**
- `cont3`: approximately **0.111**

Additionally, **9 of the 14 continuous predictors have an absolute Pearson correlation below 0.05**.

These values show that no individual continuous predictor has a strong straight-line relationship with `loss` by itself.

Weak correlation does not mean that a variable has no predictive value. Correlation measures only a limited form of relationship and does not capture interactions or many nonlinear patterns.

The binned-target analysis suggests nonlinear structure in several predictors. Under the **proposed Gate 3 classification rule, which still awaits team approval**, **8 of 14 continuous fields** are classified as having non-monotonic binned median-loss patterns, meaning the medians do not follow a strong consistent increasing or decreasing trend under that rule:

`cont1`, `cont2`, `cont4`, `cont6`, `cont7`, `cont10`, `cont12`, and `cont14`.

Under the same proposed rule, `cont3` and `cont11` are classified as showing monotonic trends, while `cont5`, `cont8`, `cont9`, and `cont13` are classified as inconclusive. These labels summarize the binned medians and do not prove that the underlying relationships are strictly monotonic or nonlinear.

The rule requires a bin-median spread of at least 10% of the overall median loss and at least two bins with non-overlapping 95% bootstrap intervals. It then labels a trend as monotonic when the absolute bin-order rank correlation is at least 0.8, and otherwise labels it non-monotonic. These are exploratory, single-field comparisons. The intervals describe uncertainty for individual bins rather than simultaneous uncertainty across all comparisons. Classifications are sensitive near the thresholds: `cont11` and `cont12` receive different labels despite their strong correlation. Patterns may also reflect relationships with other predictors.

One useful example is `cont14`. Its Pearson correlation with `loss` is only about **0.019**, yet the difference between its highest and lowest bin medians is approximately **32.57% of the overall median loss**. This illustrates why correlation alone is insufficient for deciding whether a predictor should be retained.

### Continuous Redundancy

Several continuous fields are also strongly correlated with one another:

- `cont11` and `cont12`: **r = 0.994**
- `cont1` and `cont9`: **r = 0.930**
- `cont6` and `cont10`: **r = 0.883**

Overall, **5 of the 91 continuous-predictor pairs** have an absolute Pearson correlation above 0.8.

This indicates that some predictors contain highly overlapping linear information. It does not establish that `cont11` and `cont12` are interchangeable in a predictive model.

The reason for this redundancy cannot be determined because the variables are anonymous. These fields should therefore remain available for October modeling, where the effect of removing or retaining them can be evaluated using held-out MAE rather than assumptions based only on correlation.

Evidence: [continuous inventory](../artifacts/continuous_inventory.csv), [binned-target table](../artifacts/continuous_bin_target.csv), and the strongest-pairs table and distribution figures in the [notebook](../notebooks/data-understanding.ipynb), Gate 3 Task 4. Interpretation and limitations are recorded in [FND-001, FND-007, and FND-008](findings_register.md).

## 6. What Remains Unknown

The largest limitation of the September analysis is that all **130 predictors** are anonymized.

The dataset does not tell us what any specific `cat*` or `cont*` field represents. The project overview provides examples of possible insurance features, but those examples do not map specific business concepts to specific columns.

Because of this anonymity, September evidence cannot determine why a particular field is associated with higher or lower losses. For example, a difference between two levels of a categorical field can be measured, but it cannot be connected to a specific claim characteristic or business mechanism.

Without field documentation, the team also cannot verify which predictors would be available when a claim is first filed or whether a field contains information collected later. This remains an unanswered question rather than evidence that leakage is present.

The data also contains only one labeled file. There is no separate future-period dataset or external test dataset. Therefore, the September analysis cannot determine whether these distributions and relationships will remain stable for future claims.

## 7. Work Deferred to October

September focused on understanding and documenting the data rather than building and evaluating predictive models.

October evaluation will use mean absolute error (MAE), the average size of the difference between predicted and actual loss, in the original loss units. The following tasks and questions are deferred to October model development:

- creating training and validation partitions from the supplied dataset;
- establishing baseline model performance using MAE;
- comparing linear and nonlinear modeling approaches;
- testing whether training with a transformed target such as `log1p(loss)` improves held-out MAE after predictions are returned to the original loss scale;
- testing encoding approaches for categorical variables;
- testing methods for handling rare and previously unseen categorical levels;
- evaluating whether highly correlated or apparently weak predictors can be removed without worsening validation MAE;
- evaluating whether nonlinear patterns observed during September provide useful predictive information; and
- fitting all preprocessing decisions using training data only to prevent validation leakage.

These are future modeling tasks and experiments rather than demonstrated September results. Their motivation is recorded in the [findings register and October hypotheses](findings_register.md); the detailed recommendation register and modeling handoff are separate Gate 4 Task 3 deliverables.

## 8. Limitations and What the Evidence Does Not Justify

The September findings should be interpreted within several important limitations.

### Anonymous fields

The actual meanings of the predictor fields are unknown. Observed relationships cannot be translated into specific insurance or claim mechanisms without additional documentation.

### Association is not causation

Differences in loss between categories or correlations between continuous fields and `loss` describe associations within this dataset. They do not establish causal relationships.

Marginal association also does not establish complete predictive usefulness. A feature with weak individual correlation may still contribute through nonlinear relationships or interactions with other variables.

### Large claims are sparse but economically meaningful

Very large claims occur much less frequently than ordinary claims, but they account for a meaningful share of total paid loss. They should not automatically be removed as outliers without evidence that they are incorrect.

### Future stability is unknown

This analysis uses one labeled dataset with no separate future period. It therefore cannot establish whether predictor distributions, target distributions, category support, or predictor-target relationships will remain stable over time.

### Target transformations are exploratory

The `log1p(loss)` plots make the highly skewed target easier to inspect. They are not model-evaluation results. Whether a transformed training target improves predictive performance must be tested using held-out data and MAE in the original loss units.

### September does not establish production readiness

The September EDA does not demonstrate that any model is accurate, calibrated, stable, fair, operationally reliable, or ready for production.

No predictive model has been validated as part of this milestone.

### September does not establish an appropriate reserve for an individual claim

Although the larger project is motivated by estimating final claim costs and informing reserve decisions, the September analysis alone cannot determine an appropriate reserve for a specific claim.

Individual reserve recommendations would require a validated modeling process, appropriate performance testing, business review, and additional operational considerations.

## 9. September Conclusion

September established a reproducible understanding of the supplied Allstate claims dataset.

The dataset is structurally clean, with no missing values or duplicate rows, but its anonymous predictors create important interpretation limits. The target has a strong right-skewed distribution in which a small number of expensive claims have meaningful economic impact.

Categorical predictors range from simple binary fields to high-cardinality fields containing rare levels, while continuous predictors show generally weak marginal linear relationships with the target, exploratory binned patterns, and some strong redundancy with one another.

These findings provide evidence for designing the October modeling experiments, but they do not establish causation, feature usefulness, future distribution stability, model performance, production readiness, or appropriate claim-level reserves.

All confirmed September data-processing and workflow defects in the [anomaly register](anomaly_register.md) have recorded fixes, including the official run that closes G4-WF-010. Review of several fixes remains pending. Final Gate 4 approval still depends on the independent reviews and team decisions recorded as incomplete in the [Gate 3 sign-off](gate3_signoff.md) and [Gate 4 sign-off](gate4_signoff.md). This report does not mark those approvals or rechecks as complete.
