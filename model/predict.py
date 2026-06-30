"""Run the trained model on today's features, with SHAP explanations."""

import os
import sys

import xgboost as xgb
import shap
import pandas as pd

# features.py lives in ../pipeline relative to this file, not in this folder,
# so it must be added to sys.path explicitly before importing it.
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pipeline"))

from features import FEATURE_COLUMNS
from config import RISK_THRESHOLDS


def load_model(path: str) -> xgb.XGBClassifier:
    model = xgb.XGBClassifier()
    model.load_model(path)
    return model


def predict_with_explanation(model: xgb.XGBClassifier, feature_row: dict) -> dict:
    X = pd.DataFrame([feature_row])[FEATURE_COLUMNS]
    risk_score = float(model.predict_proba(X)[0, 1] * 100)

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)
    shap_row = shap_values[0] if not isinstance(shap_values, list) else shap_values[0][0]

    driver_impact = sorted(
        zip(FEATURE_COLUMNS, shap_row), key=lambda x: abs(x[1]), reverse=True
    )
    top_drivers = [name for name, _ in driver_impact[:5]]

    if risk_score >= RISK_THRESHOLDS["critical"]:
        alert_level = "critical"
    elif risk_score >= RISK_THRESHOLDS["elevated"]:
        alert_level = "elevated"
    else:
        alert_level = "normal"

    return {
        "risk_score": round(risk_score, 1),
        "alert_level": alert_level,
        "top_drivers": top_drivers,
        "shap_values": {name: float(val) for name, val in driver_impact},
        "recommended_actions": recommend_actions(alert_level, top_drivers),
    }


def generate_explanation(county: str, disease: str, result: dict, raw: dict) -> str:
    """
    Produce a short, human-readable explanation of the score, built directly from
    the model's own SHAP drivers and the disease's known risk pathway — not a
    separate AI call, but a templated narrative grounded in the actual prediction
    so officials can see *why* without needing to read a SHAP table themselves.
    """
    score = result["risk_score"]
    level = result["alert_level"]
    drivers = result["top_drivers"][:3]

    driver_phrases = {
        "rainfall_mm_total_14d": "recent rainfall totals",
        "rainfall_anomaly": "rainfall running above normal for the area",
        "temperature_c_mean": "average temperatures",
        "ndvi": "vegetation/standing-water conditions",
        "wash_score": "water, sanitation and hygiene conditions",
        "mobility_score": "population movement levels",
        "health_capacity_score": "local health system capacity",
        "data_quality_score": "completeness of recent reporting",
    }
    named_drivers = [driver_phrases.get(d, d.replace("_", " ")) for d in drivers]
    driver_text = ", ".join(named_drivers[:-1]) + (
        f", and {named_drivers[-1]}" if len(named_drivers) > 1 else named_drivers[0]
    )

    level_phrase = {
        "critical": "is at critical risk",
        "elevated": "shows elevated risk",
        "normal": "is at normal/routine risk",
    }[level]

    return (
        f"{county} {level_phrase} for {disease} ({score}%), driven mainly by "
        f"{driver_text}. This estimate reflects current environmental and health-system "
        f"conditions, not a confirmed outbreak."
    )


def estimate_reported_cases(disease: str, risk_score: float, seed_key: str) -> dict:
    """
    PLACEHOLDER: synthetic, illustrative case counts correlated with the risk score,
    since no live DHIS2/surveillance case-count feed is connected yet. Replace this
    function with a real DHIS2 query once credentials are available — see README.
    """
    import hashlib
    h = int(hashlib.sha256(seed_key.encode()).hexdigest(), 16) % 1000
    base = {"malaria": 40, "cholera": 5}.get(disease, 10)
    noise = (h % 20) - 10
    cases = max(0, round(base * (risk_score / 50) + noise))
    return {"reported_cases": cases, "cases_source": "placeholder_synthetic"}


def recommend_actions(alert_level: str, top_drivers: list[str]) -> list[str]:
    actions = []
    if alert_level == "critical":
        actions.append("Preposition oral rehydration salts, IV fluids, cholera kits, and malaria drugs now.")
        actions.append("Alert county Rapid Response Team and brief neighboring counties.")
    elif alert_level == "elevated":
        actions.append("Increase surveillance reporting frequency for this county.")
        actions.append("Review supply stock levels against the elevated-risk threshold.")
    else:
        actions.append("Continue routine monitoring; no additional action required.")

    driver_actions = {
        "rainfall_mm_total_14d": "Inspect drainage and water sources for contamination risk after heavy rainfall.",
        "rainfall_anomaly": "Investigate unusual rainfall pattern versus county baseline.",
        "wash_score": "Coordinate with WASH partners on water/sanitation gaps.",
        "mobility_score": "Coordinate cross-border screening given elevated population movement.",
        "health_capacity_score": "Assess bed and staffing capacity; request reinforcement if strained.",
        "data_quality_score": "Follow up with reporting facilities — confidence in this score is reduced by data gaps.",
    }
    for driver in top_drivers:
        if driver in driver_actions:
            actions.append(driver_actions[driver])
    return actions