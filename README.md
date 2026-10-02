# AI Studio Challenge Project Title

> 💡 **Note for the team:** This is just a template. Update the above title with your AI Studio Challenge Project name. Remove all guidance notes and example text in this template and populate this README with your own content. You can work on this README throughout AI Studio, and get feedback from your AI Studio Coach and Challenge Advisor before finalizing it.  

---

### 👥 **Team Members**

**Example:**

| Name             | GitHub Handle | Contribution                                                             |
|------------------|---------------|--------------------------------------------------------------------------|
| Taylor Nguyen    | @taylornguyen | Data exploration, visualization, overall project coordination            |
| Jordan Ramirez   | @jramirez     | Data collection, exploratory data analysis (EDA), dataset documentation  |
| Amina Hassan     | @aminahassan  | Data preprocessing, feature engineering, data validation                 |
| Priya Mehta      | @pmehta       | Model selection, hyperparameter tuning, model training and optimization  |
| Chris Park       | @chrispark    | Model evaluation, performance analysis, results interpretation           |

---

## 🎯 **Project Highlights**

**Example:**

- Developed a machine learning model using `[model type/technique]` to address `[challenge project task]`.
- Achieved `[key metric or result]`, demonstrating `[value or impact]` for `[host company]`.
- Generated actionable insights to inform business decisions at `[host company or stakeholders]`.
- Implemented `[specific methodology]` to address industry constraints or expectations.

---

## 👩🏽‍💻 **Setup and Installation**

The September EDA runs as one notebook: `notebooks/data-understanding.ipynb` (Gates 1–3). The dataset is included in the repository at `data/allstate_claims_data.csv` (SHA-256 `74037cb2…ae03`).

**Official Workflow Run (VS Code)**

1. Clone the repository and check out the exact commit being verified (`git checkout <commit-sha>`). `git status` must show no changes.
2. Create and activate a virtual environment, then install the pinned versions:
   `pip install pandas==2.3.2 numpy==2.3.3 scipy==1.18.1 matplotlib==3.11.2 seaborn==0.13.2 ipykernel`
3. Open `notebooks/data-understanding.ipynb` in VS Code, select that environment as the kernel, and click **Run All**. The notebook must run from the `notebooks/` folder (VS Code's default).
4. The last cell prints the Workflow Run receipt: status, reproduction check against the committed artifacts, dependency versions, settings, and Artifact Bundle IDs. A passing official run shows `"official_gate3_run": true`. Copy the receipt into `docs/gate3_signoff.md`.

After the Gate 3 receipt, the Gate 4 section checks that counts agree across all artifacts, writes the Artifact Manifest (`artifacts/artifact_manifest.json`), and prints the Gate 4 Run Receipt with the September Artifact Bundle ID. A passing official run shows `"official_gate4_run": true`; record it in `docs/gate4_signoff.md`.

The run fails if the source file's SHA-256 changes, if `docs/findings_register.md` quotes a value the data does not reproduce, or if the independent recalculation disagrees with the primary results.

---

## 🏗️ **Project Overview**

**Describe:**

- How this project is connected to the Break Through Tech AI Program
- Your AI Studio host company and the project objective and scope
- The real-world significance of the problem and the potential impact of your work

---

## 📊 **Data Exploration**

**You might consider describing the following (as applicable):**

* The dataset(s) used: origin, format, size, type of data
* Data exploration and preprocessing approaches
* Insights from your Exploratory Data Analysis (EDA)
* Challenges and assumptions when working with the dataset(s)

**Potential visualizations to include:**

* Plots, charts, heatmaps, feature visualizations, sample dataset images

---

## 🧠 **Model Development**

**You might consider describing the following (as applicable):**

* Model(s) used (e.g., CNN with transfer learning, regression models)
* Feature selection and Hyperparameter tuning strategies
* Training setup (e.g., % of data for training/validation, evaluation metric, baseline performance)


---

## 📈 **Results & Key Findings**

**You might consider describing the following (as applicable):**

* Performance metrics (e.g., Accuracy, F1 score, RMSE)
* How your model performed
* Insights from evaluating model fairness

**Potential visualizations to include:**

* Confusion matrix, precision-recall curve, feature importance plot, prediction distribution, outputs from fairness or explainability tools

---

## 🚀 **Next Steps**

**You might consider addressing the following (as applicable):**

* What are some of the limitations of your model?
* What would you do differently with more time/resources?
* What additional datasets or techniques would you explore?

---

## 📝 **License**

Specify how your project can be used by others. Choose an appropriate license and link it here (e.g., MIT, Apache 2.0). Make sure your Challenge Advisor approves of the selected license type. 

**Example:**
This project is licensed under the MIT License.

---

## 📄 **References** (Optional but encouraged)

Cite relevant papers, articles, or resources that supported your project.

---

## 🙏 **Acknowledgements** (Optional but encouraged)

Thank your Challenge Advisor, host company representatives, TA, and others who supported your project.
