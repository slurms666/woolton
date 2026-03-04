from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Tuple


def _cardinal_from_degrees(degrees: float) -> str:
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    idx = round(degrees / 45) % 8
    return directions[idx]


def _safe_get(lst: List, idx: int, default=None):
    return lst[idx] if 0 <= idx < len(lst) else default


def _find_hour_index(hourly: Dict, current_time_iso: str) -> int:
    times = hourly.get("time", [])
    current_hour = current_time_iso[:13] + ":00"
    if current_hour in times:
        return times.index(current_hour)
    return 0


def format_current_conditions(data: Dict) -> str:
    current = data["current"]
    hourly = data["hourly"]
    idx = _find_hour_index(hourly, current.get("time", ""))
    uv = _safe_get(hourly.get("uv_index", []), idx, 0)

    wind_dir = _cardinal_from_degrees(float(current.get("wind_direction_10m", 0)))

    return (
        "📍 Current Conditions\n"
        f"🌡 Temp: {round(current.get('temperature_2m', 0))}°C "
        f"(feels like {round(current.get('apparent_temperature', 0))}°C)\n"
        f"💧 Humidity: {round(current.get('relative_humidity_2m', 0))}%\n"
        f"🌬 Wind: {round(current.get('wind_speed_10m', 0))} mph {wind_dir} "
        f"(gusts {round(current.get('wind_gusts_10m', 0))} mph)\n"
        f"☀️ UV Index: {round(uv)}"
    )


def format_daily_summary(data: Dict) -> str:
    daily = data["daily"]
    return (
        "📈 Today\n"
        f"🔺 High: {round(daily['temperature_2m_max'][0])}°C\n"
        f"🔻 Low: {round(daily['temperature_2m_min'][0])}°C\n"
        f"🌧 Max rain chance: {round(daily['precipitation_probability_max'][0])}%\n"
        f"🌬 Max gusts: {round(daily['wind_gusts_10m_max'][0])} mph\n"
        f"☀️ Max UV: {round(daily['uv_index_max'][0])}"
    )


def format_rain_timeline(data: Dict) -> Tuple[str, List[Tuple[str, float]]]:
    hourly = data["hourly"]
    current_time = data["current"].get("time", "")
    start_idx = _find_hour_index(hourly, current_time)

    times = hourly.get("time", [])[start_idx : start_idx + 12]
    probs = hourly.get("precipitation_probability", [])[start_idx : start_idx + 12]

    rain_points: List[Tuple[str, float]] = []
    lines = ["🌧 Rain risk (next 12 hours)"]
    for t, p in zip(times, probs):
        hhmm = t[11:16]
        rain_points.append((hhmm, float(p)))
        lines.append(f"{hhmm} {round(p)}%")

    return "\n".join(lines), rain_points


def detect_delivery_rain(data: Dict) -> Optional[str]:
    hourly = data["hourly"]
    times = hourly.get("time", [])
    probs = hourly.get("precipitation_probability", [])

    hits = []
    for t, p in zip(times, probs):
        dt = datetime.fromisoformat(t)
        if ((dt.hour == 8 and dt.minute >= 30) or (9 <= dt.hour <= 13)) and float(p) > 40:
            hits.append((t[11:16], float(p)))

    if not hits:
        return None

    start_time = hits[0][0]
    end_time = hits[-1][0]
    if start_time == end_time:
        window = start_time
    else:
        window = f"{start_time}–{end_time}"

    return "🚨 Delivery Round Alert\n" f"Rain likely between {window}"


def generate_practical_advice(data: Dict) -> str:
    current = data["current"]
    daily = data["daily"]

    tips: List[str] = []

    if float(current.get("temperature_2m", 0)) < 7:
        tips.append("Warm layers recommended.")
    if float(daily["wind_gusts_10m_max"][0]) > 20:
        tips.append("Breezy conditions expected.")
    if float(daily["precipitation_probability_max"][0]) > 50:
        tips.append("Take waterproofs.")
    if float(daily["uv_index_max"][0]) >= 4:
        tips.append("Consider sunscreen for longer outdoor exposure.")

    if not tips:
        tips.append("Conditions look fairly manageable for delivery rounds.")

    return "👕 Practical Advice\n" + " ".join(tips)


def format_weather_message(weather_data: Dict) -> str:
    header = "📮 Woolton DO Weather – L25 Area\n🕖 Daily briefing – 07:00"
    current = format_current_conditions(weather_data)
    daily = format_daily_summary(weather_data)
    rain_timeline, _ = format_rain_timeline(weather_data)
    alert = detect_delivery_rain(weather_data)
    advice = generate_practical_advice(weather_data)

    # Simple one-line takeaway
    max_rain = round(weather_data["daily"]["precipitation_probability_max"][0])
    max_gust = round(weather_data["daily"]["wind_gusts_10m_max"][0])
    takeaway = (
        "📌 Takeaway\n"
        f"Max rain chance {max_rain}% today with gusts up to {max_gust} mph."
    )

    parts = [header, current, daily, rain_timeline]
    if alert:
        parts.append(alert)
    parts.extend([advice, takeaway])

    return "\n\n".join(parts)
