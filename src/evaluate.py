"""
Time-Series Cross-Validation and Evaluation Engine.
Implements temporal expanding-window evaluation to prevent evaluation-time lookahead leakage.
"""

import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error

def compute_wmape(y_true, y_pred) -> float:
    """Weighted Mean Absolute Percentage Error (percentage scale 0-100)."""
    denom = np.sum(np.abs(y_true))
    if denom == 0:
        return 0.0
    return (np.sum(np.abs(y_true - y_pred)) / denom) * 100.0


def evaluate_time_series_cv(df: pd.DataFrame, models: dict, n_splits: int = 5):
    """
    Evaluates models across temporal folds using expanding windows on calendar weeks.
    
    Parameters:
        df: Feature DataFrame containing 'week_start', 'category_name', 'target', and feature columns.
        models: Dictionary of model name -> model instance.
        n_splits: Number of temporal test folds (weeks).
        
    Returns:
        results_df: Summary DataFrame of Mean & Std WMAPE, RMSE, MAE, and % Lift vs Naive.
        predictions_df: Fold-by-fold predictions for residual analysis.
    """
    # Unique chronological weeks
    unique_weeks = sorted(df["week_start"].unique())
    if len(unique_weeks) < n_splits + 2:
        n_splits = max(2, len(unique_weeks) - 2)
        
    # Test weeks are the last n_splits weeks
    test_weeks = unique_weeks[-n_splits:]
    
    # Feature columns (exclude identifiers and target)
    meta_cols = ["week_start", "category_id", "category_name", "target"]
    feature_cols = [c for c in df.columns if c not in meta_cols]
    
    all_fold_metrics = []
    all_preds = []
    
    for fold_idx, test_wk in enumerate(test_weeks):
        train_df = df[df["week_start"] < test_wk].copy()
        test_df = df[df["week_start"] == test_wk].copy()
        
        X_train, y_train = train_df[feature_cols], train_df["target"]
        X_test, y_test = test_df[feature_cols], test_df["target"]
        
        fold_record = {"fold": fold_idx + 1, "test_week": str(test_wk)[:10]}
        
        for name, model in models.items():
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            preds = np.clip(preds, a_min=0, a_max=None) # Demand is non-negative
            
            wmape = compute_wmape(y_test.values, preds)
            rmse = np.sqrt(mean_squared_error(y_test.values, preds))
            mae = mean_absolute_error(y_test.values, preds)
            
            fold_record[f"{name}_wmape"] = wmape
            fold_record[f"{name}_rmse"] = rmse
            fold_record[f"{name}_mae"] = mae
            
            # Save predictions for plotting
            for cat, true_val, pred_val in zip(test_df["category_name"], y_test.values, preds):
                all_preds.append({
                    "fold": fold_idx + 1,
                    "week_start": test_wk,
                    "category_name": cat,
                    "model": name,
                    "actual": true_val,
                    "predicted": pred_val,
                    "abs_error": abs(true_val - pred_val)
                })
                
        all_fold_metrics.append(fold_record)
        
    folds_df = pd.DataFrame(all_fold_metrics)
    preds_df = pd.DataFrame(all_preds)
    
    # Aggregate across folds
    summary_rows = []
    naive_wmape = folds_df["Last-Value Naive_wmape"].mean()
    naive_rmse = folds_df["Last-Value Naive_rmse"].mean()
    
    for name in models.keys():
        mean_wmape = folds_df[f"{name}_wmape"].mean()
        std_wmape = folds_df[f"{name}_wmape"].std()
        mean_rmse = folds_df[f"{name}_rmse"].mean()
        std_rmse = folds_df[f"{name}_rmse"].std()
        mean_mae = folds_df[f"{name}_mae"].mean()
        
        # Lift is % error reduction vs Last-Value Naive (positive is improvement)
        wmape_lift = ((naive_wmape - mean_wmape) / naive_wmape) * 100.0
        rmse_lift = ((naive_rmse - mean_rmse) / naive_rmse) * 100.0
        
        summary_rows.append({
            "Model": name,
            "Mean_WMAPE_pct": round(mean_wmape, 2),
            "Std_WMAPE_pct": round(std_wmape, 2),
            "Mean_RMSE": round(mean_rmse, 2),
            "Std_RMSE": round(std_rmse, 2),
            "Mean_MAE": round(mean_mae, 2),
            "WMAPE_Lift_pct": round(wmape_lift, 2),
            "RMSE_Lift_pct": round(rmse_lift, 2)
        })
        
    summary_df = pd.DataFrame(summary_rows).sort_values("Mean_WMAPE_pct")
    return summary_df, preds_df, folds_df
