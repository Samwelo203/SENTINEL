"""Shared configuration for SENTINEL-KE."""

# Six Nyanza region counties — coordinates are county-seat centroids.
# Swap/extend this list to monitor a different region.
COUNTIES = {
    "Kisumu": {"lat": -0.0917, "lon": 34.7680},
    "Siaya": {"lat": 0.0607, "lon": 34.2881},
    "Homa Bay": {"lat": -0.5273, "lon": 34.4571},
    "Migori": {"lat": -1.0634, "lon": 34.4731},
    "Kisii": {"lat": -0.6817, "lon": 34.7680},
    "Nyamira": {"lat": -0.5633, "lon": 34.9358},
}

# Diseases tracked — each gets its own trained model and risk score, since the
# environmental/health drivers differ (e.g. malaria tracks rainfall+temperature
# for mosquito breeding; cholera tracks rainfall+WASH for water contamination).
DISEASES = ["malaria", "cholera"]

RISK_THRESHOLDS = {
    "critical": 65,   # >= 65: critical alert
    "elevated": 40,   # 40-65: elevated risk, enhanced surveillance
    # < 40: normal, routine monitoring
}

FEATURE_DOMAINS = [
    "environmental",      # rainfall, temperature, NDVI trends
    "wash",                # water access, sanitation, hygiene
    "mobility",             # border crossings, market activity, movement
    "health_capacity",       # beds, health workers, supplies
    "data_quality",           # reporting completeness/delay confidence adjuster
]

