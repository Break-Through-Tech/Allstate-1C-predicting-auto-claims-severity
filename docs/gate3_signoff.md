### Gate 3 Independent Verification Sign-Off — Data Understanding Reviewed

**Status:** DRAFT — complete the items marked ☐ before the Team Readiness Review.
**Verification Date:** ☐

#### Exact versions used to pass Gate 3

| Item | Value |
| :--- | :--- |
| Workflow Run ID | ☐ `WR-SEPT-G3-…` (from the receipt printed by the last cell of the official run) |
| Code revision | ☐ commit SHA recorded in the receipt |
| Source | `data/allstate_claims_data.csv` · SHA-256 `74037cb248a1064e4d578692a4f4e5d8492ed1b2033daf643496e1b68b14ae03` · 70,025,339 bytes · 188,318 × 132 |
| Artifact Bundle IDs | ☐ `G3-SRC-…` · `G3-CAT-…` · `G3-CONT-…` · `G3-FND-…` · `G3-CODE-…` (from the same receipt) |
| Findings register | `docs/findings_register.md` v2.0.0 |
| Dependencies | Pinned in `requirements.txt` and enforced by the notebook setup cell: pandas 2.3.2, numpy 2.3.3, scipy 1.18.1, matplotlib 3.11.2, seaborn 0.13.2 |
| Frozen settings | Recorded in the receipt (`T4_CONFIG`): rare-level threshold <100 claims; low/high cardinality ≤10/>10 levels; 10 quantile bins with duplicates dropped (actual: `cont2` 9, `cont5` 8); target plots 50 bins, no clipping, no sampling; bootstrap seed 42 (only randomized step) |

#### Task 4 checklist

- [x] **Findings register** covers every required topic: complete, row-unique table (FND-005); long right tail (FND-006); low/high-cardinality mixture (FND-004); weak marginal linear relationships (FND-007); nonlinear binned patterns (FND-008); continuous redundancy (FND-001); anonymous features and no separate test/future data (FND-009).
- [x] **Observed vs. to-test** kept separate: findings table vs. modeling hypotheses HYP-001–HYP-004.
- [x] **No hand-edited values:** all 45 numbers quoted in the register are recalculated and checked by the notebook on every run.
- [ ] **Independent recalculation** (Gate 3 Task 4 reviewer section of `notebooks/data-understanding.ipynb`, csv + numpy path, no pandas) by someone other than each item's author. See the review matrix below.
- [ ] **Clean Workflow Run** from a committed version, reproducing all discrete results exactly and all numeric results within recorded precision. See *Setup and Installation* in `README.md`.
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

☐ Paste the JSON receipt printed by the last notebook cell of the official run here.

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