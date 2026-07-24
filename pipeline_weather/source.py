from datetime import date, timedelta

import pandas as pd
import requests

BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

# Jakarta, Indonesia by default — change lat/lon for a different city.
DEFAULT_LAT = -6.2088
DEFAULT_LON = 106.8456

DAILY_VARS = [
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "windspeed_10m_max",
    "relative_humidity_2m_mean",
    "surface_pressure_mean",
    "cloudcover_mean",
]


class SourceUnavailableError(Exception):
    """Raised when archive-api.open-meteo.com cannot be reached."""


def fetch_historical_weather(
    lat: float = DEFAULT_LAT,
    lon: float = DEFAULT_LON,
    days_back: int = 730,
) -> pd.DataFrame:
    """Fetch `days_back` days of daily historical weather ending yesterday
    (the archive API has a short delay before today's data is available).
    """
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=days_back)

    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "daily": ",".join(DAILY_VARS),
        "timezone": "auto",
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise SourceUnavailableError(
            "Could not reach archive-api.open-meteo.com — check your internet connection"
        ) from exc

    payload = response.json()
    df = pd.DataFrame(payload["daily"]).rename(columns={"time": "date"})
    df["date"] = pd.to_datetime(df["date"])
    return df
