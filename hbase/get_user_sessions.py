"""Prefix-scan chronological HBase browsing events for a specific user."""
import argparse
import happybase
p = argparse.ArgumentParser(); p.add_argument("user_id"); p.add_argument("--host", default="localhost"); p.add_argument("--port", type=int, default=9090)
args = p.parse_args(); table = happybase.Connection(args.host, args.port).table("user_events")
for key, columns in table.scan(row_prefix=(args.user_id + "|").encode()):
    print(key.decode(), {k.decode(): v.decode() for k, v in columns.items()})
