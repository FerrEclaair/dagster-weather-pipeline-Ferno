import pandas as pd
from dagster import AssetCheckResult, asset, asset_check
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

import db

ACCURACY_THRESHOLD = 0.6
FEATURE_INPUT_COLUMNS = ["quantity", "price", "category"]


def build_order_features(orders: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    merged = orders.merge(products, on="product_id", how="inner")
    merged["total"] = merged["quantity"] * merged["price"]
    median_total = merged["total"].median()
    merged["is_high_value"] = (merged["total"] > median_total).astype(int)
    return merged[
        [
            "order_id",
            "product_id",
            "customer_id",
            "quantity",
            "price",
            "category",
            "total",
            "is_high_value",
        ]
    ]


def train_classifier(features: pd.DataFrame) -> dict:
    encoded = pd.get_dummies(features[FEATURE_INPUT_COLUMNS], columns=["category"])
    feature_columns = list(encoded.columns)
    labels = features["is_high_value"]

    x_train, x_test, y_train, y_test = train_test_split(
        encoded, labels, test_size=0.3, random_state=42
    )
    model = LogisticRegression(max_iter=1000)
    model.fit(x_train, y_train)
    accuracy = accuracy_score(y_test, model.predict(x_test))

    return {"model": model, "accuracy": accuracy, "feature_columns": feature_columns}


@asset
def order_features() -> pd.DataFrame:
    orders = db.read_table("orders")
    products = db.read_table("products")
    return build_order_features(orders, products)


@asset
def trained_model(order_features: pd.DataFrame) -> dict:
    return train_classifier(order_features)


@asset_check(asset=trained_model)
def model_quality_check(trained_model: dict) -> AssetCheckResult:
    accuracy = trained_model["accuracy"]
    return AssetCheckResult(
        passed=accuracy >= ACCURACY_THRESHOLD, metadata={"accuracy": accuracy}
    )
