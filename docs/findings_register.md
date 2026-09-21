# EDA Findings Register — Allstate Claims Severity

*Evidence Status Glossary: "directly observed", "consistent with a pattern", "hypothesis", "inconclusive".*

| Finding ID | Title | Evidence Link | Result & Interpretation | Evidence Status | Limitations | October Implication |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **FND-001** | `cont11` & `cont12` collinearity | `notebooks/data-understanding.ipynb` (Heatmap) | Pearson correlation of 0.99 indicates near perfect linear redundancy. | Directly observed | Marginal association only | Retain both for September; test removal impact on validation MAE in October. |