"""
tests/test_queries.py
Unit tests for the SQL reporting layer.
All database calls are mocked so no live DB is needed.
"""
import pytest
from unittest.mock import patch, MagicMock
from contextlib import contextmanager


# ── Mock cursor context manager ─────────────────────────────────────────────

def make_mock_cursor(rows):
    """Create a mock cursor that returns `rows` on fetchall() or fetchone()."""
    cursor = MagicMock()
    if isinstance(rows, list):
        cursor.fetchall.return_value = rows
        cursor.fetchone.return_value = rows[0] if rows else None
    else:
        cursor.fetchone.return_value = rows
        cursor.fetchall.return_value = [rows]
    return cursor


def patch_cursor(rows):
    """Return a context-manager patch for app.queries.get_cursor."""
    mock_cursor = make_mock_cursor(rows)

    @contextmanager
    def mock_get_cursor(dictionary=True):
        yield mock_cursor

    return patch("app.queries.get_cursor", side_effect=mock_get_cursor), mock_cursor


# ── get_kpis tests ─────────────────────────────────────────────────────────

class TestGetKpis:

    def test_returns_expected_keys(self):
        kpi_row = {
            "total_revenue": 50000.00,
            "total_orders":  100,
            "unique_customers": 80,
            "units_sold": 450,
        }
        patcher, cursor = patch_cursor(kpi_row)
        with patcher:
            from app import queries
            result = queries.get_kpis()

        assert "total_revenue"    in result
        assert "total_orders"     in result
        assert "unique_customers" in result
        assert "units_sold"       in result
        assert "avg_order_value"  in result

    def test_sql_filters_completed_orders_only(self):
        kpi_row = {"total_revenue": 0, "total_orders": 0, "unique_customers": 0, "units_sold": 0}
        patcher, cursor = patch_cursor(kpi_row)
        with patcher:
            from app import queries
            queries.get_kpis()

        executed_sql = cursor.execute.call_args[0][0]
        assert "status = 'Completed'" in executed_sql, (
            "KPI query must filter WHERE o.status = 'Completed'"
        )

    def test_avg_order_value_is_zero_when_no_orders(self):
        kpi_row = {"total_revenue": 0, "total_orders": 0, "unique_customers": 0, "units_sold": 0}
        patcher, _ = patch_cursor(kpi_row)
        with patcher:
            from app import queries
            result = queries.get_kpis()

        assert result["avg_order_value"] == 0.0, "AOV must be 0 when total_orders is 0 (no ZeroDivisionError)"

    def test_avg_order_value_calculation(self):
        kpi_row = {"total_revenue": 10000.00, "total_orders": 20, "unique_customers": 15, "units_sold": 80}
        patcher, _ = patch_cursor(kpi_row)
        with patcher:
            from app import queries
            result = queries.get_kpis()

        assert result["avg_order_value"] == pytest.approx(500.00, abs=0.01)

    def test_date_filter_added_to_params(self):
        kpi_row = {"total_revenue": 0, "total_orders": 0, "unique_customers": 0, "units_sold": 0}
        patcher, cursor = patch_cursor(kpi_row)
        with patcher:
            from app import queries
            queries.get_kpis({"start_date": "2024-01-01", "end_date": "2024-06-30"})

        params = cursor.execute.call_args[0][1]
        assert "2024-01-01" in params
        assert "2024-06-30" in params

    def test_region_filter_added_to_params(self):
        kpi_row = {"total_revenue": 0, "total_orders": 0, "unique_customers": 0, "units_sold": 0}
        patcher, cursor = patch_cursor(kpi_row)
        with patcher:
            from app import queries
            queries.get_kpis({"region": "North"})

        params = cursor.execute.call_args[0][1]
        assert "North" in params


# ── get_monthly_revenue tests ──────────────────────────────────────────────

class TestGetMonthlyRevenue:

    def test_returns_list(self):
        rows = [
            {"month": "2024-01", "revenue": 12000.00},
            {"month": "2024-02", "revenue": 15000.50},
        ]
        patcher, _ = patch_cursor(rows)
        with patcher:
            from app import queries
            result = queries.get_monthly_revenue()

        assert isinstance(result, list)
        assert len(result) == 2

    def test_row_has_month_and_revenue_keys(self):
        rows = [{"month": "2024-03", "revenue": 8000.00}]
        patcher, _ = patch_cursor(rows)
        with patcher:
            from app import queries
            result = queries.get_monthly_revenue()

        assert result[0]["month"]   == "2024-03"
        assert result[0]["revenue"] == pytest.approx(8000.00)

    def test_filters_completed_only(self):
        patcher, cursor = patch_cursor([])
        with patcher:
            from app import queries
            queries.get_monthly_revenue()

        sql = cursor.execute.call_args[0][0]
        assert "status = 'Completed'" in sql


# ── get_top_products tests ─────────────────────────────────────────────────

class TestGetTopProducts:

    def test_limits_results(self):
        rows = [{"product_name": f"P{i}", "category": "Electronics", "units_sold": 10, "revenue": 1000.0} for i in range(10)]
        patcher, cursor = patch_cursor(rows)
        with patcher:
            from app import queries
            queries.get_top_products(limit=10)

        params = cursor.execute.call_args[0][1]
        assert 10 in params, "LIMIT param must be passed to query"

    def test_filters_completed_only(self):
        patcher, cursor = patch_cursor([])
        with patcher:
            from app import queries
            queries.get_top_products()

        sql = cursor.execute.call_args[0][0]
        assert "status = 'Completed'" in sql


# ── get_repeat_customers tests ─────────────────────────────────────────────

class TestGetRepeatCustomers:

    def test_having_clause_present(self):
        patcher, cursor = patch_cursor([])
        with patcher:
            from app import queries
            queries.get_repeat_customers()

        sql = cursor.execute.call_args[0][0]
        assert "HAVING" in sql.upper(), "Repeat customer query must include HAVING clause"
        assert "> 1" in sql, "HAVING must filter customers with more than 1 completed order"

    def test_returns_list(self):
        rows = [{"customer_id": 1, "customer_name": "Alice", "region": "North", "order_count": 3, "total_spend": 5000.0}]
        patcher, _ = patch_cursor(rows)
        with patcher:
            from app import queries
            result = queries.get_repeat_customers()

        assert isinstance(result, list)


# ── get_mom_growth tests ───────────────────────────────────────────────────

class TestGetMomGrowth:

    def test_returns_list_with_growth_fields(self):
        rows = [
            {"month": "2024-01", "revenue": 10000.0, "previous_revenue": None,    "growth_percentage": None},
            {"month": "2024-02", "revenue": 12000.0, "previous_revenue": 10000.0, "growth_percentage": 20.00},
        ]
        patcher, _ = patch_cursor(rows)
        with patcher:
            from app import queries
            result = queries.get_mom_growth()

        assert len(result) == 2
        assert result[1]["growth_percentage"] == pytest.approx(20.00)
        assert result[0]["previous_revenue"] is None

    def test_sql_uses_lag_and_cte(self):
        patcher, cursor = patch_cursor([])
        with patcher:
            from app import queries
            queries.get_mom_growth()

        sql = cursor.execute.call_args[0][0].upper()
        assert "LAG(" in sql, "MoM growth query must use LAG window function"
        assert "WITH " in sql, "MoM growth query must use a CTE (WITH clause)"
