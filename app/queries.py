"""
InsightBoard — SQL Reporting Layer
All business metrics are defined here as parameterized SQL queries.
Never concatenate user-supplied values; always use %s placeholders.
"""

from decimal import Decimal
from .db import get_cursor
import logging

logger = logging.getLogger(__name__)

# ── Allowed sort columns (whitelist to prevent injection) ──────────────────
_SALES_SORT_MAP = {
    "order_date":   "o.order_date",
    "line_total":   "(oi.quantity * oi.unit_price)",
    "customer":     "c.customer_name",
    "region":       "o.region",
    "status":       "o.status",
    "quantity":     "oi.quantity",
    "product":      "p.product_name",
}


# ── Private helper ─────────────────────────────────────────────────────────

def _to_float(value) -> float:
    """Convert Decimal / None to float safely."""
    if value is None:
        return 0.0
    return float(value)


def _kpi_where(filters: dict):
    """Build WHERE conditions for KPI / chart queries (completed orders)."""
    conditions = ["o.status = 'Completed'"]
    params: list = []
    if filters.get("start_date"):
        conditions.append("o.order_date >= %s")
        params.append(filters["start_date"])
    if filters.get("end_date"):
        conditions.append("o.order_date <= %s")
        params.append(filters["end_date"])
    if filters.get("region"):
        conditions.append("o.region = %s")
        params.append(filters["region"])
    return " AND ".join(conditions), params


# ── Query 1 — Executive KPIs ───────────────────────────────────────────────

def get_kpis(filters: dict | None = None) -> dict:
    """Total revenue, orders, customers, units sold, and AOV (completed only)."""
    filters = filters or {}
    where, params = _kpi_where(filters)
    sql = f"""
        SELECT
            COALESCE(SUM(oi.quantity * oi.unit_price), 0)  AS total_revenue,
            COUNT(DISTINCT o.order_id)                      AS total_orders,
            COUNT(DISTINCT o.customer_id)                   AS unique_customers,
            COALESCE(SUM(oi.quantity), 0)                   AS units_sold
        FROM Orders o
        JOIN OrderItems oi ON oi.order_id = o.order_id
        WHERE {where}
    """
    with get_cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
    revenue = _to_float(row["total_revenue"])
    orders  = int(row["total_orders"])
    return {
        "total_revenue":     revenue,
        "total_orders":      orders,
        "unique_customers":  int(row["unique_customers"]),
        "units_sold":        int(row["units_sold"]),
        "avg_order_value":   round(revenue / orders, 2) if orders > 0 else 0.0,
    }


# ── Query 2 — Monthly revenue trend ───────────────────────────────────────

def get_monthly_revenue(filters: dict | None = None) -> list:
    """Revenue grouped by calendar month (YYYY-MM)."""
    filters = filters or {}
    where, params = _kpi_where(filters)
    sql = f"""
        SELECT DATE_FORMAT(o.order_date, '%Y-%m') AS month,
               SUM(oi.quantity * oi.unit_price)   AS revenue
        FROM Orders o
        JOIN OrderItems oi ON oi.order_id = o.order_id
        WHERE {where}
        GROUP BY DATE_FORMAT(o.order_date, '%Y-%m')
        ORDER BY month
    """
    with get_cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    return [{"month": r["month"], "revenue": _to_float(r["revenue"])} for r in rows]


# ── Query 3 — Top products ─────────────────────────────────────────────────

def get_top_products(filters: dict | None = None, limit: int = 10) -> list:
    """Top products by revenue for completed orders."""
    filters = filters or {}
    where, params = _kpi_where(filters)
    if filters.get("category"):
        where += " AND p.category = %s"
        params.append(filters["category"])
    params.append(limit)
    sql = f"""
        SELECT p.product_name, p.category,
               SUM(oi.quantity)                 AS units_sold,
               SUM(oi.quantity * oi.unit_price) AS revenue
        FROM OrderItems oi
        JOIN Orders   o ON o.order_id   = oi.order_id
        JOIN Products p ON p.product_id = oi.product_id
        WHERE {where}
        GROUP BY p.product_id, p.product_name, p.category
        ORDER BY revenue DESC
        LIMIT %s
    """
    with get_cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    return [
        {
            "product_name": r["product_name"],
            "category":     r["category"],
            "units_sold":   int(r["units_sold"]),
            "revenue":      _to_float(r["revenue"]),
        }
        for r in rows
    ]


# ── Query 4 — Regional performance ────────────────────────────────────────

