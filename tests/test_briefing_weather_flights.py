import pytest
import os
from grid.external_data import fetch_weather_data, fetch_flight_data

@pytest.mark.anyio
async def test_weather_and_flights_missing_credentials(monkeypatch):
    # Set keys to empty/missing
    monkeypatch.setenv("OPENWEATHER_API_KEY", "")
    monkeypatch.setenv("FLIGHTAWARE_API_KEY", "")

    weather_res = await fetch_weather_data()
    assert weather_res["provider"] == "openweather"
    assert weather_res["status"] == "blocked_missing_credentials"
    assert not weather_res["live"]
    assert weather_res["data"] is None

    flight_res = await fetch_flight_data()
    assert flight_res["provider"] == "flightaware"
    assert flight_res["status"] == "blocked_missing_credentials"
    assert not flight_res["live"]
    assert flight_res["data"] is None

@pytest.mark.anyio
async def test_weather_and_flights_placeholder_credentials(monkeypatch):
    # Set keys to placeholders
    monkeypatch.setenv("OPENWEATHER_API_KEY", "YOUR_OPENWEATHER_API_KEY")
    monkeypatch.setenv("FLIGHTAWARE_API_KEY", "aeroapi")

    weather_res = await fetch_weather_data()
    assert weather_res["status"] == "blocked_missing_credentials"
    assert weather_res["data"] is None

    flight_res = await fetch_flight_data()
    assert flight_res["status"] == "blocked_missing_credentials"
    assert flight_res["data"] is None
