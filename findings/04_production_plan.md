# Operational Production Plan: Automated Demand Forecasting Pipeline

**Author:** Sidharth Menon  
**Stakeholder:** Operations Director & Data Engineering Team  
**Scope:** Weekly Batch Inference, Continuous Performance Monitoring & Automated Retraining  
**Milestone:** 05 -- Production Thinking & Deployment Architecture  

---

## 1. System Architecture & End-to-End Data Flow

The production system operates as an asynchronous, containerized batch pipeline orchestrated via Apache Airflow (or AWS Step Functions / Prefect). The model artifact is a serialized Scikit-learn pipeline centered on the **Huber Regressor**.

`mermaid
flowchart LR
    A[("NeonDB PostgreSQL")] -->|Weekly ETL Cutoff Sunday 23:00 UTC| B["Feature Pipeline src/features.py"]
    B -->|Zero-Leakage Lag & Rolling Features| C["Inference Engine Huber Regressor"]
    D[("Model Registry S3 / GCS")] -->|Serialized Artifact v1.2.0.pkl| C
    C -->|1-to-4 Week Demand Forecasts| E[("PostgreSQL ecom.category_forecasts")]
    E -->|Automated Ingestion| F["Tableau / Metabase Procurement Dashboard"]
    E -->|Automated PO Drafting| G["ERP / Supply Chain Replenishment Queue"]
`

---

## 2. Batch Inference Cadence & Execution SLA

* **Execution Window:** Runs every **Sunday at 23:00 UTC** (following weekly order book close at 22:59 UTC).
* **Latency SLA:** The complete pipeline (extract.py -> features.py -> evaluate.py) must terminate and populate ecom.category_forecasts by **Sunday 23:30 UTC** (30-minute hard SLA).
* **Operational Consumer:** Category Procurement Managers access finalized demand projections on Monday morning at **08:00 AM local time** to finalize weekly purchase orders with external suppliers.
* **Output Schema:** Forecasts are stored with forecast_id, created_at, target_week_start, category_id, predicted_units, lower_bound_80ci, upper_bound_80ci, and model_version.

---

## 3. Automated Monitoring & Alert Thresholds

The pipeline executes an automated post-inference validation suite comparing past predictions with freshly realized ground truth actuals:

| Alert Tier | Metric / Condition | Evaluation Scope | Automated Action |
| :--- | :--- | :--- | :--- |
| **P1 -- Critical Alert** | **WMAPE > 40%** OR Model beats Naive by < 0% | Trailing 2-week rolling window | PagerDuty page to On-Call ML Engineer; automated failover to Last-Value Naive baseline in ERP queue. |
| **P2 -- Warning Alert** | **WMAPE > 30%** on any single category | Realized prior week actuals | Slack notification to Category Buyer and ML Team for manual buffer adjustment. |
| **Data Drift Alert** | **PSI > 0.25** or KS-test (p < 0.01) | Input volume and momentum distributions | Flags feature distribution drift; triggers automated data validation checks on upstream tracking. |
| **Anomaly Guardrail** | Prediction swing > 35% WoW without promo tag | Forward inference week | Halts automated PO creation for category; requests human authorization in procurement portal. |

---

## 4. Retraining Cadence & Promotion Gate

* **Scheduled Cadence:** Retrained **quarterly (every 13 weeks)** using an expanding window of historical data (minimum 26 trailing weeks).
* **Event-Driven Trigger:** Automated pipeline kicks off out-of-cycle re-fitting if aggregate 4-week WMAPE deteriorates below the persistence floor (24.71%).
* **Shadow Deployment Gate:** Candidate models must run in a **4-week shadow soak**. A newly trained champion replaces the incumbent only if it demonstrates a statistically significant WMAPE reduction (> 5% relative improvement) and zero inference errors.

---

## 5. Cold Starts & Boundary Edge Cases

* **New Category Launches (< 4 weeks history):** The pipeline flags cold-start status and routes forecasts to an analog hierarchical model using parent department averages combined with marketing launch plan targets.
* **Promotional Campaign Surges:** Marketing logs planned campaign dates in an upstream marketing_calendar table. When active, momentum damping weights are temporarily relaxed to absorb campaign lifts without lagged over-projection during post-campaign cool-downs.
