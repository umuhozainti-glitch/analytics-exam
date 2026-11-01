"""Create four static, report-ready charts from Spark's CSV result folders."""
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

def load(folder: Path) -> pd.DataFrame:
    files = list(folder.glob("*.csv"))
    if not files: raise FileNotFoundError(f"No CSV part file in {folder}")
    return pd.read_csv(files[0])

def save(fig, target: Path):
    fig.tight_layout(); fig.savefig(target, dpi=180, bbox_inches="tight"); plt.close(fig)

def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--input", default="outputs"); parser.add_argument("--output", default="outputs/figures")
    args = parser.parse_args(); source, out = Path(args.input), Path(args.output); out.mkdir(parents=True, exist_ok=True)
    revenue = load(source / "category_revenue").head(10).sort_values("revenue")
    fig, ax = plt.subplots(figsize=(8, 5)); ax.barh(revenue.category_id, revenue.revenue, color="#2d6a4f"); ax.set(title="Top categories by revenue", xlabel="Revenue", ylabel="Category"); save(fig, out / "01_category_revenue.png")
    pairs = load(source / "recommendations").head(12).sort_values("count")
    fig, ax = plt.subplots(figsize=(9, 5)); ax.barh(pairs.left + " + " + pairs.right, pairs["count"], color="#457b9d"); ax.set(title="Most frequent product pairs", xlabel="Orders containing both products", ylabel="Pair"); save(fig, out / "02_recommendations.png")
    funnel = load(source / "funnel_by_referrer").sort_values("conversion_pct")
    fig, ax = plt.subplots(figsize=(8, 5)); ax.barh(funnel.referrer, funnel.conversion_pct, color="#e76f51"); ax.set(title="Conversion rate by acquisition channel", xlabel="Converted sessions (%)", ylabel="Referrer"); save(fig, out / "03_channel_conversion.png")
    cohort = load(source / "cohort_revenue"); cohort["cohort_month"] = cohort.cohort_month.astype(str).str[:7]; cohort["purchase_month"] = cohort.purchase_month.astype(str).str[:7]
    table = cohort.pivot(index="cohort_month", columns="purchase_month", values="revenue").fillna(0)
    fig, ax = plt.subplots(figsize=(9, 5)); image = ax.imshow(table.values, aspect="auto", cmap="YlGnBu"); ax.set(title="Cohort revenue by registration and purchase month", xlabel="Purchase month", ylabel="Registration cohort", xticks=range(len(table.columns)), xticklabels=table.columns, yticks=range(len(table.index)), yticklabels=table.index); fig.colorbar(image, ax=ax, label="Revenue"); save(fig, out / "04_cohort_revenue.png")
    print(f"Created four charts in {out}")

if __name__ == "__main__": main()
