"""MarketLens - Market Data Analytics & Visualisation Module.

Computes descriptive statistics, price distributions, and rating breakdowns
from cleaned datasets using pandas, and generates executive text reports and
publication-grade charts using matplotlib.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Union
import logging

# Ensure non-interactive backend for headless environments & servers
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

logger = logging.getLogger("marketlens.analytics")


def generate_market_metrics(
    df_clean: pd.DataFrame,
    pipeline_stats: Optional[Dict[str, int]] = None,
) -> Dict[str, Any]:
    """Compute comprehensive descriptive market metrics from cleaned data.
    
    Args:
        df_clean: Processed pandas DataFrame.
        pipeline_stats: Optional audit counts from the cleaner module.
        
    Returns:
        Dictionary of computed descriptive statistics.
    """
    if df_clean.empty:
        logger.warning("Empty dataframe provided to analytics module.")
        return {}

    prices = df_clean["price_gbp"].dropna()
    ratings = df_clean["rating_stars"].dropna()

    total_records = len(df_clean)
    unique_titles = df_clean["title"].nunique()

    # Price Analytics
    mean_price = float(prices.mean()) if not prices.empty else 0.0
    median_price = float(prices.median()) if not prices.empty else 0.0
    min_price = float(prices.min()) if not prices.empty else 0.0
    max_price = float(prices.max()) if not prices.empty else 0.0
    std_price = float(prices.std()) if len(prices) > 1 else 0.0
    total_catalog_value = float(prices.sum()) if not prices.empty else 0.0

    # Rating Breakdown (1 to 5 stars)
    rating_counts = df_clean["rating_stars"].value_counts().sort_index().to_dict()
    # Normalize dictionary to guarantee presence of stars 1 through 5
    rating_distribution = {star: int(rating_counts.get(star, 0)) for star in range(1, 6)}

    # Availability Breakdown
    in_stock_count = int(df_clean["is_in_stock"].sum())
    out_of_stock_count = total_records - in_stock_count

    stats = pipeline_stats or {}

    metrics = {
        "total_records_processed": total_records,
        "unique_product_titles": unique_titles,
        "duplicates_removed": stats.get("duplicates_removed", 0),
        "invalid_records_rejected": stats.get("validation_failures", 0),
        "mean_price_gbp": round(mean_price, 2),
        "median_price_gbp": round(median_price, 2),
        "min_price_gbp": round(min_price, 2),
        "max_price_gbp": round(max_price, 2),
        "std_price_gbp": round(std_price, 2),
        "total_catalog_valuation_gbp": round(total_catalog_value, 2),
        "in_stock_count": in_stock_count,
        "out_of_stock_count": out_of_stock_count,
        "rating_distribution": rating_distribution,
    }

    logger.info(
        "Analytics computed: %d records, Avg Price: £%.2f (Range: £%.2f - £%.2f)",
        total_records,
        mean_price,
        min_price,
        max_price,
    )
    return metrics


def save_text_report(metrics: Dict[str, Any], output_path: Union[str, Path]) -> Path:
    """Generate a structured, executive-ready text report.
    
    Args:
        metrics: Dictionary returned by generate_market_metrics().
        output_path: Target destination path.
        
    Returns:
        Path of the generated report.
    """
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    total = metrics.get("total_records_processed", 0)
    rating_dist = metrics.get("rating_distribution", {})

    report_lines = [
        "=" * 68,
        "              MARKETLENS DATA RESEARCH REPORT",
        "        Automated Market Research & Strategy Deliverable",
        "=" * 68,
        "",
        "1. DATA COLLECTION & INGESTION AUDIT",
        f"   - Total Cleaned Records Analyzed : {total:,}",
        f"   - Unique Product Titles          : {metrics.get('unique_product_titles', 0):,}",
        f"   - Duplicate Records Removed      : {metrics.get('duplicates_removed', 0):,}",
        f"   - Rejected Corrupted Records     : {metrics.get('invalid_records_rejected', 0):,}",
        "",
        "2. PRICE & VALUATION ANALYSIS (GBP)",
        f"   - Average (Mean) Price           : £{metrics.get('mean_price_gbp', 0.0):.2f}",
        f"   - Median Price                   : £{metrics.get('median_price_gbp', 0.0):.2f}",
        f"   - Price Range (Min - Max)        : £{metrics.get('min_price_gbp', 0.0):.2f} - £{metrics.get('max_price_gbp', 0.0):.2f}",
        f"   - Standard Deviation             : £{metrics.get('std_price_gbp', 0.0):.2f}",
        f"   - Total Catalog Value            : £{metrics.get('total_catalog_valuation_gbp', 0.0):,.2f}",
        "",
        "3. INVENTORY & AVAILABILITY",
        f"   - In Stock Items                 : {metrics.get('in_stock_count', 0):,} ({metrics.get('in_stock_count', 0) / max(total, 1) * 100:.1f}%)",
        f"   - Out of Stock Items             : {metrics.get('out_of_stock_count', 0):,} ({metrics.get('out_of_stock_count', 0) / max(total, 1) * 100:.1f}%)",
        "",
        "4. STAR RATING DISTRIBUTION",
    ]

    for star, count in rating_dist.items():
        pct = (count / max(total, 1)) * 100
        bar = "█" * int(pct // 5)
        report_lines.append(f"   - {star} Star(s) : {count:3d} ({pct:5.1f}%)  {bar}")

    report_lines.extend([
        "",
        "=" * 68,
        "Generated automatically by MarketLens Analytics Engine",
        "=" * 68,
    ])

    report_content = "\n".join(report_lines)
    with open(target, mode="w", encoding="utf-8") as f:
        f.write(report_content)

    logger.info("Saved text research report to: %s", target)
    return target


def generate_visual_charts(
    df_clean: pd.DataFrame,
    output_path: Union[str, Path],
) -> Optional[Path]:
    """Generate dual visual charts (Price Distribution + Rating Histogram) using Matplotlib.
    
    Args:
        df_clean: Processed DataFrame.
        output_path: Target PNG destination.
        
    Returns:
        Path of the saved chart PNG image.
    """
    if df_clean.empty or "price_gbp" not in df_clean.columns:
        logger.warning("Insufficient data to generate charts.")
        return None

    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    prices = df_clean["price_gbp"].dropna()
    ratings = df_clean["rating_stars"].value_counts().reindex(range(1, 6), fill_value=0)

    # Setup corporate consulting aesthetic
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5), dpi=150)
    fig.suptitle("MarketLens — Product Price & Rating Analytics", fontsize=14, fontweight="bold", y=1.02)

    # Subplot 1: Price Distribution Histogram
    ax1.hist(prices, bins=10, color="#1F4E79", edgecolor="white", alpha=0.85)
    mean_val = prices.mean()
    median_val = prices.median()
    ax1.axvline(mean_val, color="#E74C3C", linestyle="--", linewidth=2, label=f"Mean: £{mean_val:.2f}")
    ax1.axvline(median_val, color="#F39C12", linestyle=":", linewidth=2, label=f"Median: £{median_val:.2f}")
    ax1.set_title("Price Distribution (£ GBP)", fontsize=11, fontweight="bold")
    ax1.set_xlabel("Price (£ GBP)")
    ax1.set_ylabel("Number of Books")
    ax1.legend(loc="upper right", frameon=True)
    ax1.grid(True, linestyle="--", alpha=0.5)

    # Subplot 2: Rating Distribution Bar Chart
    colors = ["#BDC3C7", "#95A5A6", "#3498DB", "#2980B9", "#1F4E79"]
    bars = ax2.bar(ratings.index, ratings.values, color=colors, edgecolor="black", linewidth=0.5)
    ax2.set_title("Customer Rating Breakdown", fontsize=11, fontweight="bold")
    ax2.set_xlabel("Star Rating (1 - 5)")
    ax2.set_ylabel("Book Count")
    ax2.set_xticks(range(1, 6))
    ax2.set_xticklabels(["1 Star", "2 Stars", "3 Stars", "4 Stars", "5 Stars"])
    ax2.grid(axis="y", linestyle="--", alpha=0.5)

    # Add count labels on top of each bar
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax2.annotate(
                f"{height}",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontweight="bold",
            )

    plt.tight_layout()
    plt.savefig(target, dpi=150, bbox_inches="tight")
    plt.close(fig)

    logger.info("Generated visual analytics chart: %s", target)
    return target
