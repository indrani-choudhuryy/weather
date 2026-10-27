"""Thin client for the Open-Meteo APIs (geocoding + forecast). No API key required."""

import requests

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT_SECONDS = 10

# WMO weather interpretation codes -> (description, emoji)
# https://open-meteo.com/en/docs (see "WMO Weather interpretation codes")
WEATHER_CODES = {
    0: ("Clear sky", "☀️"),
    1: ("Mainly clear", "🌤️"),
    2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁️"),
    45: ("Fog", "🌫️"),
    48: ("Depositing rime fog", "🌫️"),
    51: ("Light drizzle", "🌦️"),
    53: ("Moderate drizzle", "🌦️"),
    55: ("Dense drizzle", "🌧️"),
    56: ("Light freezing drizzle", "🌧️"),
    57: ("Dense freezing drizzle", "🌧️"),
    61: ("Slight rain", "🌦️"),
    63: ("Moderate rain", "🌧️"),
    65: ("Heavy rain", "🌧️"),
    66: ("Light freezing rain", "🌧️"),
    67: ("Heavy freezing rain", "🌧️"),
    71: ("Slight snow", "🌨️"),
    73: ("Moderate snow", "🌨️"),
    75: ("Heavy snow", "❄️"),
    77: ("Snow grains", "❄️"),
    80: ("Slight rain showers", "🌦️"),
    81: ("Moderate rain showers", "🌧️"),
    82: ("Violent rain showers", "⛈️"),
    85: ("Slight snow showers", "🌨️"),
    86: ("Heavy snow showers", "❄️"),
    95: ("Thunderstorm", "⛈️"),
    96: ("Thunderstorm with slight hail", "⛈️"),
    99: ("Thunderstorm with heavy hail", "⛈️"),
}

UNITS = {
    "metric": {"temperature_unit": "celsius", "wind_speed_unit": "kmh",
               "temp_symbol": "°C", "wind_symbol": "km/h", "precip_symbol": "mm"},
    "imperial": {"temperature_unit": "fahrenheit", "wind_speed_unit": "mph",
                 "temp_symbol": "°F", "wind_symbol": "mph", "precip_symbol": "mm"},
}


class WeatherError(Exception):
    """Raised when the API cannot be reached or returns something unexpected."""


def describe_code(code: int) -> tuple[str, str]:
    """Map a WMO weather code to a (description, emoji) pair."""
    return WEATHER_CODES.get(code, ("Unknown", "❓"))


def _get_json(url: str, params: dict) -> dict:
    try:
        response = requests.get(url, params=params, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout as exc:
        raise WeatherError("The weather service took too long to respond. Please try again.") from exc
    except requests.exceptions.ConnectionError as exc:
        raise WeatherError("Could not connect to the weather service. Check your internet connection.") from exc
    except requests.exceptions.HTTPError as exc:
        raise WeatherError(f"The weather service returned an error: {exc}") from exc
    except ValueError as exc:
        raise WeatherError("The weather service returned an invalid response.") from exc


def search_city(name: str, count: int = 5) -> list[dict]:
    """Find up to `count` places matching `name`. Returns an empty list if nothing matches."""
    name = name.strip()
    if not name:
        raise WeatherError("Please enter a city name.")

    data = _get_json(GEOCODE_URL, {"name": name, "count": count, "language": "en", "format": "json"})
    results = data.get("results") or []
    return [
        {
            "name": r.get("name", ""),
            "region": r.get("admin1", ""),
            "country": r.get("country", ""),
            "latitude": r["latitude"],
            "longitude": r["longitude"],
        }
        for r in results
    ]


def get_weather(latitude: float, longitude: float, units: str = "metric", days: int = 7) -> dict:
    """
    Fetch current conditions and a daily forecast.

    Returns a dict with keys: "current" (dict), "daily" (list of dicts), "units" (dict of symbols).
    """
    if units not in UNITS:
        raise ValueError("units must be 'metric' or 'imperial'")
    u = UNITS[units]

    data = _get_json(FORECAST_URL, {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,"
                   "weather_code,wind_speed_10m,is_day",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "auto",
        "forecast_days": days,
        "temperature_unit": u["temperature_unit"],
        "wind_speed_unit": u["wind_speed_unit"],
    })

    try:
        cur = data["current"]
        daily = data["daily"]
        current = {
            "temperature": cur["temperature_2m"],
            "feels_like": cur["apparent_temperature"],
            "humidity": cur["relative_humidity_2m"],
            "wind_speed": cur["wind_speed_10m"],
            "weather_code": cur["weather_code"],
            "is_day": bool(cur["is_day"]),
            "time": cur["time"],
        }
        forecast = [
            {
                "date": daily["time"][i],
                "weather_code": daily["weather_code"][i],
                "temp_max": daily["temperature_2m_max"][i],
                "temp_min": daily["temperature_2m_min"][i],
                "precipitation": daily["precipitation_sum"][i],
            }
            for i in range(len(daily["time"]))
        ]
    except (KeyError, IndexError, TypeError) as exc:
        raise WeatherError("Unexpected data format from the weather service.") from exc

    return {"current": current, "daily": forecast, "units": u}
