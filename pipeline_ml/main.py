import pandas as pd
from dagster import asset

import db


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


@asset
def order_features() -> pd.DataFrame:
    orders = db.read_table("orders")
    products = db.read_table("products")
    return build_order_features(orders, products)
