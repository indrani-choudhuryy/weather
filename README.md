# Weather App 🌤️

A small weather dashboard that shows **current conditions** and a **7-day forecast** for any city.
It uses the free [Open-Meteo](https://open-meteo.com/) APIs, so **no API key or signup is required**.

## Features

- City search with a location picker when several places share the same name
- Current temperature, "feels like", humidity, wind speed and conditions
- 7-day forecast table (high, low, rainfall) plus a temperature chart
- Metric (°C, km/h) and imperial (°F, mph) units
- Friendly error messages for unknown cities, timeouts and network failures
- Responses cached for 10 minutes to avoid unnecessary API calls

## Tech stack

Python, Requests, Streamlit, Pandas

## Run locally

```bash
python3 -m venv venv
source venv/bin/activate      # on Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Run the tests

```bash
python3 -m unittest discover -s tests -v
```

The tests mock the HTTP layer, so they run offline.

## Project structure

```
weather.py           # API client: geocoding, forecast, weather-code mapping, error handling
app.py               # Streamlit UI
tests/test_weather.py
requirements.txt
```

## How it works

1. The city name is sent to the Open-Meteo **Geocoding API**, which returns matching places with coordinates.
2. The chosen coordinates are sent to the **Forecast API**, which returns current weather and daily data.
3. WMO weather codes (e.g. `61` = slight rain) are mapped to readable descriptions and emojis.
4. `weather.py` raises a single `WeatherError` for any API failure, so the UI only has to handle one exception type.

## Possible improvements

- Hourly forecast view
- Save favourite cities
- Auto-detect the user's location
- Weather alerts and air-quality data (Open-Meteo also offers an air-quality API)
