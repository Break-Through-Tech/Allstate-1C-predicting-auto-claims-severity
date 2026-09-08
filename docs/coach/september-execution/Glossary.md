# Glossary

Terms are arranged alphabetically. Use the table of contents to jump directly to
an entry. These definitions apply to the September Allstate milestone unless the
Challenge Project Overview or an approved project decision provides a more
specific definition.

## Table of Contents

- [A](#a-entries)
  - [Absolute error](#absolute-error)
  - [Analysis contract](#analysis-contract)
  - [Anomaly register](#anomaly-register)
  - [Artifact Bundle](#artifact-bundle)
  - [Artifact Manifest](#artifact-manifest)
  - [Artifacts](#artifacts)
  - [Authoritative source](#authoritative-source)
- [B](#b-entries)
  - [Binned target relationship](#binned-target-relationship)
  - [Bundle integrity](#bundle-integrity)
- [C](#c-entries)
  - [Cardinality](#cardinality)
  - [Categorical feature](#categorical-feature)
  - [Claim](#claim)
  - [Constant predictor](#constant-predictor)
  - [Continuous feature](#continuous-feature)
  - [Correlation](#correlation)
  - [Cross-validation](#cross-validation)
- [D](#d-entries)
  - [Data dictionary](#data-dictionary)
  - [Data lineage](#data-lineage)
  - [Distribution](#distribution)
  - [Distribution shift](#distribution-shift)
  - [Duplicate row](#duplicate-row)
- [E](#e-entries)
  - [ECDF](#ecdf)
  - [EDA](#eda)
  - [Evidence status](#evidence-status)
- [F](#f-entries)
  - [Feature](#feature)
  - [Feature role](#feature-role)
  - [Findings register](#findings-register)
  - [Frozen](#frozen)
- [G](#g-entries)
  - [Gate](#gate)
- [H](#h-entries)
  - [High-cardinality feature](#high-cardinality-feature)
  - [Holdout data](#holdout-data)
- [I](#i-entries)
  - [Identifier](#identifier)
  - [Independent verification](#independent-verification)
  - [Interquartile range](#interquartile-range)
- [L](#l-entries)
  - [Leakage](#leakage)
  - [Log target view](#log-target-view)
  - [`loss`](#loss)
- [M](#m-entries)
  - [Mean Absolute Error](#mean-absolute-error)
  - [Mean-constant baseline](#mean-constant-baseline)
  - [Median-constant baseline](#median-constant-baseline)
  - [Missingness](#missingness)
  - [Model split](#model-split)
- [O](#o-entries)
  - [Observed range](#observed-range)
  - [October Recommendation Register](#october-recommendation-register)
  - [Outlier](#outlier)
- [P](#p-entries)
  - [Pearson correlation](#pearson-correlation)
  - [Prediction](#prediction)
  - [Preprocessing](#preprocessing)
- [Q](#q-entries)
  - [Quantile](#quantile)
  - [Quantile bin](#quantile-bin)
- [R](#r-entries)
  - [Rare level](#rare-level)
  - [Reproducibility](#reproducibility)
  - [Run Receipt](#run-receipt)
- [S](#s-entries)
  - [Seed](#seed)
  - [Skewness](#skewness)
  - [Source hash](#source-hash)
  - [Spearman correlation](#spearman-correlation)
  - [Support](#support)
- [T](#t-entries)
  - [Target](#target)
  - [Target encoding](#target-encoding)
  - [Training fold](#training-fold)
- [U](#u-entries)
  - [Unit of analysis](#unit-of-analysis)
  - [Univariate relationship](#univariate-relationship)
  - [Unseen level](#unseen-level)
- [V](#v-entries)
  - [Validation data](#validation-data)
- [W](#w-entries)
  - [Workflow Run](#workflow-run)
- [Usage Guide](#usage-guide)
  - [Example dialogue](#example-dialogue)
  - [How these terms relate](#how-these-terms-relate)
  - [Terminology to use consistently](#terminology-to-use-consistently)

## A entries

### Absolute error

The non-negative distance between one predicted claim amount and the observed
`loss`:

```text
absolute error = |predicted loss - observed loss|
```

Overprediction and underprediction by the same dollar amount have the same
absolute error. Absolute error remains in the original target units.

### Analysis contract

The plain-language and technical agreement that fixes what the analysis is trying
to answer. For this project it identifies the claim-level unit of analysis, the
`loss` target, field roles, MAE metric, September scope, important non-uses, and
the limits created by anonymous predictors.

The analysis contract is a project decision record, not an insurance contract.

### Anomaly register

The shared record of unexpected data or workflow conditions. Each anomaly should
include a stable ID, description, affected count, severity, owner, status,
evidence, handling decision, and likely impact. Non-blocking anomalies remain in
the register after a gate passes.

### Artifact Bundle

An **Artifact Bundle** is a complete package of related
[Artifacts](#artifacts) from one successfully completed task or group of related
tasks. It includes the files, an [Artifact Manifest](#artifact-manifest), the
evidence needed to interpret them, and the checks needed to confirm that they are
complete and usable by the next step. Partial or failed work is not an approved
Artifact Bundle.

For example, a target-profile bundle may contain the notebook or source code,
machine-readable summary table, raw and log-scale figures, findings-register
entries, Run Receipt, and independent-review record.

### Artifact Manifest

A machine-readable inventory describing an Artifact Bundle's files, versions,
schemas, settings, source relationships, and file hashes. The manifest connects
the evidence to one source file, code revision, and configuration.

### Artifacts

**Artifacts** are the work products created by the project. They may include
notebooks, source code, configuration, field-profile tables, figures, data
dictionaries, findings registers, reports, decision records, manifests, and
review notes.

A file does not need to contain code to be an Artifact. A Markdown review record
or a machine-readable CSV summary is also an Artifact.

### Authoritative source

The one approved source-data version from which a Workflow Run begins. For the
September Allstate milestone, the starting authoritative source is
`data/allstate_claims_data.csv`, identified by its path, file size, header, shape,
and SHA-256 hash.

A similarly named or newer file does not replace the authoritative source until
the team records and approves that change.

## B entries

### Binned target relationship

A summary that groups a continuous feature into recorded intervals and reports
the target distribution within each interval. The September method uses
quantile-based bins and reports support, raw mean `loss`, raw median `loss`, and
interquartile range.

Binning can reveal nonlinear patterns hidden by one correlation coefficient. A
visible pattern remains an association, not proof of causation or predictive
value in a future model.

### Bundle integrity

Confirmation that an Artifact Bundle contains every declared file and that its
hashes, schemas, source relationships, configurations, and required checks match
its Artifact Manifest.

## C entries

### Cardinality

The number of distinct observed values or levels in a field. In this project,
categorical cardinality ranges from many binary fields to `cat116`, which has 326
observed levels in the supplied data.

Cardinality does not measure feature importance. A high-cardinality feature may
still contain useful information but requires careful support and encoding plans.

### Categorical feature

One of the 116 anonymous predictors named `cat1` through `cat116`. Each observed
value is a nominal level. Letters and multi-letter codes are labels, not ordered
measurements.

The exact business meaning of each categorical feature is unknown unless the
Challenge Advisor supplies a mapping.

### Claim

One auto-insurance claim represented by one row of the supplied CSV. The row
contains an identifier, anonymous categorical and continuous claim or vehicle
characteristics, and the final paid amount in `loss`.

The anonymous dataset does not support identifying a person, reconstructing an
individual accident, or assigning a known business meaning to a particular
`cat*` or `cont*` field.

### Constant predictor

A simple prediction rule that gives every claim the same predicted amount. The
constant may be the training-target mean, median, or another value. It must be
estimated from model-training data and evaluated on separate validation data when
used as a model baseline.

### Continuous feature

One of the 14 anonymous predictors named `cont1` through `cont14`. The project
overview says these fields are scaled between 0 and 1. The original units and
transformations are not supplied.

The bounded scale does not mean the features are uniformly distributed or that
equal numeric differences have a confirmed business interpretation.

### Correlation

A numerical description of association between two variables. Correlation can
help identify linear or monotonic relationships, but it does not establish
causation, complete predictive usefulness, or redundancy under every model.

For nominal `cat*` fields, assigning integer codes and calculating ordinary
correlation creates an unsupported order and is not an approved association
method.

### Cross-validation

An evaluation method that repeats model training and validation across multiple
data partitions. Every preprocessing step that learns from data must be fitted
separately within each training fold.

Cross-validation belongs to October model development. September may document a
proposed design but does not tune or select models through it.

## D entries

### Data dictionary

The project-specific reference for every delivered and team-created field. For
each field, it records the exact name, approved role, observed type, range or
levels, unique-value count, missingness, known unit or scale, documented meaning,
quality limitations, and approved handling.

Because the predictors are anonymous, `unknown` is the correct meaning for an
unmapped `cat*` or `cont*` field. The dictionary must not replace missing source
documentation with a guess.

### Data lineage

The traceable path from the authoritative source through parsing, validation,
derivation, aggregation, and plotting to an Artifact. Data lineage identifies the
source version, configuration, Workflow Run, and output relationship needed to
explain where a result came from.

### Distribution

The pattern of values a field takes, including its center, spread, shape, common
values, and tail behavior. A histogram, ECDF, boxplot, percentiles, and summary
statistics provide different views of a distribution.

### Distribution shift

A change in feature support, feature values, target values, or their relationships
between the data used for development and a future, validation, test, or
production sample. The current repository supplies one labeled CSV, so September
cannot establish that a later sample has the same distribution.

### Duplicate row

A row whose values match another row in every column. An exact duplicate row is
different from two valid claims that share some feature values. The local source
currently contains no exact duplicate rows.

## E entries

### ECDF

An **empirical cumulative distribution function** plot. At each target value, the
ECDF shows the share of claims with `loss` at or below that value. It can display
the complete target distribution without depending on histogram bin widths.

### EDA

**Exploratory Data Analysis** is the structured examination of data quality,
field roles, distributions, level support, relationships, anomalies, and
limitations before model development.

For this milestone, EDA is not merely a gallery of plots. Every important figure
must connect to a reproducible table, an interpretation, a limitation, and a
findings-register entry when it supports a conclusion.

### Evidence status

The approved label describing how strongly an EDA statement is supported:

- **directly observed:** a reproducible fact calculated from the supplied data;
- **consistent with a pattern:** a reproducible association whose interpretation
  remains limited;
- **hypothesis:** a possible explanation or modeling idea that still requires
  confirmation or testing; and
- **inconclusive:** the available evidence does not support a firm conclusion.

These labels prevent anonymous-feature guesses and visual impressions from being
reported as established facts.

## F entries

### Feature

An input field considered for understanding or future prediction. The supplied
predictor fields are the 116 `cat*` and 14 `cont*` columns. `id` is an identifier,
and `loss` is the target, so neither is an ordinary predictor feature.

### Feature role

The approved purpose of a field in the workflow. September roles are:

- identifier;
- anonymous categorical predictor;
- anonymous continuous predictor;
- target; and
- derived EDA field.

A field has one recorded primary role for a given analysis version. A role may be
revised only through a documented new version and review.

### Findings register

The versioned record of the team's EDA conclusions. Each finding includes a stable
ID, concise title, evidence link, observed result, interpretation, evidence
status, limitation or alternative explanation, possible October implication,
owner, and independent reviewer.

The register separates what the data shows from what the team may choose to test
during modeling.

### Frozen

Locked to one identified version for dependent work. A frozen source, method,
threshold, binning rule, or Artifact may change only through a recorded new
version, impact assessment, and repeated approval of any affected gate.

“Frozen” does not mean permanently correct or impossible to revise.

## G entries

### Gate

A **Gate** is a group of blocking readiness conditions that must be completed and
reviewed before dependent work begins. A gate passes only after its evidence is
prepared, independently checked, discussed by the team, and explicitly approved.

For example, producing a correlation heatmap does not pass Gate 3 if the source
profile, support tables, interpretation, limitations, or independent review are
missing.

## H entries

### High-cardinality feature

A categorical feature with many observed levels relative to other fields or the
available support. The milestone does not impose one universal cutoff, but
`cat116`, `cat110`, and `cat109` require explicit high-cardinality review.

High cardinality is a data characteristic, not an automatic reason to remove a
feature.

### Holdout data

Data kept separate from development so it can provide less-biased evaluation.
The current repository does not supply a separate holdout file. A future holdout,
test, or later-period sample must be profiled for distribution and category
coverage before the team assumes historical findings apply unchanged.

## I entries

### Identifier

The `id` field that uniquely labels a claim row. It is used for integrity checks,
joining, tracing, and reproducibility. It is not a measured claim characteristic
and should not be treated as an ordinary model feature.

### Independent verification

A check performed by someone who did not produce the critical Artifact being
reviewed. The verifier follows the recorded rules, recalculates or reproduces key
evidence, and records agreements, discrepancies, and limitations.

Reading the author's conclusion without checking its evidence is not independent
verification.

### Interquartile range

The distance from the 25th percentile to the 75th percentile. It describes the
spread of the middle half of observed values and is less affected by a long right
tail than the full range or standard deviation.

## L entries

### Leakage

Information from validation or test data, or information derived from the target,
improperly influencing a preprocessing step, feature, model, threshold, or
development decision.

Allstate examples include fitting a category encoder on the complete dataset,
using validation `loss` values to create target encodings, or repeatedly changing
feature rules because validation MAE improves.

### Log target view

A transformed visualization of the positive target, usually created as
`log1p(loss)`. It compresses the long right tail so the bulk of claims and
level-wise differences are easier to see.

A log target view does not change the project metric. Future MAE must be computed
after predictions are returned to original `loss` units.

### `loss`

The positive continuous target representing the final paid amount for a claim.
The project aims to predict this amount, and future MAE is reported in the same
original units.

The supplied `loss` distribution has a long right tail. Large valid values should
not be discarded merely because they are uncommon.

## M entries

### Mean Absolute Error

**Mean Absolute Error (MAE)** is the average absolute error across evaluated
claims:

```text
MAE = mean(|predicted loss - observed loss|)
```

Lower MAE is better. MAE must name the evaluated data partition and remain in
original `loss` units. A transformed-scale error is not the project's MAE.

### Mean-constant baseline

A constant predictor that assigns every validation claim the mean `loss` from the
corresponding training data. The Challenge Project Overview asks the team to use
this as a baseline starting value.

The mean must not be calculated from validation targets. A full-data descriptive
calculation is a data check, not held-out model performance.

### Median-constant baseline

A constant predictor that assigns every validation claim the median `loss` from
the corresponding training data. The median is the constant that minimizes total
absolute error, so it is a useful comparator under MAE.

The project should retain the requested mean baseline and may report the median
baseline alongside it with this explanation.

### Missingness

The absence of a usable recorded value. The local source currently contains no
missing cells, but the workflow must still verify missingness rather than assume
it from the project description.

Zero is not missing for a scaled `cont*` field. An uncommon category label is not
missing merely because it has low support.

### Model split

The fixed division of eligible claims into model-training, validation, and, when
available, test partitions. The split belongs to October model development.

Any randomized split must record its method and seed. All target-dependent and
fitted preprocessing must learn only from the model-training portion.

## O entries

### Observed range

The minimum and maximum values present in the supplied data. An observed range is
not automatically the complete set of values possible in future data.

For example, the September file verifies that all `cont*` values fall between 0
and 1, but a future data contract should still state how out-of-range values would
be handled.

### October Recommendation Register

The October Recommendation Register records evidence-supported possibilities for
the next phase. It does not itself select, schedule, or implement October work.
Give each recommendation a stable ID such as `REC-001` and include every field
below.

| Field | Required content |
| --- | --- |
| ID | Stable recommendation identity |
| Concise action | A testable possible next step, not a vague aspiration |
| Affected workflow | Split, baseline, preprocessing, feature handling, model, evaluation, or interpretation |
| Evidence | Exact links to supporting September Artifacts, anomalies, and findings |
| Hypothesis | Why the proposed action may address the evidence |
| Proposed experiment or change | What a future planning session could choose to test |
| Expected benefit | The improvement or learning reasonably supported by the evidence |
| Tradeoffs | Complexity, interpretability, processing cost, risk, or lost comparability |
| Acceptance criterion | The observable future result needed to accept the change |
| Future evaluation need | The untouched validation design needed to test it |
| Dependencies | Required Artifacts, interfaces, permissions, or earlier decisions |
| Rough effort | A planning estimate, not a commitment |
| Suggested owner profile | Helpful starting skills, not a named person |
| Priority | `now`, `next`, `later`, or `not recommended` |
| Reopened Gate | Gate 1, 2, or 3 if adopting it changes frozen September evidence |

Use this template for each recommendation:

```markdown
## REC-000 — <concise possible action>

- Priority: now | next | later | not recommended
- Affected workflow:
- Evidence links:
- Hypothesis:
- Proposed experiment or change:
- Expected benefit:
- Tradeoffs and limitations:
- Acceptance criterion:
- Future validation/evaluation needed:
- Dependencies:
- Rough effort:
- Suggested owner profile:
- Gate reopened if adopted:
```

### Outlier

An observation that is unusually far from most other observations under a stated
rule. “Outlier” describes a statistical position; it does not establish that the
value is an error.

For this project, valid high-loss claims are central to claim severity. Investigate
suspected errors through the anomaly register, but do not remove large claims
solely to make a distribution or model easier to handle.

## P entries

### Pearson correlation

A coefficient describing linear association between two numeric variables. It
ranges from -1 to 1. Values near zero indicate weak linear association, but they
may coexist with nonlinear, interaction, or conditional relationships.

Pearson correlation is appropriate for examining the numeric `cont*` fields; it
is not appropriate for arbitrary integer codes assigned to nominal `cat*` levels.

### Prediction

An estimated final paid claim amount produced without seeing that claim's target.
For evaluation, one prediction must connect to exactly one observed `loss` through
the stable claim identifier.

### Preprocessing

The transformation of source fields into analysis or model inputs. It may include
type conversion, category encoding, imputation, scaling, rare-level handling, and
feature construction.

Any preprocessing step that learns frequencies, categories, target relationships,
or numeric parameters must be fitted on model-training data only and then applied
unchanged to validation or test data.

## Q entries

### Quantile

A value below which a stated share of observations falls. The median is the 50th
percentile. Quantiles are useful for describing the long-tailed `loss`
distribution without allowing a few large claims to determine every summary.

### Quantile bin

A group formed by dividing observations according to ranked feature values so the
groups contain approximately equal numbers of rows. Repeated values may make
fewer distinct bins possible than requested; the workflow must record the actual
boundaries and bin count.

## R entries

### Rare level

A categorical level whose support falls below a threshold declared and frozen by
the team. The threshold must state its unit and rationale.

Rare-level status supports readable EDA and future encoding plans. It is not an
automatic instruction to delete the level, merge it into another level, or remove
the feature.

### Reproducibility

The ability to regenerate required outputs from the same identified source, code,
configuration, environment, and rules. Discrete items such as the schema, field
roles, support counts, bin assignments, and figure inputs should match exactly.
Displayed numeric summaries should match within their recorded rounding precision.

### Run Receipt

The attempt-specific record of who ran a workflow or step, when and where it ran,
which source, code, configuration, and software versions it used, what happened,
and where its logs and outputs can be found.

## S entries

### Seed

A recorded starting value used to make an otherwise randomized operation
repeatable. A seed helps reproduce sampling, plotting subsamples, model splits,
and future cross-validation. It does not make a flawed evaluation design valid.

### Skewness

A numerical description of distribution asymmetry. Positive skewness indicates a
longer right tail. The local raw `loss` distribution has strong positive skew,
which is why raw and log-scale views are both required.

### Source hash

A cryptographic fingerprint calculated from a file's exact bytes. Matching hashes
help confirm that two Workflow Runs used the same file. A hash does not establish
that the file is correctly documented or that the analysis is valid.

The approved September source hash uses SHA-256.

### Spearman correlation

A rank-based coefficient describing monotonic association between two variables.
It can capture steadily increasing or decreasing relationships that are not
linear, but it still does not reveal every nonlinear pattern or establish
causation.

### Support

The number of usable observations behind a category level, bin, statistic, or
comparison. Support must name its unit and denominator. In this project, support
normally means claims unless a table explicitly defines another unit.

Large total support does not guarantee adequate support for every rare level or
extreme target region.

## T entries

### Target

The outcome a future model will estimate. For this project the target is `loss`,
the final paid claim amount. The target is not an input feature.

### Target encoding

A category transformation that uses training-target values to assign numeric
representations to category levels. It can be useful for high-cardinality fields
but is highly vulnerable to leakage and overfitting.

Target encoding is not part of the September EDA. If tested in October, it must be
cross-fitted inside training folds and must define handling for rare and unseen
levels.

### Training fold

The portion of data used to fit a model and every learned preprocessing step
during one evaluation iteration. Means, medians, category vocabularies, target
encodings, scaling parameters, and feature selection must be learned within the
training fold.

## U entries

### Unit of analysis

What one analytical observation represents. In this project, the unit is one
auto-insurance claim represented by one row. A claim, CSV row, category level,
continuous bin, and dollar of `loss` are not interchangeable units.

### Univariate relationship

The observed relationship between one predictor and the target, examined without
holding other predictors constant. Examples include `loss` summaries by one
categorical level or by bins of one continuous feature.

A univariate relationship can reveal useful patterns, but it may change when
other features, interactions, or later data are considered.

### Unseen level

A categorical value that appears in validation, test, or future data but did not
appear in the corresponding model-training data. October preprocessing must
define how unseen levels are represented without using validation or test targets.

## V entries

### Validation data

Data used to estimate how well a model or decision generalizes beyond the records
used to fit it. Validation data may be used for approved comparison and selection,
but it must not influence training features, preprocessing parameters, or target
encodings.

The current September file has not yet been divided into modeling partitions;
that split is an October task under the Challenge Project Overview.

## W entries

### Workflow Run

One recorded execution of an ordered set of project steps using identified source
data, code, configuration, software versions, and settings. A Workflow Run may
succeed, fail, or complete with anomalies; only a successful, verified run may
support an approved Artifact Bundle.

## Usage Guide

### Example dialogue

> **Fellow:** “`cont2` has the largest Pearson correlation with `loss`, so it is
> the most important feature and we should drop the others.”
>
> **Reviewer:** “The finding is directly observed only as a weak marginal linear
> association. What do the binned target summaries show? Are there nonlinear
> patterns, interactions, or correlated predictors? Feature importance and
> removal require held-out October evidence.”
>
> **Fellow:** “I will record the correlation, its limitation, the supporting plot,
> and the October experiment in the findings and recommendation registers.”

### How these terms relate

1. The **authoritative source** and its **source hash** establish which data one
   **Workflow Run** used.
1. The **analysis contract**, **unit of analysis**, **feature roles**, and **data
   dictionary** establish what each row and field means—and what remains unknown.
1. **EDA** produces field profiles, target distributions, support tables, binned
   target relationships, correlations, and an **anomaly register**.
1. The **findings register** connects those Artifacts to interpretations,
   limitations, evidence status, and possible October implications.
1. A **Run Receipt**, **Artifact Manifest**, and **independent verification**
   establish **Bundle integrity**.
1. A **Gate** passes only when the complete Artifact Bundle supports the readiness
   decision.
1. Gate 4 supports the **October Recommendation Register**, model-split plan,
   preprocessing safeguards, and mean- and median-constant baselines.

### Terminology to use consistently

- Say **claim** or **row** according to the actual unit; do not call an anonymous
  row a policyholder, customer, accident, or vehicle.
- Say **identifier** for `id`, **categorical feature** for `cat*`, **continuous
  feature** for `cont*`, and **target** for `loss`.
- Say **level** for a categorical value and **support** for the number of claims
  behind a level or bin.
- Say **directly observed**, **consistent with a pattern**, **hypothesis**, or
  **inconclusive** according to the available evidence.
- Say **association** or **relationship**, not **effect** or **cause**, unless a
  separate causal design supports the stronger claim.
- Say **log target view**, not **new target**, when `log1p(loss)` is used only for
  visualization.
- Say **high-loss claim** or **upper-tail claim**, not **bad outlier**, unless a
  documented validity check confirms an error.
- Say **weak marginal linear relationship**, not **useless feature**, when Pearson
  correlation is near zero.
- Say **correlated predictors** or **potential redundancy**, not **duplicate
  features**, unless the columns are actually identical.
- Name every metric's data partition, target scale, unit, denominator, and support.
