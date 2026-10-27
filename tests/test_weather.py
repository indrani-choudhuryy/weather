import os
import sys
import unittest
from unittest.mock import MagicMock, patch

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import weather  # noqa: E402


def fake_response(payload):
    resp = MagicMock()
    resp.json.return_value = payload
    resp.raise_for_status.return_value = None
    return resp


FORECAST_PAYLOAD = {
    "current": {
        "time": "2026-10-27T12:00",
        "temperature_2m": 31.2,
        "apparent_temperature": 34.0,
        "relative_humidity_2m": 62,
        "wind_speed_10m": 12.5,
        "weather_code": 2,
        "is_day": 1,
    },
    "daily": {
        "time": ["2026-10-27", "2026-10-28"],
        "weather_code": [2, 61],
        "temperature_2m_max": [33.0, 30.5],
        "temperature_2m_min": [24.0, 23.5],
        "precipitation_sum": [0.0, 4.2],
    },
}


class DescribeCodeTests(unittest.TestCase):
    def test_known_code(self):
        self.assertEqual(weather.describe_code(0), ("Clear sky", "☀️"))

    def test_unknown_code(self):
        self.assertEqual(weather.describe_code(12345)[0], "Unknown")


class SearchCityTests(unittest.TestCase):
    @patch("weather.requests.get")
    def test_returns_places(self, mock_get):
        mock_get.return_value = fake_response({"results": [
            {"name": "Mumbai", "admin1": "Maharashtra", "country": "India", "latitude": 19.07, "longitude": 72.88},
        ]})
        places = weather.search_city("Mumbai")
        self.assertEqual(places[0]["name"], "Mumbai")
        self.assertEqual(places[0]["country"], "India")

    @patch("weather.requests.get")
    def test_no_results_returns_empty_list(self, mock_get):
        mock_get.return_value = fake_response({"generationtime_ms": 0.5})
        self.assertEqual(weather.search_city("zzzzzz"), [])

    def test_empty_name_raises(self):
        with self.assertRaises(weather.WeatherError):
            weather.search_city("   ")


class GetWeatherTests(unittest.TestCase):
    @patch("weather.requests.get")
    def test_parses_current_and_daily(self, mock_get):
        mock_get.return_value = fake_response(FORECAST_PAYLOAD)
        report = weather.get_weather(19.07, 72.88)
        self.assertEqual(report["current"]["temperature"], 31.2)
        self.assertTrue(report["current"]["is_day"])
        self.assertEqual(len(report["daily"]), 2)
        self.assertEqual(report["daily"][1]["precipitation"], 4.2)
        self.assertEqual(report["units"]["temp_symbol"], "°C")

    @patch("weather.requests.get")
    def test_imperial_units_sent_to_api(self, mock_get):
        mock_get.return_value = fake_response(FORECAST_PAYLOAD)
        report = weather.get_weather(40.7, -74.0, units="imperial")
        params = mock_get.call_args.kwargs["params"]
        self.assertEqual(params["temperature_unit"], "fahrenheit")
        self.assertEqual(report["units"]["wind_symbol"], "mph")

    @patch("weather.requests.get")
    def test_malformed_response_raises(self, mock_get):
        mock_get.return_value = fake_response({"current": {}})
        with self.assertRaises(weather.WeatherError):
            weather.get_weather(0, 0)

    def test_invalid_units_raises(self):
        with self.assertRaises(ValueError):
            weather.get_weather(0, 0, units="kelvin")


class ErrorHandlingTests(unittest.TestCase):
    @patch("weather.requests.get", side_effect=requests.exceptions.ConnectionError)
    def test_connection_error(self, _):
        with self.assertRaises(weather.WeatherError) as ctx:
            weather.search_city("Mumbai")
        self.assertIn("connect", str(ctx.exception).lower())

    @patch("weather.requests.get", side_effect=requests.exceptions.Timeout)
    def test_timeout(self, _):
        with self.assertRaises(weather.WeatherError) as ctx:
            weather.get_weather(0, 0)
        self.assertIn("too long", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()
