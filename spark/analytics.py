"""Spark batch pipeline: normalize JSON, recommendations, cohorts, and funnel SQL."""
from __future__ import annotations
import argparse
import csv
from pathlib import Path
from pyspark.sql import SparkSession, functions as F
from pyspark.sql.window import Window

def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--data-dir", default="data"); parser.add_argument("--output", default="outputs")
    args = parser.parse_args(); spark = SparkSession.builder.appName("ecommerce-analytics").getOrCreate()
    base = args.data_dir.rstrip("/")
    users = spark.read.json(f"{base}/users.json").select("user_id", F.to_timestamp("registration_date").alias("registration_ts"))
    products = spark.read.json(f"{base}/products.json").select("product_id", "category_id", "name")
    tx = spark.read.json(f"{base}/transactions.json").filter(F.col("status").isin("completed", "shipped", "delivered")) \
        .withColumn("purchase_ts", F.to_timestamp("timestamp")).filter(F.col("purchase_ts").isNotNull())
    session_files = [str(path) for path in Path(base).glob("sessions_*.json")]
    if not session_files:
        raise FileNotFoundError(f"No session JSON files found in {base}")
    # Pass explicit paths to avoid Hadoop wildcard expansion issues on Windows.
    sessions = spark.read.json(session_files).select("session_id", "user_id", "referrer", "conversion_status", "page_views")

    # Normalized transaction line items; invalid/missing product ids cannot join.
    lines = tx.select("transaction_id", "user_id", "purchase_ts", F.explode("items").alias("item")) \
        .select("transaction_id", "user_id", "purchase_ts", F.col("item.product_id").alias("product_id"), F.col("item.quantity").alias("quantity"), F.col("item.subtotal").alias("line_revenue")) \
        .filter(F.col("product_id").isNotNull() & (F.col("quantity") > 0))
    category_revenue = lines.join(products, "product_id").groupBy("category_id").agg(F.round(F.sum("line_revenue"), 2).alias("revenue"), F.sum("quantity").alias("units")).orderBy(F.desc("revenue"))

    # Market basket pairs: canonical order prevents duplicate X,Y/Y,X records.
    baskets = lines.groupBy("transaction_id").agg(F.collect_set("product_id").alias("products"))
    recommendations = baskets.select(F.explode("products").alias("left"), "products") \
        .select("left", F.explode("products").alias("right")).where("left < right") \
        .groupBy("left", "right").count().orderBy(F.desc("count"))

    # Cohort revenue: user registration month compared with purchase month.
    cohort = lines.join(users, "user_id").withColumn("cohort_month", F.date_trunc("month", "registration_ts")) \
        .withColumn("purchase_month", F.date_trunc("month", "purchase_ts")) \
        .groupBy("cohort_month", "purchase_month").agg(F.round(F.sum("line_revenue"), 2).alias("revenue"), F.countDistinct("user_id").alias("buyers"))

    # SQL is deliberately used for the cross-store logical funnel: session events
    # (HBase in production) plus completed transactions (MongoDB in production).
    # Deduplicate purchase sessions before the join so multiple records for a
    # session cannot inflate the session and conversion counts.
    sessions.createOrReplaceTempView("session_events")
    tx.filter(F.col("session_id").isNotNull()).select("session_id").distinct().createOrReplaceTempView("purchases")
    funnel = spark.sql("""SELECT s.referrer,
      COUNT(*) AS sessions,
      SUM(CASE WHEN size(s.page_views) > 0 THEN 1 ELSE 0 END) AS engaged_sessions,
      COUNT(p.session_id) AS converted_sessions,
      COUNT(p.session_id) AS linked_purchases,
      ROUND(100.0 * COUNT(p.session_id) / COUNT(*), 2) AS conversion_pct
      FROM session_events s LEFT JOIN purchases p ON s.session_id = p.session_id
      GROUP BY s.referrer ORDER BY conversion_pct DESC""")
    for name, frame in (("category_revenue", category_revenue), ("recommendations", recommendations), ("cohort_revenue", cohort), ("funnel_by_referrer", funnel)):
        # Stream the compact aggregate results to CSV from the driver. This
        # avoids Hadoop's native Windows file-output dependency while keeping
        # the joins and aggregations distributed in Spark.
        folder = Path(args.output) / name
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / "part-00000.csv"
        with target.open("w", newline="", encoding="utf-8") as output:
            writer = csv.writer(output)
            writer.writerow(frame.columns)
            for row in frame.toLocalIterator():
                writer.writerow(row)
        print(name, frame.count())
    spark.stop()

if __name__ == "__main__": main()
