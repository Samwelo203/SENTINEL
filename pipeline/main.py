"""
Main daily pipeline entrypoint, run by a GitHub Actions scheduled workflow.

Flow: for each county -> fetch raw data once -> engineer features once
      -> for each disease -> load that disease's model -> predict + explain
      -> write docs/data/latest.json (nested by county -> disease)
      -> append to docs/data/history.json (flat list, one row per county+disease+day).
"""

import os
import sys
import json
import datetime as dt

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "model"))

from config import COUNTIES, DISEASES
from data_sources import fetch_all_for_county
from features import build_feature_row
from predict import load_model, predict_with_explanation, generate_explanation, estimate_reported_cases

ROOT = os.path.join(os.path.dirname(__file__), "..")
MODEL_DIR = os.path.join(ROOT, "model")
LATEST_PATH = os.path.join(ROOT, "docs", "data", "latest.json")
HISTORY_PATH = os.path.join(ROOT, "docs", "data", "history.json")

MAX_HISTORY_DAYS = 180  # keep file size sane; ~6 months of daily runs


def load_json(path: str, default):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default


def run():
    models = {d: load_model(os.path.join(MODEL_DIR, f"model_{d}.json")) for d in DISEASES}
    today = dt.date.today().isoformat()

    history = load_json(HISTORY_PATH, [])
    latest = {}

    for county, coords in COUNTIES.items():
        raw = fetch_all_for_county(county, coords)
        feature_row = build_feature_row(raw, history=None)  # extend to use real history later
        latest[county] = {}

        for disease in DISEASES:
            result = predict_with_explanation(models[disease], feature_row)
            cases = estimate_reported_cases(disease, result["risk_score"], f"{county}-{disease}-{today}")
            explanation = generate_explanation(county, disease, result, raw)

            record = {
                "run_date": today,
                "county": county,
                "disease": disease,
                "risk_score": result["risk_score"],
                "alert_level": result["alert_level"],
                "rainfall_mm": raw.get("rainfall_mm_total_14d"),
                "temperature_c": raw.get("temperature_c_mean"),
                "ndvi": raw.get("ndvi"),
                "wash_score": raw.get("wash_score"),
                "mobility_score": raw.get("mobility_score"),
                "health_capacity_score": raw.get("health_capacity_score"),
                "data_quality_score": raw.get("data_quality_score"),
                "top_drivers": result["top_drivers"],
                "recommended_actions": result["recommended_actions"],
                "explanation": explanation,
                **cases,
            }

            history.append(record)
            latest[county][disease] = record
            print(f"[{county}/{disease}] risk_score={result['risk_score']} alert={result['alert_level']}")

    # Drop history older than the retention window, keyed off run_date
    cutoff = (dt.date.today() - dt.timedelta(days=MAX_HISTORY_DAYS)).isoformat()
    history = [r for r in history if r["run_date"] >= cutoff]

    os.makedirs(os.path.dirname(LATEST_PATH), exist_ok=True)
    with open(LATEST_PATH, "w") as f:
        json.dump(latest, f, indent=2)
    with open(HISTORY_PATH, "w") as f:
        json.dump(history, f, indent=2)

    print(f"Pipeline complete: {len(latest)} counties x {len(DISEASES)} diseases for {today}.")


if __name__ == "__main__":
    run()
