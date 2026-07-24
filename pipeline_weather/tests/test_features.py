import pandas as pd

from main import FEATURE_COLUMNS, build_weather_features

RAW = pd.DataFrame(
    {
        "date": pd.date_range("2026-01-01", periods=6),
        "temperature_2m_max": [30.0, 31.0, 29.0, 32.0, 28.0, 33.0],
        "temperature_2m_min": [22.0, 23.0, 21.0, 24.0, 20.0, 25.0],
        "precipitation_sum": [0.0, 5.0, 0.0, 0.0, 10.0, 0.0],
        "windspeed_10m_max": [10.0, 12.0, 8.0, 11.0, 9.0, 13.0],
        "relative_humidity_2m_mean": [70.0, 75.0, 68.0, 72.0, 80.0, 65.0],
        "surface_pressure_mean": [1010.0, 1011.0, 1009.0, 1012.0, 1008.0, 1013.0],
        "cloudcover_mean": [40.0, 60.0, 30.0, 50.0, 70.0, 35.0],
    }
)


def test_build_weather_features_has_label_and_feature_columns():
    result = build_weather_features(RAW)

    for col in FEATURE_COLUMNS:
        assert col in result.columns
    assert "rain_tomorrow" in result.columns
    # No missing feature values survive the dropna step.
    assert result[FEATURE_COLUMNS].isna().sum().sum() == 0


def test_build_weather_features_labels_rain_from_next_day_precipitation():
    result = build_weather_features(RAW)

    # 2026-01-04's label should reflect 2026-01-05's precipitation (10.0mm -> rain).
    row = result.loc[result["date"] == pd.Timestamp("2026-01-04")].iloc[0]
    assert row["rain_tomorrow"] == 1

    # 2026-01-05's label should reflect 2026-01-06's precipitation (0.0mm -> no rain).
    row = result.loc[result["date"] == pd.Timestamp("2026-01-05")].iloc[0]
    assert row["rain_tomorrow"] == 0


def test_build_weather_features_keeps_last_row_with_unknown_label_for_scoring():
    result = build_weather_features(RAW)

    last_row = result.sort_values("date").iloc[-1]
    assert pd.isna(last_row["rain_tomorrow"])
