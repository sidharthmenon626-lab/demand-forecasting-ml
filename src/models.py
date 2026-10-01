"""
Forecasting Models for Weekly Demand Prediction.
Provides Scikit-Learn compatible baseline estimators and machine learning regressors.
"""

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.linear_model import Ridge, HuberRegressor
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor

class LastValueNaiveBaseline(BaseEstimator, RegressorMixin):
    """
    Persistence / Last-Value Naive Baseline:
    Predicts next week demand = last week demand (demand_lag_1).
    """
    def __init__(self, lag_col: str = "demand_lag_1"):
        self.lag_col = lag_col

    def fit(self, X, y=None):
        return self

    def predict(self, X):
        if isinstance(X, pd.DataFrame):
            return X[self.lag_col].values
        return X[:, 0]


class MovingAverageBaseline(BaseEstimator, RegressorMixin):
    """
    Moving Average Baseline:
    Predicts next week demand = prior 4-week moving average (rolling_mean_4w).
    """
    def __init__(self, ma_col: str = "rolling_mean_4w"):
        self.ma_col = ma_col

    def fit(self, X, y=None):
        return self

    def predict(self, X):
        if isinstance(X, pd.DataFrame):
            return X[self.ma_col].values
        return X[:, 1]


def get_model_candidates():
    """Returns dictionary of benchmarked baseline and ML models."""
    return {
        "Last-Value Naive": LastValueNaiveBaseline(lag_col="demand_lag_1"),
        "4-Week Moving Average": MovingAverageBaseline(ma_col="rolling_mean_4w"),
        "Huber Regressor (Robust ML)": HuberRegressor(epsilon=1.35, max_iter=1000),
        "Ridge Regressor": Ridge(alpha=50.0, random_state=42),
        "Random Forest": RandomForestRegressor(n_estimators=100, max_depth=3, min_samples_leaf=2, random_state=42),
        "XGBoost Regressor": XGBRegressor(n_estimators=40, max_depth=2, learning_rate=0.03, subsample=0.7, random_state=42)
    }
