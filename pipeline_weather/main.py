import pandas as pd
from dagster import AssetCheckResult, Definitions, ScheduleDefinition, asset, asset_check, define_asset_job
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

import db
import source

ACCURACY_THRESHOLD = 0.6
FEATURE_COLUMNS = [
    "temperature_2m_max",
    "temperature_2m_min",
    "temp_range",
    "windspeed_10m_max",
    "relative_humidity_2m_mean",
    "surface_pressure_mean",
    "cloudcover_mean",
    "precip_rolling_3d",
    "humidity_rolling_3d",
]


def build_weather_features(raw: pd.DataFrame) -> pd.DataFrame:
    """Engineer features and the training label from raw daily weather.

    `rain_tomorrow` = 1 if next day's precipitation_sum > 0mm, else 0.
    The most recent row's label is NaN (no "tomorrow" yet) — that row is
    kept so it can be scored later by `score_latest_day`, and is excluded
    from training by `train_rain_classifier`.
    """
    df = raw.sort_values("date").reset_index(drop=True)
    df["rain_tomorrow"] = (df["precipitation_sum"].shift(-1) > 0).astype(int)
    df.loc[df.index[-1], "rain_tomorrow"] = pd.NA

    df["temp_range"] = df["temperature_2m_max"] - df["temperature_2m_min"]
    df["precip_rolling_3d"] = df["precipitation_sum"].rolling(3).mean()
    df["humidity_rolling_3d"] = df["relative_humidity_2m_mean"].rolling(3).mean()

    return df.dropna(subset=FEATURE_COLUMNS).reset_index(drop=True)


def train_rain_classifier(features: pd.DataFrame) -> dict:
    labeled = features.dropna(subset=["rain_tomorrow"])
    x = labeled[FEATURE_COLUMNS]
    y = labeled["rain_tomorrow"].astype(int)

    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.3, random_state=42)
    model = RandomForestClassifier(n_estimators=200, max_depth=6, random_state=42)
    model.fit(x_train, y_train)
    accuracy = accuracy_score(y_test, model.predict(x_test))

    return {"model": model, "accuracy": accuracy, "feature_columns": FEATURE_COLUMNS}


def score_latest_day(features: pd.DataFrame, model_bundle: dict) -> pd.DataFrame:
    latest = features.sort_values("date").iloc[[-1]]
    x_latest = latest[model_bundle["feature_columns"]]
    model = model_bundle["model"]

    predicted = model.predict(x_latest)
    probability = model.predict_proba(x_latest)[:, 1]

    return pd.DataFrame(
        {
            "based_on_date": latest["date"].astype(str).values,
            "predicted_rain_tomorrow": predicted,
            "probability": probability,
        }
    )


@asset
def raw_weather_data() -> pd.DataFrame:
    return source.fetch_historical_weather()


@asset
def weather_features(raw_weather_data: pd.DataFrame) -> pd.DataFrame:
    return build_weather_features(raw_weather_data)


@asset
def trained_rain_model(weather_features: pd.DataFrame) -> dict:
    return train_rain_classifier(weather_features)


@asset_check(asset=trained_rain_model)
def model_quality_check(trained_rain_model: dict) -> AssetCheckResult:
    accuracy = trained_rain_model["accuracy"]
    return AssetCheckResult(
        passed=accuracy >= ACCURACY_THRESHOLD, metadata={"accuracy": accuracy}
    )


@asset
def rain_predictions(weather_features: pd.DataFrame, trained_rain_model: dict) -> int:
    predictions = score_latest_day(weather_features, trained_rain_model)
    return db.load_table(predictions, "rain_predictions")


refresh_weather_job = define_asset_job(name="refresh_weather_job")

refresh_weather_daily = ScheduleDefinition(
    name="refresh_weather_daily",
    job=refresh_weather_job,
    cron_schedule="0 6 * * *",
)

defs = Definitions(
    assets=[raw_weather_data, weather_features, trained_rain_model, rain_predictions],
    asset_checks=[model_quality_check],
    jobs=[refresh_weather_job],
    schedules=[refresh_weather_daily],
)
