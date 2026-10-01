"""
Feature Engineering Engine for Weekly Demand Forecasting.
Constructs leakage-free autoregressive lag, rolling statistics, momentum,
and calendar features from category-level weekly demand series.
"""

import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np

ROOT_DIR = Path(__file__).resolve().parent.parent

def load_raw_demand(data_path: Path = None) -> pd.DataFrame:
    """Loads and aggregates raw transactional data to category-week level."""
    if data_path is None:
        data_path = ROOT_DIR / "data" / "raw" / "weekly_demand.csv"
    
    if not data_path.exists():
        raise FileNotFoundError(f"Raw demand data not found at {data_path}. Run src/extract.py first.")
    
    df = pd.read_csv(data_path)
    df["week_start"] = pd.to_datetime(df["week_start"])
    
    # Aggregate across individual products to pure category x week granularity
    cat_weekly = df.groupby(["week_start", "category_id", "category_name"]).agg(
        units_demanded=("units_demanded", "sum"),
        total_revenue=("total_revenue", "sum"),
        order_count=("order_count", "sum"),
        avg_unit_price=("avg_unit_price", "mean")
    ).reset_index()
    
    # Strict sort by category and temporal order
    cat_weekly = cat_weekly.sort_values(["category_name", "week_start"]).reset_index(drop=True)
    return cat_weekly


def build_features(df: pd.DataFrame, drop_warmup: bool = True) -> pd.DataFrame:
    """
    Constructs time-series features with strict temporal hygiene.
    
    Temporal Hygiene Invariant:
    Every feature for prediction at week W is computed strictly from data <= W-1.
    All rolling statistics are preceded by a mandatory group-level shift(1).
    """
    # Ensure temporal ordering within category groups
    df = df.sort_values(["category_name", "week_start"]).reset_index(drop=True).copy()
    
    grouped = df.groupby("category_name")
    
    # Target variable to predict (week W demand)
    df["target"] = df["units_demanded"]
    
    # -------------------------------------------------------------------------
    # Group A: Autoregressive Lag Features
    # -------------------------------------------------------------------------
    df["demand_lag_1"] = grouped["units_demanded"].shift(1)
    df["demand_lag_2"] = grouped["units_demanded"].shift(2)
    df["demand_lag_4"] = grouped["units_demanded"].shift(4)
    
    # Revenue & Order count lags
    df["revenue_lag_1"] = grouped["total_revenue"].shift(1)
    df["order_count_lag_1"] = grouped["order_count"].shift(1)
    df["avg_price_lag_1"] = grouped["avg_unit_price"].shift(1)
    
    # -------------------------------------------------------------------------
    # Group B: Rolling Window Statistics (Strict shift(1) before rolling)
    # -------------------------------------------------------------------------
    shifted_demand = grouped["units_demanded"].shift(1)
    
    df["rolling_mean_2w"] = shifted_demand.groupby(df["category_name"]).transform(
        lambda s: s.rolling(window=2, min_periods=2).mean()
    )
    df["rolling_mean_4w"] = shifted_demand.groupby(df["category_name"]).transform(
        lambda s: s.rolling(window=4, min_periods=4).mean()
    )
    df["rolling_std_4w"] = shifted_demand.groupby(df["category_name"]).transform(
        lambda s: s.rolling(window=4, min_periods=4).std()
    )
    df["rolling_min_4w"] = shifted_demand.groupby(df["category_name"]).transform(
        lambda s: s.rolling(window=4, min_periods=4).min()
    )
    df["rolling_max_4w"] = shifted_demand.groupby(df["category_name"]).transform(
        lambda s: s.rolling(window=4, min_periods=4).max()
    )
    
    # -------------------------------------------------------------------------
    # Group C: Momentum & Velocity Signals
    # -------------------------------------------------------------------------
    df["demand_momentum_2w_4w"] = df["rolling_mean_2w"] - df["rolling_mean_4w"]
    df["demand_growth_ratio_1w_2w"] = (df["demand_lag_1"] + 1e-5) / (df["rolling_mean_2w"] + 1e-5)
    
    # -------------------------------------------------------------------------
    # Group D: Calendar & Temporal Signals
    # -------------------------------------------------------------------------
    df["month"] = df["week_start"].dt.month
    df["week_of_year"] = df["week_start"].dt.isocalendar().week.astype(int)
    df["is_month_start_week"] = (df["week_start"].dt.day <= 7).astype(int)
    
    # Drop current-week raw metrics so they cannot be accidentally used as features
    cols_to_drop = ["units_demanded", "total_revenue", "order_count", "avg_unit_price"]
    df = df.drop(columns=[c for c in cols_to_drop if c in df.columns])
    
    if drop_warmup:
        # Drop initial 4-week lookback period where lag_4 / rolling_4w are NaN
        initial_rows = len(df)
        df = df.dropna(subset=["demand_lag_4", "rolling_mean_4w"]).reset_index(drop=True)
        print(f"Dropped {initial_rows - len(df)} warmup rows across categories. Remaining rows: {len(df)}")
        
    return df


