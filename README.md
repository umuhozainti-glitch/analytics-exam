# Distributed E-commerce Analytics

Implementation for the AUCA Big Data Analytics final project. See
[`PROJECT_PLAN.md`](PROJECT_PLAN.md) for the chosen scope and
[`REPORT.md`](REPORT.md) for the report narrative.

## Prerequisites

Python 3.10+, Java 17, and Spark are required. Install Python packages with:

```powershell
python -m pip install -r requirements.txt
```

The supplied `dataset_generator.py` is a Jupyter notebook JSON export. A
correctly named copy is included as `dataset_generator.ipynb`. To generate a
manageable sample in `data/`, run:

```powershell
python generate_sample.py
```

The defaults generate 500 users, 300 products, 2,000 transactions, and 10,000
sessions. Adjust them with `--users`, `--products`, `--transactions`, and
`--sessions`. The original generator targets millions of records and should be
used only when sufficient time and disk space are available.

## MongoDB

Start a local MongoDB instance (Docker example):

```powershell
docker run --name ecommerce-mongo -d -p 27017:27017 mongo:7
python mongodb/load_mongodb.py --data-dir data
python mongodb/aggregations.py
```

The loader uses idempotent batched upserts and can safely be rerun. It stores
categories (with embedded subcategories), products, users, and transactions as
documents, then adds indexes used by the analytical pipelines. `--limit` applies
to each JSON collection when testing; omit it for the full data set.

## HBase

Use your course Docker/cloud HBase instance, execute `hbase/schema.hbase` in
the HBase shell, then run:

```powershell
python hbase/load_sessions.py --data-dir data --host localhost --limit 100000
python hbase/get_user_sessions.py user_000042 --host localhost
```

The default thrift port is 9090. HBase must expose its Thrift service for the
Python loader. The shell commands are still valid even if you use an alternative
client.

## Spark and figures

```powershell
spark-submit spark/analytics.py --data-dir data --output outputs
python visualize.py --input outputs --output outputs/figures
```

Spark writes CSV result tables used by `visualize.py`: category revenue,
recommendation pairs, funnel by referrer, and monthly cohort revenue. For local
Windows execution, the driver streams these compact aggregates to CSV to avoid
Hadoop's native file-output dependency; use Spark's distributed writer for
cluster-scale output.

## Submission checklist

- Run the code against a meaningful subset or full data; preserve command output.
- Put actual counts/results/screenshots in `REPORT.md`, then run
  `python render_report.py` to refresh the 6–8 page `REPORT.pdf`.
- Commit source code, the HBase schema, and reproduction instructions. Do not
  commit multi-gigabyte generated JSON unless your instructor explicitly asks.
