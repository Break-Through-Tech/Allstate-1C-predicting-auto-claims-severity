# Experiment Record Template

Copy this block for every run, including baselines, failed runs, and negative results. Keep records in the experiment register in run order and never overwrite an earlier record; a rerun gets a new ID.

**MAE is always reported in original `loss` units on a named partition.** Training or transformed-scale scores are labeled as such and never presented as held-out performance. The sealed test partition is never scored in October.

```markdown
### EXP-YYYYMMDD-NN — <short name>

**Owner:** <name> · **Date:** <YYYY-MM-DD> · **Status:** planned | completed | failed | abandoned
**Type:** baseline | candidate | iteration | optional feature experiment (if time permits)
**Compared against:** <experiment IDs, always including the mean baseline and median comparator>

#### Plan (fill in before running)
- **Hypothesis:** <what you expect and why, in one or two sentences>
- **Changed variable:** <the one thing that differs from the compared run, or "first run">
- **Planned comparison:** <metric, partition, and what result would count as better or worse>

#### Setup
- **Partition manifest:** october-split-v1 · manifest SHA-256 <first 12 chars>
- **Fit on:** training partition (141,238 claims) · **CV:** <folds, seed, or "none">
- **Scored on:** validation partition (28,248 claims) · **Test partition used:** no
- **Feature set:** all 130 source predictors | <list of changes>; `id` and `loss` excluded
- **Preprocessing:** <categorical encoding, rare threshold k, unseen handling, scaling>
- **Target handling:** raw `loss` | <transform> with inverse rule <...>
- **Model and settings:** <library, model, final hyperparameters, tuning search space>
- **Random seed(s):** <...>
- **Code version:** <commit SHA> · **Environment:** <Python, library versions>

#### Run receipt
- **Workflow Run ID:** <...> · **Runtime:** <minutes> · **Peak memory:** <if known>
- **Prediction check:** one finite prediction per validation claim, aligned by `id` (yes/no)

#### Results
| Partition | Claims | MAE (loss units) | vs mean baseline | vs median comparator |
| :--- | ---: | ---: | ---: | ---: |
| Training CV (mean ± sd across folds) | | | | |
| Validation | 28,248 | | | |

#### Interpretation and next decision
- **What happened:** <did the result support the hypothesis?>
- **Issues:** <failures, warnings, instability, overfitting signs>
- **Next decision:** iterate (<what>) | stop | defer (<why>)
- **Reviewed by:** <name, date>
```