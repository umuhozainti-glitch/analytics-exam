"""Load e-commerce JSON into MongoDB with schemas optimized for its queries."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from pymongo import MongoClient, ASCENDING, DESCENDING, ReplaceOne

def read_json(path: Path, limit: int | None = None):
    with path.open(encoding="utf-8") as source:
        rows = json.load(source)
    return rows if limit is None else rows[:limit]

def insert(collection, rows, key: str):
    if not rows:
        return
    for start in range(0, len(rows), 1000):
        operations = []
        for row in rows[start:start + 1000]:
            row["_id"] = row[key]
            operations.append(ReplaceOne({"_id": row[key]}, row, upsert=True))
        collection.bulk_write(operations, ordered=False)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--uri", default="mongodb://localhost:27017")
    parser.add_argument("--database", default="ecommerce")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--drop", action="store_true", help="drop project collections first")
    args = parser.parse_args()
    directory = Path(args.data_dir)
    db = MongoClient(args.uri)[args.database]
    collections = ("categories", "products", "users", "transactions")
    if args.drop:
        for name in collections:
            db[name].drop()

    insert(db.categories, read_json(directory / "categories.json", args.limit), "category_id")
    insert(db.products, read_json(directory / "products.json", args.limit), "product_id")
    insert(db.users, read_json(directory / "users.json", args.limit), "user_id")
    insert(db.transactions, read_json(directory / "transactions.json", args.limit), "transaction_id")

    db.categories.create_index([("name", ASCENDING)])
    db.products.create_index([("category_id", ASCENDING), ("is_active", ASCENDING)])
    db.users.create_index([("geo_data.country", ASCENDING)])
    db.transactions.create_index([("timestamp", DESCENDING)])
    db.transactions.create_index([("user_id", ASCENDING), ("timestamp", DESCENDING)])
    db.transactions.create_index([("items.product_id", ASCENDING)])
    print({name: db[name].count_documents({}) for name in collections})

if __name__ == "__main__":
    main()
