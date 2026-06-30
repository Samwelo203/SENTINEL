"""
Feature engineering: raw fetched data -> 25-feature vector across 5 domains.

Domain breakdown (5 features each = 25 total), matching the design doc:
  environmental, wash, mobility, health_capacity, data_quality
"""

import pandas as pd

FEATURE_COLUMNS = [
    # Environmental (5)
    "rainfall_mm_total_14d", "rainfall_mm_latest", "temperature_c_mean",
    "ndvi", "rainfall_anomaly",
    # WASH (5)
    "wash_score", "water_access_proxy", "sanitation_proxy",
    "hygiene_proxy", "wash_trend",
    # Mobility (5)
    "mobility_score", "border_crossing_proxy", "market_activity_proxy",
    "population_movement_proxy", "mobility_trend",
    # Health capacity (5)
    "health_capacity_score", "beds_proxy", "health_workers_proxy",
    "supply_proxy", "capacity_trend",
    # Data quality (5)
    "data_quality_score", "reporting_completeness", "reporting_timeliness",
    "source_agreement", "quality_trend",
]


def build_feature_row(raw: dict, history: pd.DataFrame | None = None) -> dict:
    """
    Expand a single raw record (one county, one day) into the full 25-feature row.
    `history` (optional) is that county's recent rows, used to compute trend/anomaly
    features; without history, trend features default to 0 (neutral).
    """
    row = {}

    # Environmental
    row["rainfall_mm_total_14d"] = raw.get("rainfall_mm_total_14d", 0.0)
    row["rainfall_mm_latest"] = raw.get("rainfall_mm_latest", 0.0)
    row["temperature_c_mean"] = raw.get("temperature_c_mean", 0.0)
    row["ndvi"] = raw.get("ndvi", 0.5)
    row["rainfall_anomaly"] = _trend(history, "rainfall_mm_total_14d", raw["rainfall_mm_total_14d"])

    # WASH
    row["wash_score"] = raw.get("wash_score", 0.5)
    row["water_access_proxy"] = raw.get("wash_score", 0.5)
    row["sanitation_proxy"] = raw.get("wash_score", 0.5)
    row["hygiene_proxy"] = raw.get("wash_score", 0.5)
    row["wash_trend"] = _trend(history, "wash_score", raw["wash_score"])

    # Mobility
    row["mobility_score"] = raw.get("mobility_score", 0.5)
    row["border_crossing_proxy"] = raw.get("mobility_score", 0.5)
    row["market_activity_proxy"] = raw.get("mobility_score", 0.5)
    row["population_movement_proxy"] = raw.get("mobility_score", 0.5)
    row["mobility_trend"] = _trend(history, "mobility_score", raw["mobility_score"])

    # Health capacity
    row["health_capacity_score"] = raw.get("health_capacity_score", 0.5)
    row["beds_proxy"] = raw.get("health_capacity_score", 0.5)
    row["health_workers_proxy"] = raw.get("health_capacity_score", 0.5)
    row["supply_proxy"] = raw.get("health_capacity_score", 0.5)
    row["capacity_trend"] = _trend(history, "health_capacity_score", raw["health_capacity_score"])

    # Data quality
    row["data_quality_score"] = raw.get("data_quality_score", 0.5)
    row["reporting_completeness"] = raw.get("data_quality_score", 0.5)
    row["reporting_timeliness"] = raw.get("data_quality_score", 0.5)
    row["source_agreement"] = raw.get("data_quality_score", 0.5)
    row["quality_trend"] = _trend(history, "data_quality_score", raw["data_quality_score"])

    return row


def _trend(history: pd.DataFrame | None, col: str, current: float) -> float:
    if history is None or history.empty or col not in history.columns:
        return 0.0
    past_mean = history[col].mean()
    if past_mean == 0:
        return 0.0
    return float((current - past_mean) / past_mean)
