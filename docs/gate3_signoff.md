### Gate 3 Independent Verification Sign-Off — Data Understanding Reviewed

**Status:** DRAFT — complete the items marked ☐ before the Team Readiness Review.
**Verification Date:** 2026-10-02

#### Exact versions used to pass Gate 3

| Item | Value |
| :--- | :--- |
| Workflow Run ID | `WR-SEPT-G3-20261002T205412Z-03140d1` |
| Code revision | `03140d1e665bdb331bccad20cc7a93d1fbe0148a` |
| Source | `data/allstate_claims_data.csv` · SHA-256 `74037cb248a1064e4d578692a4f4e5d8492ed1b2033daf643496e1b68b14ae03` · 70,025,339 bytes · 188,318 × 132 |
| Artifact Bundle IDs | `G3-SRC-60f8dc926e8c` · `G3-CAT-c627f0cac9e6` · `G3-CONT-7fb198440d14` · `G3-FND-f6c55391d79c` · `G3-CODE-ec8db22eb6a4` |
| Note | Recorded after merge (anomaly G4-WF-010). This official run is on commit `03140d1`, which also contains the Gate 4 additions; it reproduced every Gate 3 artifact exactly. The dictionary is v1.1.0 here (derived fields added; source-field rows unchanged). |
| Findings register | `docs/findings_register.md` v2.0.0 |
| Dependencies | Pinned in `requirements.txt` and enforced by the notebook setup cell: pandas 2.3.2, numpy 2.3.3, scipy 1.18.1, matplotlib 3.11.2, seaborn 0.13.2 |
| Frozen settings | Recorded in the receipt (`T4_CONFIG`): rare-level threshold <100 claims; low/high cardinality ≤10/>10 levels; 10 quantile bins with duplicates dropped (actual: `cont2` 9, `cont5` 8); target plots 50 bins, no clipping, no sampling; bootstrap seed 42 (only randomized step) |

#### Task 4 checklist

- [x] **Findings register** covers every required topic: complete, row-unique table (FND-005); long right tail (FND-006); low/high-cardinality mixture (FND-004); weak marginal linear relationships (FND-007); nonlinear binned patterns (FND-008); continuous redundancy (FND-001); anonymous features and no separate test/future data (FND-009).
- [x] **Observed vs. to-test** kept separate: findings table vs. modeling hypotheses HYP-001–HYP-004.
- [x] **No hand-edited values:** all 45 numbers quoted in the register are recalculated and checked by the notebook on every run.
- [ ] **Independent recalculation** (Gate 3 Task 4 reviewer section of `notebooks/data-understanding.ipynb`, csv + numpy path, no pandas) by someone other than each item's author. See the review matrix below.
- [x] **Clean Workflow Run** from a committed version, reproducing all discrete results exactly and all numeric results within recorded precision. See *Setup and Installation* in `README.md`.
- [x] **Recorded:** source hash, code revision, dependency versions, runtime, random seeds, plot settings, bin rules, support threshold, Workflow Run ID, and Artifact Bundle IDs (in the Workflow Run receipt).
- [ ] **Team approval, disagreements, and limitations** recorded below.

#### Independent review matrix

A reviewer may not check evidence they authored (enforced in the reviewer cell).

| Item | Evidence author(s) | Eligible reviewers | Reviewer | Result |
| :--- | :--- | :--- | :--- | :--- |
| Target summary | Leng Lim | Krish, Hector Baeza, Rachel Cheung | ☐ | ☐ |
| Categorical cardinalities (incl. `cat116`) | Krish | Leng Lim, Hector Baeza, Rachel Cheung | ☐ | ☐ |
| Continuous-to-target correlations | Hector Baeza, Task 4 owner | anyone else | ☐ | ☐ |
| Three strongest continuous pairs | Hector Baeza, Task 4 owner | anyone else | ☐ | ☐ |
| ≥3 headline findings (FND-001, -005, -006, -008) | Task 4 owner | anyone else | ☐ | ☐ |

#### Decisions requiring team approval

1. **FND-008 pattern rule (new at Gate 3):** bin-median spread ≥10% of the overall median, bins separated beyond 95% bootstrap CIs (200 resamples, seed 42), and absolute bin-order Spearman <0.8 for "non-monotonic". The frozen Gate 2 binned method is unchanged; this rule only labels its output. ☐ Approve / amend / reject.
2. **Findings register format v2.0.0:** separate observed/interpretation columns plus owner and reviewer (required by the Glossary definition). FND-001 broadened to the three strongest pairs. ☐
3. **Code fixes to earlier cells:** stable sort tie-breakers (G3-WF-002, reviewer Krish) and the anomaly-rule assertion (G3-WF-007, reviewer Leng). ☐
4. **Continuous evidence completion** (G3-EDA-004, reviewer Hector). ☐

#### Workflow Run receipt

