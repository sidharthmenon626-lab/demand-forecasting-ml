# Technical Brief: Model Benchmarking, Time-Series Cross-Validation & Honest Lift Analysis

**Author:** Sidharth Menon  
**Stakeholder:** Operations Director  
**Context:** Model Selection & Cross-Validation Benchmarking  
**Milestone:** 04 — Model Training & Evaluation  

---

## 1. Executive Summary & Honest Comparison

To establish trustworthy demand forecasts, we evaluated six candidate models using an expanding-window **`TimeSeriesSplit` (5 temporal folds)** over post-warmup weeks. In accordance with operational forecasting standards, models were evaluated strictly out-of-fold using the primary metric committed in Milestone 2: **Weighted Mean Absolute Percentage Error (WMAPE)** and **Root Mean Squared Error (RMSE)**.

### Audited Cross-Validation Benchmark:

| Model Architecture | Mean WMAPE | Std WMAPE | Mean RMSE | Std RMSE | WMAPE Lift vs. Naive | RMSE Lift vs. Naive |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Huber Regressor (Robust ML)** | **19.20%** | $\\pm 13.99\\%$ | **60.77** | $\\pm 48.54$ | **+22.28%** | **+15.46%** |
| **Last-Value Naive (Floor)** | **24.71%** | $\\pm 10.57\\%$ | **71.88** | $\\pm 18.76$ | Baseline ($0.0\\%$) | Baseline ($0.0\\%$) |
| **Ridge Regressor** | **25.13%** | $\\pm 14.51\\%$ | **72.94** | $\\pm 42.67$ | $-1.70\\%$ | $-1.48\\%$ |
| **Random Forest (max_depth=3)** | **26.96%** | $\\pm 14.96\\%$ | **74.96** | $\\pm 28.43$ | $-9.10\\%$ | $-4.29\\%$ |
| **XGBoost (max_depth=2)** | **33.27%** | $\\pm 23.89\\%$ | **84.89** | $\\pm 37.62$ | $-34.67\\%$ | $-18.10\\%$ |
| **4-Week Moving Average** | **34.55%** | $\\pm 26.30\\%$ | **85.89** | $\\pm 50.69$ | $-39.82\\%$ | $-19.49\\%$ |

---

## 2. What the Baseline Does vs. What Machine Learning Adds

### The Last-Value Naive Baseline (The 24.71% Floor):
The naive persistence baseline predicts $\\hat{y}_{c, W} = y_{c, W-1}$. In stable demand regimes, it captures the immediate level of the series without training overhead. However, when demand entered a prolonged post-promotional decay across May and June, persistence suffered from **systematic over-forecasting lag**—projecting stale peak volume into cooling weeks.

### What the Robust ML Model Adds (+22.28% Lift):
The **Huber Regressor** overcomes persistence lag by utilizing our engineered momentum features:
1. **Trend Adjustment:** Rather than assuming static persistence ($\\beta=1.0$), Huber weights `demand_lag_1` alongside `demand_momentum_2w_4w` ($2w - 4w$ moving average difference), automatically scaling down predictions when short-term momentum falls below the 4-week average.
2. **Outlier Resistance:** By applying linear loss to large residuals and squared loss to small ones, Huber is not thrown off by the early-April promotional demand spike, avoiding variance inflation.

---

## 3. Why Tree Ensembles Underperformed Linear Models

A critical diagnostic insight from our benchmark is that **Random Forest (26.96% WMAPE)** and **XGBoost (33.27% WMAPE)** underperformed linear models:
* **The Extrapolation Limit of Trees:** Decision trees partition feature space into orthogonal step-functions and predict the mean of the training leaf. When weekly demand declined into new historical minimums during June, tree models were mathematically incapable of predicting values below their lowest training leaves, causing persistent positive bias.
* **Linear Slope Extrapolation:** The Huber regressor continuously extrapolated the downward trend slope, outperforming tree ensembles by **14.07 percentage points** on WMAPE.

---

## 4. Failure Mode Diagnosis (Seeds for Milestone 5 Operationalization)

* **Temporal Cliff:** The highest forecasting errors occurred during the rapid transition out of the promotional campaign (weeks of April 20 and April 27), where demand dropped over $25\\%$ week-over-week.
* **Category Variance:** High-volume discretionary categories (*Headphones*, *Shoes*, *Decor*) had higher absolute errors ($MAE \\approx 75-90\\text{ units}$) than staple lines (*Bedding*, *Kitchen*, $MAE \\approx 50-60\\text{ units}$).
* **Operational Implication:** In production, automated alert thresholds must be configured on weekly WMAPE exceeding $35\\%$, prompting manual review during marketing campaign roll-offs.
