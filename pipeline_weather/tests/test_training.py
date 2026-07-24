import pandas as pd

from main import ACCURACY_THRESHOLD, FEATURE_COLUMNS, model_quality_check, train_rain_classifier

# Perfectly separable on cloudcover_mean so the classifier's accuracy is
# deterministic regardless of the train/test split.
N = 20
SEPARABLE_FEATURES = pd.DataFrame(
    {
        "date": pd.date_range("2026-01-01", periods=N),
        "temperature_2m_max": [30.0] * N,
        "temperature_2m_min": [22.0] * N,
        "temp_range": [8.0] * N,
        "windspeed_10m_max": [10.0] * N,
        "relative_humidity_2m_mean": [70.0] * N,
        "surface_pressure_mean": [1010.0] * N,
        "cloudcover_mean": [10.0] * (N // 2) + [90.0] * (N // 2),
        "precip_rolling_3d": [0.0] * N,
        "humidity_rolling_3d": [70.0] * N,
        "rain_tomorrow": [0] * (N // 2) + [1] * (N // 2),
    }
)


def test_train_rain_classifier_meets_accuracy_threshold_on_separable_data():
    bundle = train_rain_classifier(SEPARABLE_FEATURES)

    assert bundle["accuracy"] >= ACCURACY_THRESHOLD
    assert bundle["feature_columns"] == FEATURE_COLUMNS
    assert hasattr(bundle["model"], "predict")


def test_model_quality_check_fails_below_accuracy_threshold():
    low_accuracy_bundle = {"model": None, "accuracy": 0.3, "feature_columns": []}

    result = model_quality_check(low_accuracy_bundle)

    assert result.passed is False