def get_regional_performance(filters: dict | None = None) -> list:
    """Orders and revenue by region (completed only)."""
    filters = filters or {}
    # Regional chart should not filter by region itself (shows all regions)
    conditions = ["o.status = 'Completed'"]
    params: list = []
    if filters.get("start_date"):
        conditions.append("o.order_date >= %s")
        params.append(filters["start_date"])
    if filters.get("end_date"):
        conditions.append("o.order_date <= %s")
        params.append(filters["end_date"])
    where = " AND ".join(conditions)
    sql = f"""
        SELECT o.region,
               COUNT(DISTINCT o.order_id)       AS completed_orders,
               SUM(oi.quantity * oi.unit_price) AS revenue
        FROM Orders o
        JOIN OrderItems oi ON oi.order_id = o.order_id
        WHERE {where}
        GROUP BY o.region
        ORDER BY revenue DESC
    """
    with get_cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    return [
        {
            "region":            r["region"],
            "completed_orders":  int(r["completed_orders"]),
            "revenue":           _to_float(r["revenue"]),
        }
        for r in rows
    ]


# ── Query 7 — Category revenue ─────────────────────────────────────────────

def get_category_revenue(filters: dict | None = None) -> list:
    """Revenue and units sold by product category (completed only)."""
    filters = filters or {}
    where, params = _kpi_where(filters)
    sql = f"""
        SELECT p.category,
               SUM(oi.quantity * oi.unit_price) AS revenue,
               SUM(oi.quantity)                 AS units_sold,
               COUNT(DISTINCT o.order_id)       AS order_count
        FROM OrderItems oi
        JOIN Orders   o ON o.order_id   = oi.order_id
        JOIN Products p ON p.product_id = oi.product_id
        WHERE {where}
        GROUP BY p.category
        ORDER BY revenue DESC
    """
    with get_cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    return [
        {
            "category":    r["category"],
            "revenue":     _to_float(r["revenue"]),
            "units_sold":  int(r["units_sold"]),
            "order_count": int(r["order_count"]),
        }
        for r in rows
    ]


# ── Sales report (paginated, all filters) ─────────────────────────────────

