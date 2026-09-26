# Anomaly Register — Allstate Claims Severity

| Anomaly ID | Date Logged | Severity | Category | Description | Evidence | Owner | Status | Handling Decision | Likely Impact |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |

| G3-WF-001 | 2026-09-25 | Medium — Non-blocking | Workflow | Gate 2 categorical-analysis code is stored as quoted strings, so the notebook cell displays the code instead of executing it. | 1 notebook cell affected | Leng | Resolved (Task #10, 2026-09-26) | Restored the quoted Task #7 code to executable Python without changing its methods; verified by a complete notebook rerun. | Historical workflow issue; categorical artifacts now regenerate successfully. No source data changes. |

