# Executive Brief: Demand Forecasting Problem Framing

**Author:** Sidharth Menon  
**Stakeholder:** Operations Director  
**Context:** E-Commerce Weekly Inventory Planning & Replenishment  
**Milestone:** 02 — Problem Framing & Exploratory Demand Analysis  

---

## 1. Concrete Problem Statement

> **Objective:** **Predict weekly units demanded** at the **product category level** for a **1-to-4 week forward horizon**, evaluated primarily by **Weighted Mean Absolute Percentage Error (WMAPE)** and benchmarked against **Root Mean Squared Error (RMSE)**.

---

## 2. Core Problem Architecture & Technical Justification

### Target Variable: Units Demanded (`units_demanded`)
* **Definition:** Net aggregate quantity of physical items ordered across successful customer orders within a given Monday-to-Sunday weekly cycle.
* **Why Not Gross Revenue:** Inventory planning, container booking, pallet allocation, and warehouse shelf storage depend strictly on physical unit volume, not currency fluctuations or promotional price cuts.

### Granularity: Weekly at Category Level (Primary)
* **Time Granularity (Weekly):** Daily order volumes suffer from high intra-week noise (e.g. weekend vs. weekday traffic swings) that are irrelevant for wholesale supplier replenishment orders, which operate on weekly procurement batches.
* **Entity Granularity (Category Level across 14 Categories):** Across the 4,000 catalog SKUs, **38.6% of individual SKU-weeks have zero sales** (intermittent/lumpy Poisson demand). Attempting direct single-SKU forecasting on a 13-week history leads to severe overfitting and parameter instability. In contrast, all 14 product categories (*Skincare*, *Shoes*, *Accessories*, *Decor*, *Headphones*, etc.) maintain **100% active order continuity** across all 13 weeks (averaging 399 to 499 units/week), providing sufficient statistical density.

### Forecast Horizon: 1 to 4 Weeks Ahead
* **Operational Lead Time:** Warehouse replenishment and local supplier lead times range between 7 and 21 days (1 to 3 weeks). A 1-to-4 week rolling horizon directly informs purchase orders before safety stocks are breached, while avoiding the unreliability of multi-month forecasts on short historical series.

### Metric Choice: WMAPE (Primary) & RMSE (Secondary)
* **Why Not Standard MAPE:** Standard Mean Absolute Percentage Error divides by actual demand:
  $$\text{MAPE} = \frac{1}{n} \sum_{t=1}^n \left| \frac{y_t - \hat{y}_t}{y_t} \right|$$
  When evaluated on lower-volume categories or lower-demand weeks, small denominators cause MAPE to explode disproportionately.
* **Why WMAPE (Weighted MAPE):**
  $$\text{WMAPE} = \frac{\sum_{t=1}^n |y_t - \hat{y}_t|}{\sum_{t=1}^n y_t}$$
  WMAPE scales the absolute errors by total demand volume, yielding a robust, business-interpretable percentage that cannot divide by zero and accurately weights high-volume commercial lines.
* **Secondary Metric (RMSE):** Captures large catastrophic forecasting errors through quadratic penalization, guarding Operations against severe under-forecasts on top revenue drivers.

---

## 3. Empirical Demand Profile (What the Data Shows)

Based on the initial 13-week transaction window (March 16, 2026 to June 14, 2026; 40,000 orders; 83,259 total units demanded):
1. **Macro Trend & Campaign Surge:** Demand surged from 9,214 units in mid-March to a promotional peak of **11,134 units** in the week of April 6, 2026 (+20.8%), followed by a persistent decay into May and June, bottoming at **2,551 units** in the week of June 8.
2. **Category Co-movement:** All 14 product categories co-moved with this promotional pulse, displaying synchronized surge and decay patterns.
3. **Volatility:** Category Coefficients of Variation ($CV = \sigma / \mu$) fall in a narrow band between **0.413** (*Jeans*) and **0.477** (*Headphones*), demonstrating stable relative dispersion.
4. **Statistical Non-Stationarity:** Augmented Dickey-Fuller (ADF) testing yielded a test statistic of **-0.527 ($p = 0.887$)** on the aggregate series, rejecting stationarity at the 5% significance level. Demand is non-stationary in levels and requires differencing and autoregressive lag transformations.

---

## 4. Practical Constraints & Tractability Risks

1. **Short Historical Horizon (13 Weeks):** A single quarter of data prevents capturing full 52-week annual seasonality or holiday calendar shifts (e.g. Diwali / Black Friday). The model must rely on short-term autoregressive momentum ($t-1, t-2, t-4$) rather than annual cycle components.
2. **Asymmetric Error Costs:** In operations, stockouts cause permanent lost sales and customer dissatisfaction ($cost \approx 3x-5x$), whereas over-forecasting incurs temporary warehouse holding costs. Quantile loss monitoring ($p75$ / $p80$) should be considered during model deployment.
