"""
Data ingestion for SENTINEL-KE.

Live sources wired up:
  - Open-Meteo: rainfall + temperature (free, no API key)
  - NASA MODIS NDVI via NASA POWER / AppEEARS (requires free NASA Earthdata token)

Stubbed sources (return placeholder/synthetic values until you connect them):
  - WASH indicators       -> wire to WASH Kenya / WHO/UNICEF JMP datasets or county reports
  - Mobility              -> wire to mobile network operator data, border-post counts, or
                             Google/Meta mobility-style proxies
  - Health system capacity -> wire to DHIS2 (Kenya's national health information system)
  - Disease case counts    -> wire to DHIS2 surveillance modules

Each stub is isolated in its own function so swapping in a real integration later
means editing one function, not the pipeline.
"""

import os
import datetime as dt
import requests

NASA_POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def fetch_weather(lat: float, lon: float, days: int = 14) -> dict:
    """Rainfall + temperature, last `days` days, from Open-Meteo (no key needed)."""
    end = dt.date.today()
    start = end - dt.timedelta(days=days)
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "daily": "precipitation_sum,temperature_2m_mean",
        "timezone": "Africa/Nairobi",
    }
    resp = requests.get(OPEN_METEO_URL, params=params, timeout=30)
    resp.raise_for_status()
    daily = resp.json()["daily"]
    rainfall = daily["precipitation_sum"]
    temps = daily["temperature_2m_mean"]
    return {
        "rainfall_mm_total_14d": sum(r for r in rainfall if r is not None),
        "rainfall_mm_latest": rainfall[-1] if rainfall else None,
        "temperature_c_mean": sum(t for t in temps if t is not None) / max(len(temps), 1),
    }


def fetch_ndvi(lat: float, lon: float) -> dict:
    """
    Vegetation index proxy via NASA POWER (uses surface data as a stand-in).
    For production-grade NDVI, switch to NASA AppEEARS / MODIS MOD13Q1 with an
    Earthdata token (set NASA_EARTHDATA_TOKEN env var) — left as a clear extension point.
    """
    token = os.environ.get("NASA_EARTHDATA_TOKEN")
    if not token:
        # Without a token we can't hit MODIS directly — return a neutral placeholder
        # so the pipeline still runs end-to-end. Replace this branch once you have
        # Earthdata credentials.
        return {"ndvi": 0.5, "ndvi_source": "placeholder_no_token"}

    # Real AppEEARS/MODIS call would go here once token is supplied.
    return {"ndvi": 0.5, "ndvi_source": "todo_real_modis_call"}


def fetch_wash(county: str) -> dict:
    """STUB: water access / sanitation / hygiene score (0-1, higher = better conditions)."""
    return {"wash_score": 0.6, "wash_source": "placeholder"}


def fetch_mobility(county: str) -> dict:
    """STUB: border crossings / market activity / movement index (0-1, higher = more movement)."""
    return {"mobility_score": 0.4, "mobility_source": "placeholder"}


def fetch_health_capacity(county: str) -> dict:
    """STUB: hospital beds / health workers / emergency supply adequacy (0-1, higher = better)."""
    return {"health_capacity_score": 0.5, "health_capacity_source": "placeholder"}


def fetch_data_quality(county: str) -> dict:
    """STUB: reporting completeness/timeliness confidence multiplier (0-1)."""
    return {"data_quality_score": 0.7, "data_quality_source": "placeholder"}


def fetch_all_for_county(name: str, coords: dict) -> dict:
    """Assemble the full raw feature dict for one county for today's run."""
    record = {"county": name, "run_date": dt.date.today().isoformat()}
    record.update(fetch_weather(coords["lat"], coords["lon"]))
    record.update(fetch_ndvi(coords["lat"], coords["lon"]))
    record.update(fetch_wash(name))
    record.update(fetch_mobility(name))
    record.update(fetch_health_capacity(name))
    record.update(fetch_data_quality(name))
    return record
