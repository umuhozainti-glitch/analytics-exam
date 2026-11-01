"""Run the supplied notebook generator with configurable, smaller counts."""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notebook", default="dataset_generator.ipynb")
    parser.add_argument("--output-dir", default="data")
    parser.add_argument("--users", type=int, default=500)
    parser.add_argument("--products", type=int, default=300)
    parser.add_argument("--transactions", type=int, default=2000)
    parser.add_argument("--sessions", type=int, default=10000)
    args = parser.parse_args()

    notebook = json.loads(Path(args.notebook).read_text(encoding="utf-8"))
    code = "\n".join(
        "".join(cell["source"])
        for cell in notebook["cells"]
        if cell.get("cell_type") == "code"
    )
    replacements = {
        "NUM_USERS": (10000, args.users),
        "NUM_PRODUCTS": (5000, args.products),
        "NUM_TRANSACTIONS": (500000, args.transactions),
        "NUM_SESSIONS": (2000000, args.sessions),
    }
    for name, (default, value) in replacements.items():
        code, count = re.subn(rf"\b{name}\s*=\s*{default}\b", f"{name} = {value}", code, count=1)
        if count != 1:
            raise ValueError(f"Could not find the expected {name} setting in {args.notebook}")

    output = Path(args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    os.chdir(output)
    exec(compile(code, str(Path(args.notebook).resolve()), "exec"), {"__name__": "__main__"})


if __name__ == "__main__":
    main()
