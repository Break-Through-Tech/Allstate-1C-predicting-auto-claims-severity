# Predicting Auto Claims Severity

**Company / Org:** Allstate  
**Challenge Advisor:** Krystal Smuda, krystal.smuda@allstate.com; Nancy Zhang, nancy.zhang@allstate.com  
**Program:** Break Through Tech AI Studio - Fall 2026

---

## 🏢 About Allstate

Allstate is a leading provider of insurance and financial services in the United States. We specialize in auto insurance, providing coverage and support to help our customers during times of need.

---

## 🎯 The Challenge

### Project Summary
It can take months to know the final cost to Allstate from a claim due to repair times and legal determinations. If the cost can be estimated up front when the claim is first filed, it can be used to help set reserves and gain a better understanding of what contributes to higher claims. The main goal is to predict the claim’s final cost using insurance claim data.

### Success Criteria
Mean Absolute Error (MAE), students getting hands-on experience setting up and running models, and students understanding how the model works including its input parameters and output.

### Project Milestones

Use these milestones to guide your work. Your team will create a **GitHub Projects board** to track tasks within each milestone.

| Month      | Milestone                | Key Activities                                         |
|------------|--------------------------|-------------------------------------------------------|
| **September** | Data Understanding      | Explore dataset, correlation, plots, document findings |
| **October**  | Model Development       | Create data splits, train baseline model, experiment with approaches, experiment with feature inclusion/exclusion (optional if time), iterate |
| **November** | Evaluation & Presentation| Finalize model, understand key predictor fields (optional if time), prepare presentation, document results |

> **Note for the team:** Please create a GitHub Projects board in this repository to break these milestones into weekly tasks. Go to the **Projects** tab → **New project** → Choose **Board** → Add columns for each month.

---

## 📊 Dataset

**Name and Source:** [Auto Insurance Claims Dataset]  
**Format:** CSV  
**Size:** under 1gb  
**Location:** https://github.com/Break-Through-Tech/Allstate_Auto_Claims_Severity_Prediction/tree/main/data  

### Key Details
- Numerical and categorical data stored in CSV format. Each record represents one auto insurance claim, its total paid amount ('loss' field), and different anonymized claim and vehicle characteristic fields (cat#, cont# fields).  
- There can be times when a claim is closed without any payment. These claims are excluded.  
- Since the predictor fields are anonymized, we want to provide some ideas of what they could be: loss type (animal accident, intersection accident, etc), air bag deployment indicator, highway/interstate indicator, point of impact, time of day, report lag, reported by (insured, family member, claimant, police), number of vehicles involved, vehicle model year, vehicle make, ...  
- Continuous fields are put on a scale between 0 and 1  
- The data is relatively 'clean' but students should still perform exploratory data analysis to get an understand of the data (field, field levels, univariate relation to the target)

---

## 🛠️ Suggested Approach

**ML Problem Type:** Regression  

**Algorithm examples:** generalized linear model (GLM), random forest, gradient boosting machine (GBM), extreme gradient boosting (XGBoost)  


**Recommended Libraries:**
- data analysis and manipulation: pandas
- visualizations: matplotlib  
- modeling: statsmodels, scikit-learn, xgboost, tensorflow, keras  

**Evaluation Metrics:**
- Mean Absolute Error (MAE)
  - a good baseline starting value to compare models to is a mean model (prediction = avg(target))  

---

## 📚 Resources to Get Started

The following resources will help your team understand the problem space and potential technical approaches for this project:

**Background Reading:**
- Car insurance coverages. The target loss is the total of all of these but for more insurance knowledge see here: https://www.allstate.com/resources/car-insurance/types-of-car-insurance-coverage  

**Technical Tutorials:**
- https://medium.com/swlh/modeling-insurance-claim-severity-b449ac426c23  
- https://machinelearningmastery.com/xgboost-for-regression/  
- https://machinelearningmastery.com/gradient-boosting-with-scikit-learn-xgboost-lightgbm-and-catboost/  

*Feel free to explore beyond these, and share anything interesting you find with me!*

---

## 🤝 How We'll Work Together

**Check-ins:** During our biweekly 60-min AI Studio Lab Section meeting block (2nd and 4th week of every month)  
**Communication:** email (see above for emails of your advisor)    
**Response time:** Within 48 hours on weekdays  

**Recommended Tools:**
- **Coding:** Google Colab
- **Collaboration:** GitHub, Notion
- **Virtual Meetings:** Zoom

---

## 🚀 Getting Started

1. **Review this overview document** and note any questions for our first meeting
2. **Begin reviewing the dataset** using the link above
3. **Read the GitHub Projects documentation** [here](https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects)

I'm excited to work with you!

---

## ❓ Questions?

Please bring any questions to our first meeting during the week of August 24th
