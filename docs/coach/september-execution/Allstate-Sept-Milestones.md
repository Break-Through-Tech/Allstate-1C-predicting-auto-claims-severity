# Allstate Sept Milestones

This guide is meant to be used as a suggestion for the September milestone for
the Allstate project.

**September Milestone:**

Data Understanding -> Explore dataset, correlation, plots, document findings

## Gate Handoffs

The Allstate project has 4 [**Gates**](./Glossary.md#gate).

1. **Gate 1:** Data Ready
1. **Gate 2:** EDA Scope and Methods Frozen
1. **Gate 3:** Data Understanding Reviewed
1. **Gate 4:** September Complete

In practice, each **Gate Handoff** should work as follows:

1. **Evidence owner prepares:** every checklist item links to an exact committed
   [Artifact](./Glossary.md#artifacts) or verified
   [Artifact Bundle ID](./Glossary.md#artifact-bundle).
1. **Independent teammate verifies:** someone who did not produce the critical
   Artifact reproduces or independently checks the key result.
1. **Team Readiness Review:** the owner demonstrates the evidence; the team
   records limitations, anomalies, open disagreements, and dissent.
1. **Board updates:** dependent items become ready only after the gate decision is
   recorded.

### Artifacts

When completing tasks, the team will produce
[Artifacts](./Glossary.md#artifacts). Keep the working notebook and generated
evidence in the team's shared Google Colab space so every fellow, the coach, and
the Challenge Advisor can access them. Commit the reproducible notebook or source
code, configuration, approved tables and figures, reports, and decision records
to the repository. Use [Artifact Bundles](./Glossary.md#artifact-bundle) to make
asynchronous handoffs easier.

### September Scope Protections

- Use [`data/allstate_claims_data.csv`](../../../data/allstate_claims_data.csv) as
  the single September source unless the Challenge Advisor approves a replacement
  or additional dataset.
- Treat one row as one anonymized auto-insurance claim and `loss` as that claim's
  total paid amount. Do not invent policyholder, vehicle, accident, or coverage
  details that the anonymous fields do not provide.
- Keep `id` as an [identifier](./Glossary.md#identifier), not an ordinary model
  feature or business measurement.
- Treat every `cat*` field as nominal. Alphabetical or integer codes do not create
  a meaningful order.
- Use `log1p(loss)` to make plots readable when helpful, but keep business
  summaries and future MAE evaluation in the original `loss` units.
- Do not delete valid large claims merely because they look like outliers. High
  claim severity is part of the phenomenon the project must understand.
- Do not drop a predictor because it has weak marginal correlation or is highly
  correlated with another predictor. Record the observation and defer feature
  removal to validated October experiments.
- Do not begin model comparison, hyperparameter tuning, target encoding, feature
  selection, SHAP analysis, or dashboard development before Gate 4 is approved.
- Do not describe an association as causal or claim that an anonymous feature has
  a specific business meaning without confirmation from the Challenge Advisor.

## Gate 1 - Data Ready

### Source identity and access

- [ ] Load the project overview, EDA research, source CSV, and shared project
  materials into the team's Google Colab space.
- [ ] Confirm that every fellow, the coach, and the Challenge Advisor can access
  the working notebook, project materials, and approved Artifacts.
- [ ] Record the [authoritative source](./Glossary.md#authoritative-source) as
  `data/allstate_claims_data.csv`.
- [ ] Confirm and record the source identity:
  - file size: `70,025,339` bytes;
  - 188,318 data rows; and
  - 132 columns.
- [ ] If the source hash, size, shape, or header does not match, stop and record an
  anomaly before continuing. Do not silently substitute a different file.

### Schema and integrity

- [ ] Confirm that the header contains, in order:
  - `id`;
  - `cat1` through `cat116`;
  - `cont1` through `cont14`; and
  - `loss`.
- [ ] Confirm the exact column roles:
  - 1 identifier;
  - 116 categorical predictors;
  - 14 continuous predictors; and
  - 1 regression target.
- [ ] Confirm that `id` is present, non-missing, and unique for all 188,318 rows.
- [ ] Confirm that the table contains 0 exact duplicate rows and 0 missing cells.
- [ ] Confirm that all `cont*` fields are numeric and every observed value is
  within the documented 0-to-1 scale.
- [ ] Confirm that `loss` is numeric, finite, and strictly positive. Record any
  violation rather than deleting it automatically.
- [ ] Confirm that every `cat*` value is read as a category label without imposing
  numeric or alphabetical order.
- [ ] Record observed data types, unique-value counts, ranges, and missingness for
  all 132 fields in a machine-readable profile.
- [ ] Create an [anomaly register](./Glossary.md#anomaly-register). Resolve every
  blocking source, parsing, schema, and integrity anomaly. For each non-blocking
  anomaly, record its severity, owner, status, evidence, handling decision, and
  likely impact.
- [ ] Generate every calculated table and figure from the recorded source and
  configuration. Do not hand-edit calculated values in the report.
- [ ] Complete one clean [Workflow Run](./Glossary.md#workflow-run) that reproduces
  the source profile and machine-readable evidence.
- [ ] Have someone other than the workflow author independently verify:
  - the source identity;
  - row and column counts;
  - header and column-role counts;
  - identifier uniqueness;
  - missingness and duplicate totals;
  - continuous ranges; and
  - Artifact Bundle integrity.

## Gate 2 - EDA Scope and Methods Frozen

### Plain-language analysis contract

- [ ] Write a plain-language statement that the project aims to estimate a
  claim's final paid amount early enough to support reserve planning and a better
  understanding of factors associated with higher claim severity.
- [ ] Define the [unit of analysis](./Glossary.md#unit-of-analysis) as one auto
  insurance claim represented by one row.
- [ ] Define `loss` as the regression target and original `loss` units as the
  reporting and future evaluation scale.
- [ ] Record MAE as the project success metric and explain absolute error in plain
  language.
- [ ] State that closed claims without payment are excluded according to the
  project overview; verify only that the delivered file contains positive `loss`
  values rather than inferring why any individual value is present.
- [ ] State that the meanings of individual `cat*` and `cont*` fields are unknown.
  The examples in the project overview are possible field types, not a mapping.
- [ ] Record the intended non-uses: September EDA does not establish causation,
  determine an individual reserve, prove production readiness, or authorize
  automated claims decisions.

### Project-specific data dictionary

- [ ] Create one shared, versioned [data dictionary](./Glossary.md#data-dictionary)
  covering all 132 delivered fields and every team-created field.
- [ ] For every source field, record:
  - exact source name;
  - approved role;
  - observed data type;
  - observed range or category levels;
  - unique-value count;
  - missing count and percentage;
  - known unit or scale;
  - documented meaning or `unknown`;
  - known quality limitation; and
  - approved September handling.
- [ ] Mark `id` as an identifier excluded from distribution and target-effect
  interpretation except for integrity checks.
- [ ] Mark every `cat*` field as an anonymous nominal categorical predictor.
- [ ] Mark every `cont*` field as an anonymous continuous predictor scaled between
  0 and 1; do not claim the original unit or transformation is known.
- [ ] Mark `loss` as the positive continuous target representing total paid claim
  amount.
- [ ] For every derived field, record its stable name, purpose, inputs, exact
  derivation, allowed values, version, and owner. This includes `log1p_loss`,
  quantile-bin labels, and any support flags.
- [ ] Mark disputed or undocumented meanings as unresolved. Do not replace an
  unknown meaning with the team's guess.

### Target-analysis method

- [ ] Freeze one target summary that includes count, mean, median, standard
  deviation, minimum, maximum, skewness, and at least the 25th, 50th, 75th, 90th,
  95th, and 99th percentiles.
- [ ] Freeze the required target views:
  - raw `loss` histogram;
  - `log1p(loss)` histogram;
  - raw `loss` boxplot or ECDF; and
  - a compact percentile table in original units.
- [ ] Record plot binning, axis, clipping, and sampling settings. A visual axis may
  be limited for readability only if the full distribution and excluded share
  remain reported.
- [ ] Confirm that `log1p(loss)` is a visualization field, not a replacement for
  the original target or future MAE calculation.

### Categorical-analysis method

- [ ] Freeze an inventory for all 116 `cat*` fields that reports:
  - cardinality;
  - most- and least-common level support;
  - most-common level share;
  - minimum and median level support; and
  - the number of levels below the team's declared
    [rare-level threshold](./Glossary.md#rare-level).
- [ ] Record the rare-level threshold and rationale before interpreting
  high-cardinality plots. The threshold is an EDA display and support rule, not an
  automatic instruction to remove data.
- [ ] Freeze level-to-target tables containing, at minimum, level support, raw
  mean `loss`, raw median `loss`, and interquartile range.
- [ ] For low-cardinality fields, use readable box, violin, or point plots of
  `log1p(loss)` together with raw-unit summary tables.
- [ ] For high-cardinality fields, use ordered point or table views for adequately
  supported levels and summarize the rare tail separately. Do not create an
  unreadable plot containing hundreds of labels.
- [ ] Confirm that no categorical association is calculated from arbitrary
  alphabetic-to-integer codes.

### Continuous-analysis method

- [ ] Freeze an inventory for all 14 `cont*` fields that reports distribution
  summaries, observed range, and unique-value count.
- [ ] Produce a histogram or density view and a boxplot for every continuous
  field.
- [ ] Calculate Pearson and Spearman correlations of every `cont*` field with raw
  `loss` and `log1p(loss)`. Treat each coefficient as a marginal association, not
  a feature-importance score.
- [ ] Quantile-bin each continuous field using a recorded default of 10 bins.
  When repeated values prevent 10 distinct bins, record the actual bin count
  rather than forcing artificial boundaries.
- [ ] For every continuous bin, report support, raw mean `loss`, raw median
  `loss`, and interquartile range. Plot support together with the mean and median
  target pattern.
- [ ] Produce one annotated Pearson correlation heatmap for the 14 continuous
  predictors and a table of the strongest absolute predictor-predictor pairs.
- [ ] Confirm that no feature will be removed during September solely because of
  weak target correlation or strong predictor-predictor correlation.

### Findings and review method

- [ ] Create a versioned [findings register](./Glossary.md#findings-register).
  Each entry must record:
  - stable finding ID and concise title;
  - exact evidence or plot link;
  - observed result;
  - interpretation;
  - evidence status;
  - limitation or alternative explanation;
  - possible October implication; and
  - owner and reviewer.
- [ ] Use the evidence-status terms **directly observed**, **consistent with a
  pattern**, **hypothesis**, and **inconclusive** as defined in the glossary.
- [ ] Have the team approve the data dictionary, target views, rare-level rule,
  continuous-bin rule, correlation methods, and findings-register format before
  Gate 3 conclusions are finalized.
- [ ] Record who performed the independent review, disagreements, limitations,
  and the exact Artifact versions used to pass Gate 2.

## Gate 3 - Data Understanding Reviewed

### Data-quality evidence

- [ ] Reproduce the Gate 1 source profile from the frozen source and configuration.
- [ ] Report the exact row count, column count, feature-role counts, identifier
  uniqueness, missingness, duplicate total, and observed numeric ranges.
- [ ] Confirm that a clean dataset reduces repair work but does not remove the
  need to study level support, distributions, and target relationships.
- [ ] Resolve every blocking EDA or workflow anomaly. For each non-blocking
  anomaly, preserve the affected count, severity, owner, handling rule, and likely
  impact.

### Target-distribution evidence

- [ ] Reproduce and explain these local verification values, allowing only normal
  rounding differences:
  - mean `loss`: 3,037.34;
  - median `loss`: 2,115.57;
  - 95th percentile: 8,508.54;
  - maximum: 121,012.25; and
  - raw skewness: 3.795.
- [ ] Explain the long right tail in plain language and show how the raw and
  transformed views answer different questions.
- [ ] Report high-loss observations as part of the severity distribution. If any
  value is suspected to be invalid, place it in the anomaly register and preserve
  the original row until the issue is resolved.
- [ ] Keep every headline business statistic in original `loss` units even when a
  transformed plot is used.

### Categorical evidence

- [ ] Confirm the cardinality and support inventory covers all 116 categorical
  fields.
- [ ] Reproduce these starting checks:
  - 72 categorical fields have 2 observed levels;
  - 88 have at most 4 observed levels;
  - `cat116` has 326 levels;
  - `cat110` has 131 levels; and
  - `cat109` has 84 levels.
- [ ] Identify fields and levels with low support, dominant levels, or unusually
  uneven target distributions. State the denominator and support for every
  comparison.
- [ ] Review the high-cardinality fields without assuming they are unusable or
  deleting rare levels during EDA.
- [ ] Confirm that every categorical target comparison includes support and raw
  target summaries, not only a transformed plot.

### Continuous evidence

- [ ] Confirm the distribution inventory and binned target summaries cover all 14
  continuous fields.
- [ ] Reproduce the strongest absolute raw Pearson relationships with `loss`:
  - `cont2`: approximately 0.142;
  - `cont7`: approximately 0.120; and
  - `cont3`: approximately 0.111.
- [ ] Explain that no continuous predictor has a strong linear marginal
  relationship with raw `loss` and that this does not establish low predictive
  value.
- [ ] Use the binned mean, median, spread, and support to identify nonlinear or
  uncertain univariate patterns that one correlation coefficient can hide.
- [ ] Reproduce and explain the strongest continuous-feature correlations:
  - `cont11`-`cont12`: approximately 0.994;
  - `cont1`-`cont9`: approximately 0.930; and
  - `cont6`-`cont10`: approximately 0.883.
- [ ] Record the implications of correlated predictors for later linear-model
  interpretation without removing a field before held-out MAE testing.

### Findings and limitations

- [ ] The findings register must address, at minimum:
  - the complete, row-unique table and light cleaning burden;
  - the long right tail of `loss`;
  - the mixture of many low-cardinality and a few high-cardinality categorical
    fields;
  - weak marginal linear continuous-to-target relationships;
  - nonlinear patterns visible in binned target views;
  - strong redundancy among selected continuous predictors; and
  - the limits created by anonymous feature meanings and the absence of a
    separate test or future-period dataset.
- [ ] Distinguish what the data directly shows from what might be useful to test
  during modeling.
- [ ] Have someone other than the EDA author independently recalculate:
  - the target summary;
  - categorical cardinalities for a representative set including `cat116`;
  - continuous-to-target correlations;
  - the three strongest continuous-feature pairs; and
  - at least three headline findings from their underlying evidence.

### Reproducibility and October-readiness evidence

- [ ] From a clean committed project version in Google Colab, rerun the September
  workflow through the final EDA tables, figures, and findings register.
- [ ] Confirm that the clean run reproduces all discrete results exactly and all
  displayed numerical results within the recorded rounding precision.
- [ ] Record the source hash, code revision, dependency versions, notebook/runtime
  version, random seeds, plot settings, bin rules, support threshold, Workflow Run
  ID, and Artifact Bundle IDs.
- [ ] Draft, but do not tune against, an October evaluation plan that keeps
  preprocessing inside training data and computes MAE on untouched validation
  data in original `loss` units.
- [ ] State that October must include the Challenge Advisor's requested
  mean-constant baseline. Also propose a median-constant comparator because the
  median minimizes absolute error for a constant prediction.
- [ ] Do not present the full-data descriptive constant MAE as held-out model
  performance. October baselines must be fitted on training partitions only.
- [ ] Record how future categorical encoders will handle rare and previously
  unseen levels without learning from validation data.
- [ ] Record the team's approval, disagreements, limitations, exact Workflow Run,
  and Artifact Bundle IDs used to pass Gate 3.

## Gate 4 - September Complete

### Completion and independent review

**Completion rule:** If the source identity, schema, target meaning, anonymous
feature handling, EDA methods, or a blocking anomaly remains unresolved at the end
of September, keep Gate 4 open and record the blocker. Do not weaken a check,
delete inconvenient observations, or invent a field meaning only to meet the
calendar date.

- [ ] Confirm that the final September Artifact Bundle contains:
  - source identity and manifest;
  - plain-language analysis contract;
  - project-specific data dictionary;
  - anomaly register;
  - reproducible EDA notebook or source code;
  - machine-readable data-quality and field-profile tables;
  - target-distribution tables and figures;
  - categorical cardinality, support, and target-effect evidence;
  - continuous distribution, binned-target, and correlation evidence;
  - findings register;
  - independent-review records; and
  - instructions for reproducing the September workflow.
- [ ] Have someone other than the primary workflow author run or verify the final
  Artifact Bundle from the locked source and configuration.
- [ ] Confirm that every final count, table, figure, and finding traces to the same
  approved source, code, and configuration versions.
- [ ] Resolve every confirmed data-processing or workflow defect before completing
  the gate. If a correction changes a headline value or finding, record the
  reason, affected Artifact versions, corrected run, and independent recheck.

### Handoff and communication

- [ ] Prepare a plain-language September report explaining:
  - what one row and each field family represents;
  - what the target represents and why its distribution matters;
  - the most important data-quality findings;
  - categorical cardinality and support patterns;
  - continuous distributions, target relationships, and redundancy;
  - what remains unknown because the predictors are anonymous;
  - what was deferred to October; and
  - what the evidence does not justify.
- [ ] Explain the important limitations, including:
  - the field meanings are anonymous;
  - marginal association does not establish causation or complete predictive
    usefulness;
  - large claims are sparse but economically meaningful;
  - this single labeled file cannot establish future distribution stability;
  - transformed target plots are not evaluation results; and
  - September findings do not establish production readiness or an appropriate
    reserve for an individual claim.
- [ ] Create an
  [October Recommendation Register](./Glossary.md#october-recommendation-register).
  Link every recommendation to exact September evidence and label it as a future
  decision or experiment rather than completed work.
- [ ] Prepare the October modeling handoff without selecting a winning model. It
  must identify:
  - the frozen source and field-role versions;
  - the original-scale target and MAE metric;
  - the proposed split or cross-validation design and seed;
  - the mean- and median-constant baseline plan;
  - leakage-safe categorical encoding and preprocessing boundaries;
  - high-cardinality and unseen-level handling questions;
  - correlated-feature interpretation concerns;
  - candidate model families from the project overview;
  - required validation evidence; and
  - unresolved questions for the Challenge Advisor.
- [ ] Preserve the approved Artifact Bundle IDs, manifests, Workflow Run receipts,
  source and configuration hashes, anomaly register, decisions, deviations, and
  reproduction instructions in the team's shared Google Colab space and
  repository as appropriate.
- [ ] Present the handoff to the full team. Record approvals, dissent, unresolved
  risks, and work explicitly deferred to October.
- [ ] In the team retrospective, record:
  - one practice to keep;
  - one practice to change;
  - one experiment to try; and
  - one lesson about interpreting anonymous insurance-claim data responsibly.
- [ ] Do not create speculative October implementation tickets before the handoff
  is approved. Begin October planning from the approved handoff and its evidence.
