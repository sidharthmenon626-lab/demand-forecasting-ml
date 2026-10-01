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

### Target Variable: Units Demanded (units_demanded)
* **Definition:** Net aggregate quantity of physical items ordered across confirmed customer orders in a Monday-to-Sunday weekly cycle.
* **Why Units over Revenue:** Warehouse storage, pallet allocation, and supplier replenishment depend strictly on physical volume, not discounted rupee values.

### Granularity: Weekly at Category Level (14 Categories)
* **Weekly Aggregation:** Daily order volumes exhibit excessive intra-week noise (weekend vs. weekday traffic swings) irrelevant for wholesale procurement, which runs on weekly purchasing batches.
* **Category Aggregation:** Across the 4,000 catalog SKUs, **38.6% of individual SKU-weeks have zero orders** (intermittent Poisson demand). Modeling individual SKUs on 13 weeks of history leads to severe overfitting. In contrast, all 14 product categories (*Skincare*, *Shoes*, *Accessories*, *Decor*, *Headphones*, etc.) maintain **100% active order continuity** across all 13 weeks (averaging 399 to 499 units/week), providing sufficient statistical density.

### Forecast Horizon: 1 to 4 Weeks Forward
* **Procurement Lead Time:** Supplier lead times range from 7 to 21 days (1 to 3 weeks). A 1-to-4 week rolling horizon directly informs purchase orders before safety stocks breach, avoiding the unreliability of multi-month forecasts on short series.

### Metric Choice: WMAPE (Primary) & RMSE (Secondary)
* **Why Standard MAPE Breaks:** Mean Absolute Percentage Error divides by actual demand:
  \\text{MAPE} = \\frac{1}{n} \\sum_{t=1}^n \\left| \\frac{y_t - \\hat{y}_t}{y_t} \\right|
  On low-demand weeks, tiny denominators cause MAPE to explode disproportionately.
* **Why WMAPE Excels:**
  \\text{WMAPE} = \\frac{\\sum_{t=1}^n |y_t - \\hat{y}_t|}{\\sum_{t=1}^n y_t}
  WMAPE scales absolute errors by aggregate volume, yielding a robust percentage error that cannot divide by zero and properly weights top revenue categories.
* **Secondary Metric (RMSE):** Quadratically penalizes large forecasting misses, guarding Operations against catastrophic stockouts on high-volume product lines.

---

## 3. Empirical Demand Profile (Historical Findings)

Analysis of the 13-week order history (March 16 – June 14, 2026; 40,000 orders; 83,259 units) reveals:
1. **Macro Trend & Surge:** Demand escalated from 9,214 units to a promotional peak of **11,134 units** in early April (+20.8%), followed by a persistent decay down to **2,551 units** in June (-77.1%).
2. **Category Co-movement:** All 14 categories co-moved synchronously with this promotional pulse.
3. **Volatility:** Category Coefficients of Variation ( = \\sigma / \\mu$) cluster tightly between **0.413** (*Jeans*) and **0.477** (*Headphones*).
4. **Statistical Non-Stationarity:** Augmented Dickey-Fuller (ADF) testing yields a test statistic of **-0.527 ( = 0.887$)**, confirming non-stationarity and necessitating autoregressive lag features (-1, t-2$) in Milestone 3.

---

## 4. Practical Constraints & Tractability Risks

1. **Short Historical Horizon (13 Weeks):** A single quarter prevents capturing 52-week annual seasonality or holiday shifts. The model must rely on short-term momentum rather than yearly seasonal indices.
2. **Asymmetric Error Costs:** Stockouts cause permanent lost sales ( \\approx 3x-5x$), whereas over-forecasting incurs holding fees. Quantile monitoring ($) will be needed in production.
