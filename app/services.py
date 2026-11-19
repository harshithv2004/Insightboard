"""
InsightBoard — Business Logic & Services Layer
Handles input validation, data formatting, and CSV generation.
"""

import csv
import io
import logging
from datetime import datetime

from . import queries

logger = logging.getLogger(__name__)

VALID_REGIONS    = {"North", "South", "East", "West", "Central"}
VALID_STATUSES   = {"Completed", "Pending", "Cancelled"}
VALID_CATEGORIES = {"Electronics", "Office Supplies", "Furniture", "Software", "Accessories"}
VALID_SORT_COLS  = {"order_date", "line_total", "customer", "region", "status", "quantity", "product"}


class ValidationError(ValueError):
    """Raised when filter parameters fail validation."""


# ── Validation ─────────────────────────────────────────────────────────────

def validate_filters(args) -> dict:
    """
    Validate and sanitize filter parameters from a Flask request.args object.
    Returns a clean dict; raises ValidationError on invalid input.
    """
    filters: dict = {}

    start_date = args.get("start_date", "").strip()
    end_date   = args.get("end_date",   "").strip()
    region     = args.get("region",     "").strip()
    category   = args.get("category",   "").strip()
    status     = args.get("status",     "").strip()

    if start_date:
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
            filters["start_date"] = start_date
        except ValueError:
            raise ValidationError(
                f"Invalid start_date '{start_date}'. Use YYYY-MM-DD format."
            )

    if end_date:
        try:
            datetime.strptime(end_date, "%Y-%m-%d")
            filters["end_date"] = end_date
        except ValueError:
            raise ValidationError(
                f"Invalid end_date '{end_date}'. Use YYYY-MM-DD format."
            )

    if start_date and end_date and start_date > end_date:
        raise ValidationError("start_date cannot be after end_date.")

    if region:
        if region not in VALID_REGIONS:
            raise ValidationError(
                f"Invalid region '{region}'. Must be one of: {', '.join(sorted(VALID_REGIONS))}."
            )
        filters["region"] = region

    if category:
        if category not in VALID_CATEGORIES:
            raise ValidationError(
                f"Invalid category '{category}'. Must be one of: {', '.join(sorted(VALID_CATEGORIES))}."
            )
        filters["category"] = category

    if status:
        if status not in VALID_STATUSES:
            raise ValidationError(
                f"Invalid status '{status}'. Must be one of: {', '.join(sorted(VALID_STATUSES))}."
            )
        filters["status"] = status

    return filters


def validate_pagination(args) -> tuple[int, int]:
    """Validate and return (page, per_page) from request args."""
    try:
        page = max(1, int(args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1

    try:
        per_page = min(200, max(10, int(args.get("per_page", 25))))
    except (ValueError, TypeError):
        per_page = 25

    return page, per_page


def validate_sort(args) -> tuple[str, str]:
    """Validate and return (sort_by, sort_dir) from request args."""
    sort_by  = args.get("sort_by",  "order_date").strip()
    sort_dir = args.get("sort_dir", "DESC").strip().upper()

    if sort_by not in VALID_SORT_COLS:
        sort_by = "order_date"
    if sort_dir not in {"ASC", "DESC"}:
        sort_dir = "DESC"

    return sort_by, sort_dir


# ── Dashboard data aggregation ─────────────────────────────────────────────

def get_dashboard_data(filters: dict) -> dict:
    """Fetch all data needed for the executive dashboard in one call."""
    return {
        "kpis":                 queries.get_kpis(filters),
        "monthly_revenue":      queries.get_monthly_revenue(filters),
        "regional_performance": queries.get_regional_performance(filters),
        "category_revenue":     queries.get_category_revenue(filters),
        "top_products":         queries.get_top_products(filters, limit=10),
    }


# ── CSV Export ─────────────────────────────────────────────────────────────

CSV_FIELDS = [
    "order_id", "customer_name", "order_date", "region", "status",
    "product_name", "category", "quantity", "unit_price", "line_total",
]

CSV_HEADERS = [
    "Order ID", "Customer", "Order Date", "Region", "Status",
    "Product", "Category", "Quantity", "Unit Price (₹)", "Line Total (₹)",
]


def generate_csv(filters: dict) -> str:
    """
    Generate a UTF-8 CSV string for all rows matching filters.
    Uses the same query definitions as the on-screen sales report.
    """
    rows = queries.get_all_sales(filters)

    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow(CSV_HEADERS)

    for r in rows:
        writer.writerow([
            r["order_id"],
            r["customer_name"],
            r["order_date"],
            r["region"],
            r["status"],
            r["product_name"],
            r["category"],
            r["quantity"],
            f"{r['unit_price']:.2f}",
            f"{r['line_total']:.2f}",
        ])

    return output.getvalue()
