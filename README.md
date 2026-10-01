# Demand Forecasting with Machine Learning

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Database](https://img.shields.io/badge/PostgreSQL-NeonDB-336791.svg)](https://neon.tech/)
[![Framework](https://img.shields.io/badge/scikit--learn-Time--Series-F7931E.svg)](https://scikit-learn.org/)
[![Status](https://img.shields.io/badge/Project_Status-Milestone_1_Complete-success.svg)]()

> **Operations Objective:** Forecast weekly demand across product categories to optimize inventory replenishment, prevent costly stockouts, and minimize inventory holding costs.

---

## Business Problem & Context

In high-growth e-commerce operations, inaccurate demand planning leads to two symmetrical financial liabilities:
1. **Stockouts on High-Velocity SKUs:** Lost gross merchandise value (GMV), disrupted customer acquisition momentum, and lower retention.
2. **Over-Ordering on Low-Velocity SKUs:** Bloated working capital, increased warehouse storage fees, and eventual inventory markdowns or write-offs.

This project builds an end-to-end, leakage-free machine learning demand forecasting pipeline on transactional order data from **40,000 customer orders** across **14 active product categories** and **4,000 catalog products**.

---

## Project Milestones & Roadmap

| Milestone | Status | Title & Scope | Key Deliverables |
| :--- | :---: | :--- | :--- |
| **Milestone 1** | **Completed** | **Project Setup & Repository Skeleton** | Repository scaffolding, pinned dependencies (
equirements.txt), secure credential handling (.env), SQL extraction pipeline (sql/extract_weekly_demand.sql, src/extract.py). |
| **Milestone 2** | Queued | **Frame the Problem & Explore Demand** | Aggregate order history to weekly series; analyze category-level trend, seasonality, intermittent zero-order weeks, coefficient of variation ($), and stationarity tests (
otebooks/01_eda_demand_exploration.ipynb). |
| **Milestone 3** | Queued | **Engineer Time-Series Features** | Construct lag features (-1, t-2, t-4$), rolling statistics (4-week and 12-week moving averages, standard deviation, min/max), and calendar signals strictly avoiding lookahead leakage (src/features.py, 
otebooks/02_feature_engineering.ipynb). |
| **Milestone 4** | Queued | **Train, Evaluate & Compare Models** | Establish persistence and Seasonal Naive baselines; train Linear/Ridge, Random Forest, and Gradient Boosted Trees (XGBoost/LightGBM) using rolling-origin cross-validation (TimeSeriesSplit); evaluate on RMSE, MAE, and WMAPE (
otebooks/03_model_training_evaluation.ipynb). |
| **Milestone 5** | Queued | **Production Thinking & Portfolio Polish** | Formulate an operational production deployment roadmap (indings/04_production_plan.md) specifying weekly Sunday cron inference, drift alert thresholds, and quarterly retraining; synthesize 3 quantified takeaways in an Executive Memo (indings/00_executive_summary.md). |

---

## Repository Structure

`	ext
demand-forecasting-ml/
├── .gitignore                          # Excludes secrets (.env), caches, and raw CSV dumps
├── .env.example                        # Template for database connection configuration
├── requirements.txt                    # Pinned Python dependencies
├── README.md                           # Project front-door documentation & reproduction guide
├── data/
│   ├── raw/                            # Extracted weekly transactional aggregates (git-ignored)
│   └── processed/                      # Feature-engineered training/validation matrices
├── sql/
│   └── extract_weekly_demand.sql       # PostgreSQL extraction query against ecom schema
├── src/
│   ├── __init__.py                     # Package declaration
│   ├── extract.py                      # Database extraction engine (reads NeonDB via .env)
│   ├── features.py                     # Leakage-free lag & rolling feature generators
│   ├── models.py                       # Baseline regressors & machine learning estimators
│   └── evaluate.py                     # Time-series cross-validation & evaluation metrics
├── notebooks/
│   ├── 01_eda_demand_exploration.ipynb # Milestone 2: Exploratory demand analysis
│   ├── 02_feature_engineering.ipynb    # Milestone 3: Feature construction & leakage audits
│   └── 03_model_training_evaluation.ipynb # Milestone 4: Model benchmarking & error analysis
├── findings/
│   ├── 00_executive_summary.md         # Milestone 5: 3 quantified operational insights
│   └── 04_production_plan.md          # Milestone 5: Inference cadence, monitoring, & retraining
└── figures/                            # Exported charts (prediction vs actual, error distributions)
`

---

## Data Pipeline & Database Architecture

The source database is hosted on NeonDB (PostgreSQL) under the ecom schema:
* ecom.orders: 40,000 order headers (status, created_at, subtotal, 	otal, etc.).
* ecom.order_items: 81,806 order items (qty, unit_price, line_total).
* ecom.product_variants & ecom.products: 4,000 catalog items categorized across 14 active lines (e.g. *Skincare*, *Shoes*, *Accessories*, *Decor*, *Headphones*, *Jackets*).

The weekly demand query aggregates line-item demand into weekly intervals:
\text{units\_demanded}_{c, w} = \sum_{i \in \text{orders}_{c, w}} \text{qty}_i

---

## Quickstart & Reproduction Guide

### 1. Clone & Setup Environment
`ash
git clone https://github.com/sidharthmenon626-lab/demand-forecasting-ml.git
cd demand-forecasting-ml

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
`

### 2. Configure Database Credentials
Create a .env file in the project root:
`ash
cp .env.example .env
`
Populate DATABASE_URL with your PostgreSQL credentials:
`env
DATABASE_URL=postgresql://<user>:<password>@<host>:5432/<database>?sslmode=require
`

### 3. Extract Weekly Demand Data
Run the extraction pipeline:
`ash
python src/extract.py
`
This executes sql/extract_weekly_demand.sql and saves the extracted 31,938 aggregated records to data/raw/weekly_demand.csv.

---

## Tech Stack & Tools

* **Programming:** Python 3.11+
* **Data Manipulation:** pandas, NumPy
* **Database / SQL:** PostgreSQL (NeonDB), psycopg2-binary
* **Modeling & Metrics:** scikit-learn (TimeSeriesSplit), statsmodels, XGBoost, LightGBM
* **Visualization:** matplotlib, seaborn
* **Orchestration / Notebooks:** Jupyter