def get_sales_report(
    filters: dict | None = None,
    page: int = 1,
    per_page: int = 25,
    sort_by: str = "order_date",
    sort_dir: str = "DESC",
) -> dict:
    """Detailed order-line sales report with pagination and filters."""
    filters  = filters or {}
    sort_col = _SALES_SORT_MAP.get(sort_by, "o.order_date")
    sort_dir = "ASC" if sort_dir.upper() == "ASC" else "DESC"

    conditions = ["1=1"]
    params: list = []

    if filters.get("start_date"):
        conditions.append("o.order_date >= %s")
        params.append(filters["start_date"])
    if filters.get("end_date"):
        conditions.append("o.order_date <= %s")
        params.append(filters["end_date"])
    if filters.get("region"):
        conditions.append("o.region = %s")
        params.append(filters["region"])
    if filters.get("category"):
        conditions.append("p.category = %s")
        params.append(filters["category"])
    if filters.get("status"):
        conditions.append("o.status = %s")
        params.append(filters["status"])

    where = " AND ".join(conditions)

    base = f"""
        FROM Orders o
        JOIN Customers  c  ON c.customer_id = o.customer_id
        JOIN OrderItems oi ON oi.order_id   = o.order_id
        JOIN Products   p  ON p.product_id  = oi.product_id
        WHERE {where}
    """

    count_sql = f"SELECT COUNT(*) AS total {base}"
    data_sql  = f"""
        SELECT
            o.order_id,
            c.customer_name,
            o.order_date,
            o.region,
            o.status,
            p.product_name,
            p.category,
            oi.quantity,
            oi.unit_price,
            (oi.quantity * oi.unit_price) AS line_total
        {base}
        ORDER BY {sort_col} {sort_dir}
        LIMIT %s OFFSET %s
    """

    offset = (page - 1) * per_page

    with get_cursor() as cur:
        cur.execute(count_sql, params)
        total = int(cur.fetchone()["total"])

        cur.execute(data_sql, params + [per_page, offset])
        rows = cur.fetchall()

    data = [
        {
            "order_id":     r["order_id"],
            "customer_name": r["customer_name"],
            "order_date":   str(r["order_date"]),
            "region":       r["region"],
            "status":       r["status"],
            "product_name": r["product_name"],
            "category":     r["category"],
            "quantity":     int(r["quantity"]),
            "unit_price":   _to_float(r["unit_price"]),
            "line_total":   _to_float(r["line_total"]),
        }
        for r in rows
    ]

    return {
        "data":     data,
        "total":    total,
        "page":     page,
        "per_page": per_page,
        "pages":    max(1, (total + per_page - 1) // per_page),
    }


def get_all_sales(filters: dict | None = None) -> list:
    """Return all matching rows (no pagination) for CSV export."""
    result = get_sales_report(filters=filters, page=1, per_page=100_000)
    return result["data"]


# ── Query 5 — Repeat customers ─────────────────────────────────────────────

def get_repeat_customers(filters: dict | None = None) -> list:
    """Customers with more than one completed order."""
    filters = filters or {}
    conditions = ["o.status = 'Completed'"]
    params: list = []
    if filters.get("start_date"):
        conditions.append("o.order_date >= %s")
        params.append(filters["start_date"])
    if filters.get("end_date"):
        conditions.append("o.order_date <= %s")
        params.append(filters["end_date"])
    if filters.get("region"):
        conditions.append("c.region = %s")
        params.append(filters["region"])
    where = " AND ".join(conditions)
    sql = f"""
        SELECT c.customer_id, c.customer_name, c.region,
               COUNT(DISTINCT o.order_id)       AS order_count,
               SUM(oi.quantity * oi.unit_price) AS total_spend
        FROM Customers c
        JOIN Orders    o  ON o.customer_id = c.customer_id
        JOIN OrderItems oi ON oi.order_id  = o.order_id
        WHERE {where}
        GROUP BY c.customer_id, c.customer_name, c.region
        HAVING COUNT(DISTINCT o.order_id) > 1
        ORDER BY total_spend DESC
        LIMIT 100
    """
    with get_cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    return [
        {
            "customer_id":   r["customer_id"],
            "customer_name": r["customer_name"],
            "region":        r["region"],
            "order_count":   int(r["order_count"]),
            "total_spend":   _to_float(r["total_spend"]),
        }
        for r in rows
    ]


def get_high_value_customers(filters: dict | None = None, limit: int = 20) -> list:
    """Top customers by total spend (completed orders)."""
    filters = filters or {}
    conditions = ["o.status = 'Completed'"]
    params: list = []
    if filters.get("start_date"):
        conditions.append("o.order_date >= %s")
        params.append(filters["start_date"])
    if filters.get("end_date"):
        conditions.append("o.order_date <= %s")
        params.append(filters["end_date"])
    where = " AND ".join(conditions)
    params.append(limit)
    sql = f"""
        SELECT c.customer_id, c.customer_name, c.region,
               COUNT(DISTINCT o.order_id)       AS order_count,
               SUM(oi.quantity * oi.unit_price) AS total_spend,
               MAX(o.order_date)                AS last_order
        FROM Customers c
        JOIN Orders    o  ON o.customer_id = c.customer_id
        JOIN OrderItems oi ON oi.order_id  = o.order_id
        WHERE {where}
        GROUP BY c.customer_id, c.customer_name, c.region
        ORDER BY total_spend DESC
        LIMIT %s
    """
    with get_cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    return [
        {
            "customer_id":   r["customer_id"],
            "customer_name": r["customer_name"],
            "region":        r["region"],
            "order_count":   int(r["order_count"]),
            "total_spend":   _to_float(r["total_spend"]),
            "last_order":    str(r["last_order"]),
        }
        for r in rows
    ]


# ── Query 6 — Month-over-month growth (CTE + window function) ─────────────

def get_mom_growth() -> list:
    """Month-over-month revenue growth using CTE and LAG window function."""
    sql = """
        WITH monthly_sales AS (
            SELECT DATE_FORMAT(o.order_date, '%Y-%m') AS month,
                   SUM(oi.quantity * oi.unit_price)   AS revenue
            FROM Orders o
            JOIN OrderItems oi ON oi.order_id = o.order_id
            WHERE o.status = 'Completed'
            GROUP BY DATE_FORMAT(o.order_date, '%Y-%m')
        ),
        sales_with_previous AS (
            SELECT month, revenue,
                   LAG(revenue) OVER (ORDER BY month) AS previous_revenue
            FROM monthly_sales
        )
        SELECT month, revenue, previous_revenue,
               ROUND(
                   100.0 * (revenue - previous_revenue)
                   / NULLIF(previous_revenue, 0),
               2) AS growth_percentage
        FROM sales_with_previous
        ORDER BY month
    """
    with get_cursor() as cur:
        cur.execute(sql)
        rows = cur.fetchall()
    return [
        {
            "month":             r["month"],
            "revenue":           _to_float(r["revenue"]),
            "previous_revenue":  _to_float(r["previous_revenue"]) if r["previous_revenue"] is not None else None,
            "growth_percentage": float(r["growth_percentage"]) if r["growth_percentage"] is not None else None,
        }
        for r in rows
    ]


# ── Distinct filter values ─────────────────────────────────────────────────

def get_distinct_regions() -> list:
    with get_cursor() as cur:
        cur.execute("SELECT DISTINCT region FROM Orders ORDER BY region")
        return [r["region"] for r in cur.fetchall()]


def get_distinct_categories() -> list:
    with get_cursor() as cur:
        cur.execute("SELECT DISTINCT category FROM Products ORDER BY category")
        return [r["category"] for r in cur.fetchall()]
