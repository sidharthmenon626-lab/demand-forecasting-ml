# Technical Brief: Time-Series Feature Engineering & Temporal Hygiene

**Author:** Sidharth Menon  
**Stakeholder:** Operations Director  
**Context:** Feature Store Architecture & Leakage-Free Predictors  
**Milestone:** 03 — Time-Series Feature Engineering  

---

## 1. Feature Architecture Overview

To forecast weekly category demand without future lookahead, we engineered a feature matrix containing **1 row per `(category x week)`** with **14 predictive features** organized into four functional groups:

| Feature Group | Features | Operational / Behavioral Rationale |
| :--- | :--- | :--- |
| **A. Autoregressive Lags** | `demand_lag_1`, `demand_lag_2`, `demand_lag_4` | Captures baseline demand level, 2-week momentum, and 1-month replenishment anchors ($r = 0.867$ for lag 1). |
| **B. Rolling Window Statistics** | `rolling_mean_2w`, `rolling_mean_4w`, `rolling_std_4w`, `rolling_min_4w`, `rolling_max_4w` | Smooths high-frequency weekly noise, provides local trend directions, and quantifies recent demand dispersion/volatility. |
| **C. Momentum & Velocity** | `demand_momentum_2w_4w`, `demand_growth_ratio_1w_2w` | Measures acceleration versus cooling; signals whether promotional surges are decaying before actual sales drop. |
| **D. Calendar & Telemetry Signals** | `month`, `week_of_year`, `is_month_start_week`, `revenue_lag_1`, `order_count_lag_1`, `avg_price_lag_1` | Encodes intra-quarter seasonality, month-start payday surges, and historical order frequency. |

---

## 2. Temporal Hygiene: How Leakage Was Strictly Prevented

The single most destructive vulnerability in machine learning demand forecasting is **lookahead leakage**—where features for target week $W$ accidentally compute statistics containing week $W$.

### The Mandatory `shift(1)` Protocol:
In standard pipelines, computing `df['demand'].rolling(4).mean()` at week $W$ averages weeks $[W-3, W-2, W-1, W]$, directly leaking the ground-truth target.

To eliminate this vulnerability mathematically, all time-series transformations enforce an invariant:
$$\text{Feature}_W = f(y_{t \le W-1})$$

In [`src/features.py`](../src/features.py), every rolling calculation is preceded by a strict group-level `.shift(1)`:
```python
shifted_demand = df.groupby('category_name')['units_demanded'].shift(1)
df['rolling_mean_4w'] = shifted_demand.groupby(df['category_name']).transform(
    lambda s: s.rolling(window=4, min_periods=4).mean()
)
```
Furthermore, all unlagged current-week transactional fields (`units_demanded`, `total_revenue`, `order_count`, `avg_unit_price`) are excised from the feature matrix $X$, ensuring estimators only access historical predictors.

---

## 3. Deliberately Omitted Features

1. **52-Week Annual Lag ($t-52$):** The transaction history spans 13 weeks (March 16 – June 14, 2026). Attempting 52-week lookbacks would require imputing 75% of the series or zero-padding, injecting artificial noise.
2. **Next-Week Promotional / Price Schedules:** In practice, mid-week markdowns and promotional changes are enacted dynamically. Feeding forward-looking pricing signals would introduce lookahead bias.

---

## 4. Verification & Automated Leakage Audit

Our automated assertion test suite ([`src/features.py`](../src/features.py)) audited the materialized feature matrix:
* **Test 1 (Lag Alignment):** Verified across all 126 category-weeks that $\text{demand\_lag\_1}_{c, W} \equiv y_{c, W-1}$ ($100\%$ exact match).
* **Test 2 (Rolling Exclusion):** Confirmed that $\text{rolling\_mean\_2w}_{c, W} = \frac{y_{W-1} + y_{W-2}}{2}$, with week $W$ strictly excluded.
* **Test 3 (Correlation Check):** The maximum feature-to-target Pearson correlation is **0.867** (`demand_lag_1`), confirming realistic autoregressive predictive power without label memorization ($r < 0.999$).
* **Baseline Sanity Model:** A simple Ridge regression fit on training folds produced an $R^2$ of **0.784** ($WMAPE \approx 18.2\%$)—a realistic, sound baseline ready for Milestone 4.
