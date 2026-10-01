# Executive Summary: Machine Learning Demand Forecasting for Inventory Procurement

**Author:** Sidharth Menon  
**Stakeholder:** Operations Director  
**Scope:** Final Operational Synthesis & Strategic Recommendations  
**Deliverable:** 00 -- Executive Memorandum  

---

## Executive Overview

To optimize wholesale inventory replenishment and curb stockouts, we developed an audited, leakage-free weekly demand forecasting engine evaluated on **83,259 units** across **14 product categories** over 13 weeks of order history.

---

## Three Key Quantified Operational Takeaways

### 1. Robust ML Outperforms Naive Persistence by +22.28% (19.20% WMAPE)
The **Huber Regressor** achieved a **19.20% WMAPE** and **60.77 RMSE** under rolling-origin cross-validation, delivering a **+22.28% error reduction** over the Last-Value Naive benchmark (24.71% WMAPE). By leveraging short-term demand momentum (2w - 4w difference), the model automatically damps replenishment projections during post-promotional cooling phases, preventing chronic inventory bloat.

### 2. Resolving the 38.5% Intermittency Dilemma via Category Aggregation
At the individual SKU level, **38.5% of SKU-weeks exhibited zero orders** (intermittent Poisson distribution), which destabilizes parametric models. Aggregating demand to 14 product categories provides **100% temporal continuity** (averaging 399 to 499 units/week), eliminating sparse noise while aligning forecasting directly with wholesale supplier ordering batches.

### 3. Tiered Safety Stock Buffering to Free Working Capital
Demand volatility analysis (CV = sigma / mu) reveals two operational tiers:
* **Discretionary Lines (Headphones, Decor, Shoes, CV approx 0.47):** Require a **20-25% safety stock buffer** to absorb rapid campaign swings.
* **Core Staple Lines (Bedding, Kitchen, CV approx 0.41):** Require only an **8-12% buffer**, enabling immediate working capital reductions without stockout risk.
