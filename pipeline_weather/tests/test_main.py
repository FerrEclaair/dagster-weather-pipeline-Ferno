from unittest.mock import patch

import pandas as pd
from dagster import materialize

import db
import source
from main import model_quality_check, raw_weather_data, rain_predictions, trained_rain_model, weather_features

N = 20
FAKE_RAW = pd.DataFrame(
    {
        "date": pd.date_range("2026-01-01", periods=N),
        "temperature_2m_max": [28.0 + (i % 5) for i in range(N)],
        "temperature_2m_min": [20.0 + (i % 3) for i in range(N)],
        "precipitation_sum": [0.0, 8.0] * (N // 2),
        "windspeed_10m_max": [10.0] * N,
        "relative_humidity_2m_mean": [65.0 + (i % 10) for i in range(N)],
        "surface_pressure_mean": [1010.0] * N,
        "cloudcover_mean": [30.0 + (i % 20) for i in range(N)],
    }
)


def test_weather_pipeline_produces_predictions_and_passes_quality_check():
    loaded = {}

    def fake_load_table(df: pd.DataFrame, table_name: str) -> int:
        loaded[table_name] = df
        return len(df)

    with patch.object(
        source, "fetch_historical_weather", return_value=FAKE_RAW
    ), patch.object(db, "load_table", side_effect=fake_load_table):
        result = materialize(
            [raw_weather_data, weather_features, trained_rain_model, rain_predictions, model_quality_check]
        )

    assert result.success

    predictions = loaded["rain_predictions"]
    assert len(predictions) == 1
    assert set(predictions.columns) == {"based_on_date", "predicted_rain_tomorrow", "probability"}

    evaluations = result.get_asset_check_evaluations()
    assert len(evaluations) == 1
