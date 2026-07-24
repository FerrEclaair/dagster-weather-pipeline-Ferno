from unittest.mock import Mock, patch

import pytest
import requests

import source


def _fake_daily_payload(days=5):
    dates = [f"2026-01-0{i + 1}" for i in range(days)]
    daily = {"time": dates}
    for var in source.DAILY_VARS:
        daily[var] = [1.0] * days
    return {"daily": daily}


def test_fetch_historical_weather_returns_dataframe():
    fake_response = Mock()
    fake_response.json.return_value = _fake_daily_payload(days=5)
    fake_response.raise_for_status.return_value = None

    with patch("source.requests.get", return_value=fake_response) as mock_get:
        result = source.fetch_historical_weather(days_back=5)

    assert len(result) == 5
    assert "date" in result.columns
    for var in source.DAILY_VARS:
        assert var in result.columns
    mock_get.assert_called_once()
    assert mock_get.call_args.args[0] == source.BASE_URL


def test_fetch_historical_weather_raises_source_unavailable_on_network_error():
    with patch("source.requests.get", side_effect=requests.ConnectionError("boom")):
        with pytest.raises(source.SourceUnavailableError):
            source.fetch_historical_weather()
