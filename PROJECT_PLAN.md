# Distributed E-commerce Analytics — Project Plan

## Scope selected

This implementation answers the business question: **which products and channels
produce the best conversion, and which products should be recommended together?**
It uses MongoDB for catalogue, profiles, and purchase documents; HBase for
high-volume browsing events; and Spark for distributed cleaning, basket analysis,
funnel analysis, and the cross-system join.

## Repository deliverables

| Requirement | Deliverable |
| --- | --- |
| MongoDB model, loading and two analytics queries | `mongodb/` |
| HBase schema, loader and lookup | `hbase/` |
| Spark batch processing and Spark SQL | `spark/analytics.py` |
| Integrated funnel query | `spark/analytics.py --analysis funnel` |
| Static visualisations | `visualize.py` (writes `outputs/figures/`) |
| Report-ready technical narrative | `REPORT.md` |

## Data caveat

`dataset_generator.py` is a Jupyter notebook JSON export despite its extension.
Open it as a notebook, or rename a copy to `dataset_generator.ipynb`, before
running it in Jupyter/Colab. Its current product records do not include the
optional `subcategory_id` shown in the brief. This project therefore treats
`subcategory_id` as nullable and joins products at the category level.

## Suggested reproducible run

1. Generate data, or place `users.json`, `products.json`, `categories.json`,
   `transactions.json`, and `sessions_*.json` in `data/`.
2. Start MongoDB and HBase (instructions in `README.md`).
3. Load MongoDB: `python mongodb/load_mongodb.py --data-dir data`.
4. Create/load HBase: run the commands in `hbase/schema.hbase`, then
   `python hbase/load_sessions.py --data-dir data`.
5. Run Spark: `spark-submit spark/analytics.py --data-dir data --output outputs`.
6. Generate charts: `python visualize.py --input outputs --output outputs/figures`.

## What to include as evidence in the submission

Capture terminal output for the MongoDB counts and aggregation results, an HBase
`get`/`scan`, Spark row counts, and the four generated charts. Insert those
screenshots and the measured values into `REPORT.md` before converting it to PDF.
