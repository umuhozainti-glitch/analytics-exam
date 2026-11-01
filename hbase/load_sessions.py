"""Flatten session page views into HBase user_events and daily product metrics."""
from __future__ import annotations
import argparse, glob, json
from collections import Counter
from pathlib import Path
import happybase

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", default="data"); p.add_argument("--host", default="localhost")
    p.add_argument("--port", type=int, default=9090); p.add_argument("--limit", type=int, default=None)
    args = p.parse_args(); connection = happybase.Connection(args.host, args.port)
    events, metrics, seen = connection.table("user_events"), connection.table("product_daily_metrics"), 0
    counts = Counter()
    with events.batch(batch_size=1000) as batch:
        for filename in glob.glob(str(Path(args.data_dir) / "sessions_*.json")):
            for session in json.load(open(filename, encoding="utf-8")):
                if args.limit is not None and seen >= args.limit: break
                seen += 1
                for n, view in enumerate(session.get("page_views", [])):
                    timestamp = view["timestamp"]
                    key = f'{session["user_id"]}|{timestamp}|{session["session_id"]}|{n:03d}'
                    values = {b"event:type": view["page_type"].encode(), b"event:session_id": session["session_id"].encode(),
                              b"context:referrer": session.get("referrer", "unknown").encode(),
                              b"context:device": session.get("device_profile", {}).get("type", "unknown").encode()}
                    if view.get("product_id"):
                        product, day = view["product_id"], timestamp[:10]
                        values[b"event:product_id"] = product.encode()
                        counts[(product, day, "views")] += 1
                    batch.put(key.encode(), values)
            if args.limit is not None and seen >= args.limit: break
    with metrics.batch(batch_size=1000) as batch:
        for (product, day, metric), value in counts.items():
            batch.put(f"{product}|{day}".encode(), {f"metrics:{metric}".encode(): str(value).encode()})
    print(f"Loaded {seen} sessions and {sum(counts.values())} product views")

if __name__ == "__main__": main()