def audit_leakage(features_df: pd.DataFrame) -> bool:
    """
    Automated assertion suite ensuring zero future lookahead leakage.
    Raises AssertionError if any temporal hygiene rule is violated.
    """
    print("\n--- Running Automated Temporal Leakage Audit ---")
    
    # Audit 1: Lag 1 alignment check
    for cat in features_df["category_name"].unique():
        sub = features_df[features_df["category_name"] == cat].sort_values("week_start")
        for i in range(1, len(sub)):
            curr_lag1 = sub.iloc[i]["demand_lag_1"]
            prev_target = sub.iloc[i-1]["target"]
            assert np.isclose(curr_lag1, prev_target), (
                f"Leakage Audit FAILED for {cat} at week {sub.iloc[i]['week_start']}: "
                f"demand_lag_1 ({curr_lag1}) != prior actual ({prev_target})"
            )
            
    print("PASS 1/3: demand_lag_1 perfectly matches prior week actual (zero lookahead).")
    
    # Audit 2: Rolling mean exclusion check
    for cat in features_df["category_name"].unique():
        sub = features_df[features_df["category_name"] == cat].sort_values("week_start")
        for i in range(len(sub)):
            curr_rolling2 = sub.iloc[i]["rolling_mean_2w"]
            if i >= 2:
                expected_rolling2 = (sub.iloc[i-1]["target"] + sub.iloc[i-2]["target"]) / 2.0
                assert np.isclose(curr_rolling2, expected_rolling2), (
                    f"Leakage Audit FAILED: rolling_mean_2w ({curr_rolling2}) != ({expected_rolling2})"
                )
    print("PASS 2/3: rolling_mean_2w verified strictly over [W-2, W-1]; week W excluded.")
    
    # Audit 3: Perfect correlation check
    numeric_cols = features_df.select_dtypes(include=[np.number]).columns
    feature_cols = [c for c in numeric_cols if c not in ["target", "category_id"]]
    corrs = features_df[feature_cols].corrwith(features_df["target"])
    for col, r in corrs.items():
        assert abs(r) < 0.999, f"Leakage Audit FAILED: {col} has suspicious correlation {r:.4f} with target."
        
    print(f"PASS 3/3: Max feature-to-target correlation is {corrs.abs().max():.4f} ({corrs.abs().idxmax()}) - no label leaks.")
    print("Result: ALL TEMPORAL LEAKAGE AUDITS PASSED!\n")
    return True


def save_features(features_df: pd.DataFrame, output_path: Path = None) -> Path:
    """Persists the processed feature matrix to disk."""
    if output_path is None:
        out_dir = ROOT_DIR / "data" / "processed"
        out_dir.mkdir(parents=True, exist_ok=True)
        output_path = out_dir / "category_weekly_features.csv"
        
    features_df.to_csv(output_path, index=False)
    print(f"Successfully saved feature matrix to {output_path} ({len(features_df)} rows x {features_df.shape[1]} columns)")
    return output_path


if __name__ == "__main__":
    raw_df = load_raw_demand()
    feat_df = build_features(raw_df, drop_warmup=True)
    audit_leakage(feat_df)
    save_features(feat_df)
