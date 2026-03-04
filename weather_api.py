import logging
from typing import Any, Dict

import requests

WEATHER_URL = (
    "https://api.open-meteo.com/v1/forecast?latitude=53.37&longitude=-2.84"
    "&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,"
    "uv_index_max,wind_gusts_10m_max"
    "&hourly=temperature_2m,uv_index,apparent_temperature,precipitation_probability,"
    "precipitation,wind_speed_10m,wind_direction_10m,wind_gusts_10m,"
    "relative_humidity_2m,cloud_cover"
    "&models=ukmo_uk_deterministic_2km"
    "&current=temperature_2m,apparent_temperature,relative_humidity_2m,"
    "wind_speed_10m,wind_gusts_10m,wind_direction_10m"
    "&timezone=Europe/London&wind_speed_unit=mph&precipitation_unit=mm&forecast_hours=24"
)


def get_weather_data() -> Dict[str, Any]:
    """Fetch and return structured weather data.

    Returns:
        dict with keys: current, hourly, daily, timezone
    Raises:
        RuntimeError on network/API/format errors
    """
    try:
        response = requests.get(WEATHER_URL, timeout=20)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        logging.exception("Weather API request failed")
        raise RuntimeError(f"Weather API request failed: {exc}") from exc

    for required in ("current", "hourly", "daily"):
        if required not in payload:
            raise RuntimeError(f"Weather API response missing '{required}'")

    return {
        "current": payload["current"],
        "hourly": payload["hourly"],
        "daily": payload["daily"],
        "timezone": payload.get("timezone", "Europe/London"),
    }
