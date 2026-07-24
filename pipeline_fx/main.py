import pandas as pd
from dagster import Definitions, ScheduleDefinition, asset, define_asset_job

import db
import source


@asset
def raw_exchange_rates() -> pd.DataFrame:
    payload = source.fetch_latest_rates(base="USD")
    rows = [
        {"base_currency": "USD", "quote_currency": currency, "rate": rate}
        for currency, rate in payload["rates"].items()
    ]
    return pd.DataFrame(rows)


@asset
def exchange_rates_table(raw_exchange_rates: pd.DataFrame) -> int:
    return db.load_table(raw_exchange_rates, "exchange_rates")


# TODO(exercise-2): add an `orders_in_eur` asset that reads the `orders` and
# `products` tables written by pipeline_products, joins them with
# exchange_rates_table, and converts order totals to EUR — see
# docs/exercises.md. This is a cross-container exercise: pipeline_fx and
# pipeline_products both write to the same warehouse Postgres, so this asset
# can just read those tables directly with the Warehouse engine.

refresh_fx_job = define_asset_job(name="refresh_fx_job")

refresh_fx_daily = ScheduleDefinition(
    name="refresh_fx_daily",
    job=refresh_fx_job,
    cron_schedule="0 6 * * *",
)

defs = Definitions(
    assets=[raw_exchange_rates, exchange_rates_table],
    jobs=[refresh_fx_job],
    schedules=[refresh_fx_daily],
)
