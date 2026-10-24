"""Погода через Open-Meteo (бесплатно, без ключа)."""

from . import http

# WMO-коды погоды → (описание, эмодзи)
WEATHER = {
    0: ("Ясно", "☀️"),
    1: ("Преимущественно ясно", "🌤️"),
    2: ("Переменная облачность", "⛅"),
    3: ("Пасмурно", "☁️"),
    45: ("Туман", "🌫️"),
    48: ("Изморозь", "🌫️"),
    51: ("Морось", "🌦️"),
    53: ("Морось", "🌦️"),
    55: ("Морось", "🌧️"),
    61: ("Небольшой дождь", "🌧️"),
    63: ("Дождь", "🌧️"),
    65: ("Сильный дождь", "🌧️"),
    71: ("Снег", "🌨️"),
    73: ("Снег", "🌨️"),
    75: ("Снегопад", "❄️"),
    77: ("Снег", "❄️"),
    80: ("Ливни", "🌧️"),
    81: ("Ливень", "🌧️"),
    82: ("Сильный ливень", "⛈️"),
    95: ("Гроза", "⛈️"),
    96: ("Гроза с градом", "⛈️"),
    99: ("Гроза с градом", "⛈️"),
}


def _desc(code):
    return WEATHER.get(code, ("—", ""))


def fetch(latitude, longitude, timezone):
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}&longitude={longitude}"
        "&current=temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m"
        "&daily=temperature_2m_max,temperature_2m_min,weather_code"
        f"&timezone={timezone}&forecast_days=1"
    )
    raw = http.get_json(url, timeout=20, retries=2)

    cur = raw.get("current", {})
    day = raw.get("daily", {})
    desc, icon = _desc(cur.get("weather_code", 0))
    highs = day.get("temperature_2m_max") or [0]
    lows = day.get("temperature_2m_min") or [0]
    return {
        "temp": round(cur.get("temperature_2m", 0)),
        "feels_like": round(cur.get("apparent_temperature", 0)),
        "humidity": cur.get("relative_humidity_2m"),
        "wind": round(cur.get("wind_speed_10m", 0), 1),
        "weather": desc,
        "icon": icon,
        "high": round(highs[0]),
        "low": round(lows[0]),
    }
