# Candidate decision and October report completion

Verified existing baseline and candidate predictions using the shared evaluator and exact frozen validation IDs. Added reusable strict two-baseline decision logic with synthetic tests, reviewed the pre-recorded XGBoost retention policy, refreshed diagnostics for all released candidates, and generated a stakeholder report and formal technical recommendation.

Decision: **PROVISIONAL_CANDIDATE — XGBoost A2-C03**.

| Candidate | Validation MAE | Claims | Change vs mean | Change vs median | Improvement vs mean | Improvement vs median | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| Ridge GLM | 1250.453333 | 28248 | -709.177583 | -552.340521 | 36.189344% | 30.638030% | QUALIFIES |
| XGBoost A2-C03 | 1167.515314 | 28248 | -792.115603 | -635.278540 | 40.421673% | 35.238557% | PROVISIONAL_CANDIDATE |
| XGBoost A2-C06 | 1166.681104 | 28248 | -792.949812 | -636.112750 | 40.464243% | 35.284830% | NOT_RETAINED_BY_EXISTING_POLICY |

September EDA examined the full labeled file, including claims later assigned to validation and reserved test. These are retrospective results, not independent prospective confirmation. Filing-time inputs are an Advisor-authorized assumption; individual feature definitions, timestamps and lineage remain unverified. High-loss underprediction persists. Gate 4 reproduction matched predictions exactly but used Python 3.13.2 rather than 3.13.5, so exact environment confirmation remains conditional. Reproductions do not establish random-seed stability.

The GLM-only comparison is historical, not current. All candidate releases now have valid evidence. A2-C06 remains non-retained under the training-CV policy despite its slightly lower validation score. The GLM reproduction narrative and receipt differ in their precision; this report uses receipt values and labels cross-run training evidence.

Next confirmation: Evaluate the unchanged retained model on newly supplied, temporally separated claims after agreeing a protocol; do not tune on that cohort. Success criterion: Strictly lower MAE than both frozen constants; exact claim coverage and valid filing-time provenance. Pre-register uncertainty and business criteria before results are seen. Team/Advisor review, independent data, feature lineage and exact-environment reproduction remain open; no approval is fabricated.

Files: `scripts/model_comparison.py` (decision helper); `scripts/candidate_report.py`; `tests/test_candidate_decision.py`; `docs/october_report.md`; `docs/october_candidate_decision.md`; this summary; decision CSV/JSON, target-bin/high-loss CSVs, development evidence JSON and report receipt under `artifacts/october/gate 4/candidate_decision/decision-20261124T070336Z-7db5f673`.

Reproduce: `python3 -m scripts.candidate_report --write-docs`. Synthetic tests: `python3 -m unittest discover -s tests -p test_candidate_decision.py`. The run receipt contains the computed validation checklist, tests and exact hashes. Generation code version is distinct from the eventual commit containing these outputs.

All 80 relevant decision, comparison, evaluator, partition and Gate 2 verification tests pass (including 19 new decision tests); the broader 106-test repository run encountered 29 error entries from the missing `xgboost` dependency in existing runner tests. This limitation is separate from the report's verified prediction results.

No new candidate models trained, baseline constants refitted, hyperparameters tuned, partition assignments changed, additional internal test targets inspected, or production-readiness claims made.
