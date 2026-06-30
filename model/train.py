"""
Train the XGBoost outbreak-risk model.

IMPORTANT — read this before trusting any predictions:
This script trains on SYNTHETIC labels generated from documented epidemiological
relationships (e.g., heavy rainfall + poor WASH + low health capacity -> higher
cholera/diarrheal risk), because no real historical outbreak-labeled dataset is
wired in yet. This lets the full pipeline run end-to-end today.

Before this system is used for real decisions, replace `generate_synthetic_training_data()`
with actual historical data: county-level outbreak dates/case counts from DHIS2,
matched against historical weather/WASH/mobility/capacity records for the same dates.
That is the single most important step to make SENTINEL-KE's predictions trustworthy.
"""

import os
import sys

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
import joblib

# features.py lives in ../pipeline relative to this file, not in this folder,
# so it must be added to sys.path explicitly before importing it.
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pipeline"))

from features import FEATURE_COLUMNS


def generate_synthetic_training_data(disease: str, n_samples: int = 5000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    data = {col: rng.uniform(0, 1, n_samples) for col in FEATURE_COLUMNS}
    df = pd.DataFrame(data)

    # Rescale a few columns to realistic ranges
    df["rainfall_mm_total_14d"] *= 200
    df["rainfall_mm_latest"] *= 40
    df["temperature_c_mean"] = 18 + df["temperature_c_mean"] * 18
    for c in ["rainfall_anomaly", "wash_trend", "mobility_trend", "capacity_trend", "quality_trend"]:
        df[c] = (df[c] - 0.5) * 2  # center anomalies/trends around 0

    if disease == "malaria":
        # Malaria risk tracks rainfall + warm temperature (mosquito breeding conditions)
        # and vegetation (standing water/breeding sites), tempered by health capacity.
        risk_logit = (
            0.015 * df["rainfall_mm_total_14d"]
            + 1.3 * df["rainfall_anomaly"].clip(lower=0)
            + 0.08 * (df["temperature_c_mean"] - 25).clip(lower=0)
            + 1.2 * df["ndvi"]
            - 1.5 * df["health_capacity_score"]
            - 0.8 * df["data_quality_score"]
            - 1.2
        )
    elif disease == "cholera":
        # Cholera risk tracks heavy rainfall/flooding + poor WASH + population movement.
        risk_logit = (
            0.02 * df["rainfall_mm_total_14d"]
            + 1.6 * df["rainfall_anomaly"].clip(lower=0)
            - 2.2 * df["wash_score"]
            + 1.5 * df["mobility_score"]
            - 1.5 * df["health_capacity_score"]
            - 1.0 * df["data_quality_score"]
            - 1.0
        )
    else:
        raise ValueError(f"Unknown disease: {disease}")

    prob = 1 / (1 + np.exp(-risk_logit))
    df["outbreak"] = rng.binomial(1, prob)
    return df


def train_and_save(disease: str, output_path: str = None):
    if output_path is None:
        output_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), f"model_{disease}.json"
        )
    df = generate_synthetic_training_data(disease)
    X = df[FEATURE_COLUMNS]
    y = df["outbreak"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric="auc",
    )
    model.fit(X_train, y_train)

    auc = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])
    print(f"[{disease}] Validation AUC: {auc:.3f}")

    model.save_model(output_path)
    return model, auc


if __name__ == "__main__":
    for disease in ["malaria", "cholera"]:
        train_and_save(disease)
