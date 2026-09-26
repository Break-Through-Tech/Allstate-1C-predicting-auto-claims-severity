# Anomaly Register — Allstate Claims Severity

| Anomaly ID | Date Logged | Severity | Category | Description | Evidence | Owner | Status | Handling Decision | Likely Impact |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |

| G3-WF-001 | 2026-09-25 | Medium — Non-blocking | Workflow | Gate 2 categorical-analysis code is stored as quoted strings, so the notebook cell displays the code instead of executing it. | 1 notebook cell affected | Leng | Open | Preserve the existing categorical artifacts and correct the notebook cell before categorical analysis is rerun. | Does not block Gate 3 Task 1 source-profile or target-distribution verification, but categorical-analysis reruns are unreliable until corrected. |