```json
{
  "workflow_run_id": "WR-SEPT-G3-20261002T205412Z-03140d1",
  "status": "COMPLETED WITH WARNINGS",
  "official_gate3_run": true,
  "run_utc": "2026-10-02T20:54:12+00:00",
  "code_revision": "03140d1e665bdb331bccad20cc7a93d1fbe0148a",
  "clean_at_start": true,
  "source": {
    "path": "data/allstate_claims_data.csv",
    "sha256": "74037cb248a1064e4d578692a4f4e5d8492ed1b2033daf643496e1b68b14ae03",
    "bytes": 70025339
  },
  "runtime": {
    "python": "3.13.16",
    "platform": "macOS-26.5.2-arm64-arm-64bit-Mach-O"
  },
  "dependencies": {
    "matplotlib": "3.11.2",
    "numpy": "2.3.3",
    "pandas": "2.3.2",
    "scipy": "1.18.1",
    "seaborn": "0.13.2"
  },
  "settings": {
    "rare_level_threshold": "support < 100 claims (Gate 2, Task #7); display/support rule only",
    "cardinality_display_rule": "<=10 levels low, >10 high (Gate 2, Task #7)",
    "continuous_bin_rule": "pandas.qcut(q=10, duplicates='drop'); actual bin count recorded (Gate 2 Task 4)",
    "target_plot_settings": "50 bins, no clipping, no sampling (Gate 2 Task 1, item 10)",
    "correlations": "Pearson and Spearman vs raw loss and log1p(loss); Pearson for predictor pairs (Gate 2 Task 4)",
    "binned_pattern_rule (proposed at Gate 3; needs team approval)": {
      "bootstrap_resamples": 200,
      "bootstrap_seed": 42,
      "ci": "95% percentile CI of each bin median",
      "practical_spread": ">= 10% of overall median",
      "monotonic": "abs(Spearman of bin index vs bin median) >= 0.8"
    },
    "random_seeds": "42 for the bootstrap; no other randomized operations",
    "display_precision": "loss 2 dp; skewness and correlations 3 dp; shares 2 dp (%)"
  },
  "reproduction": {
    "artifacts/source_profile.csv": "exact",
    "artifacts/data_dictionary_v1.1.0.csv": "exact",
    "artifacts/categorical_cardinality_verification.csv": "exact",
    "artifacts/categorical_dominance_evidence.csv": "exact",
    "artifacts/categorical_high_cardinality_evidence.csv": "exact",
    "artifacts/categorical_inventory.csv": "exact",
    "artifacts/categorical_level_target.csv": "exact",
    "artifacts/categorical_low_support_evidence.csv": "exact",
    "artifacts/categorical_starting_checks.csv": "exact",
    "artifacts/categorical_target_evidence.csv": "exact",
    "artifacts/continuous_inventory.csv": "exact",
    "artifacts/continuous_bin_target.csv": "exact"
  },
  "independent_review": [
    {
      "item": "target summary",
      "checks": 13,
      "matches": 13,
      "reviewer": "PENDING",
      "independent": false
    },
    {
      "item": "categorical cardinalities (incl. cat116)",
      "checks": 9,
      "matches": 9,
      "reviewer": "PENDING",
      "independent": false
    },
    {
      "item": "continuous-to-target correlations",
      "checks": 14,
      "matches": 14,
      "reviewer": "PENDING",
      "independent": false
    },
    {
      "item": "three strongest continuous pairs",
      "checks": 3,
      "matches": 3,
      "reviewer": "PENDING",
      "independent": false
    },
    {
      "item": "headline findings (FND-001, -005, -006, -008)",
      "checks": 7,
      "matches": 7,
      "reviewer": "PENDING",
      "independent": false
    }
  ],
  "artifact_bundle_ids": {
    "SRC": "G3-SRC-60f8dc926e8c",
    "CAT": "G3-CAT-c627f0cac9e6",
    "CONT": "G3-CONT-7fb198440d14",
    "FND": "G3-FND-f6c55391d79c",
    "CODE": "G3-CODE-ec8db22eb6a4"
  },
  "problems": [],
  "warnings": [
    "independent review incomplete (PENDING or not independent)"
  ]
}
```

#### Team approval

| Member | Role | Approves (Y/N) | Date | Comment |
| :--- | :--- | :--- | :--- | :--- |
| Rachel Cheung | Fellow | | | |
| Leng Lim | Fellow | | | |
| Krish | Fellow | | | |
| Hector Baeza | Fellow | | | |
| | Coach | | | |
| | Challenge Advisor | | | |

#### Disagreements and dissent

| Topic | Positions | Resolution / status |
| :--- | :--- | :--- |
| | | |

#### Limitations carried into October

- All 130 predictors are anonymous; findings are associations within this file and cannot be tied to business mechanisms (FND-009).
- There is one labeled file with no separate test or later-period set, so stability over time is untested (FND-009).
- Binned patterns are univariate, with pointwise intervals across many bins; field labels near the rule thresholds are sensitive (FND-008).
- Extreme losses (high and low) are retained; their validity cannot be confirmed from the data alone (FND-006).
- Marginal correlations do not establish predictive value or feature importance (FND-007).
- September EDA does not establish causation, set individual reserves, show production readiness, or authorize automated claims decisions.

**Verdict:** ☐