"""
tests/test_routes.py
Integration tests for Flask routes.
All database calls are mocked so no live DB is needed.
"""
import pytest
import json
from unittest.mock import patch, MagicMock


# ── Shared mock data ───────────────────────────────────────────────────────

MOCK_KPIS = {
    "total_revenue": 125000.0,
    "total_orders": 450,
    "unique_customers": 220,
    "units_sold": 3200,
    "avg_order_value": 277.78,
}

MOCK_DASHBOARD = {
    "kpis":                 MOCK_KPIS,
    "monthly_revenue":      [{"month": "2024-01", "revenue": 12500.0}],
    "regional_performance": [{"region": "North", "completed_orders": 100, "revenue": 50000.0}],
    "category_revenue":     [{"category": "Electronics", "revenue": 75000.0, "units_sold": 500, "order_count": 200}],
    "top_products":         [{"product_name": "Laptop", "category": "Electronics", "units_sold": 50, "revenue": 65000.0}],
}

MOCK_SALES = {
    "data":     [{"order_id": 1, "customer_name": "Alice", "order_date": "2024-01-15", "region": "North",
                  "status": "Completed", "product_name": "Laptop", "category": "Electronics",
                  "quantity": 1, "unit_price": 1299.99, "line_total": 1299.99}],
    "total":    1,
    "page":     1,
    "per_page": 25,
    "pages":    1,
}


# ── Page route tests ───────────────────────────────────────────────────────

class TestPageRoutes:

    def test_root_redirects_to_dashboard(self, client):
        res = client.get("/", follow_redirects=False)
        assert res.status_code == 302
        assert "/dashboard" in res.headers.get("Location", "")

    def test_dashboard_page_returns_200(self, client):
        res = client.get("/dashboard")
        assert res.status_code == 200
        assert b"Dashboard" in res.data or b"InsightBoard" in res.data

    def test_sales_page_returns_200(self, client):
        res = client.get("/reports/sales")
        assert res.status_code == 200

    def test_products_page_returns_200(self, client):
        res = client.get("/reports/products")
        assert res.status_code == 200

    def test_customers_page_returns_200(self, client):
        res = client.get("/reports/customers")
        assert res.status_code == 200

    def test_404_for_unknown_page(self, client):
        res = client.get("/this-does-not-exist")
        assert res.status_code == 404


# ── API: /api/dashboard ────────────────────────────────────────────────────

class TestApiDashboard:

    def test_returns_200_with_valid_json(self, client):
        with patch("app.routes.services.get_dashboard_data", return_value=MOCK_DASHBOARD):
            res = client.get("/api/dashboard")
        assert res.status_code == 200
        data = json.loads(res.data)
        assert "kpis" in data
        assert "monthly_revenue" in data
        assert "regional_performance" in data
        assert "category_revenue" in data
        assert "top_products" in data

    def test_kpis_structure(self, client):
        with patch("app.routes.services.get_dashboard_data", return_value=MOCK_DASHBOARD):
            res = client.get("/api/dashboard")
        kpis = json.loads(res.data)["kpis"]
        assert "total_revenue"    in kpis
        assert "total_orders"     in kpis
        assert "unique_customers" in kpis
        assert "units_sold"       in kpis
        assert "avg_order_value"  in kpis

    def test_invalid_date_format_returns_400(self, client):
        res = client.get("/api/dashboard?start_date=not-a-date")
        assert res.status_code == 400
        data = json.loads(res.data)
        assert "error" in data

    def test_start_after_end_returns_400(self, client):
        res = client.get("/api/dashboard?start_date=2024-12-01&end_date=2024-01-01")
        assert res.status_code == 400
        data = json.loads(res.data)
        assert "error" in data

    def test_invalid_region_returns_400(self, client):
        res = client.get("/api/dashboard?region=INVALID_REGION")
        assert res.status_code == 400

    def test_valid_region_filter_passes(self, client):
        with patch("app.routes.services.get_dashboard_data", return_value=MOCK_DASHBOARD):
            res = client.get("/api/dashboard?region=North")
        assert res.status_code == 200

    def test_content_type_is_json(self, client):
        with patch("app.routes.services.get_dashboard_data", return_value=MOCK_DASHBOARD):
            res = client.get("/api/dashboard")
        assert "application/json" in res.content_type


# ── API: /api/reports/sales ────────────────────────────────────────────────

class TestApiSales:

    def test_returns_200_with_data(self, client):
        with patch("app.routes.queries.get_sales_report", return_value=MOCK_SALES):
            res = client.get("/api/reports/sales")
        assert res.status_code == 200
        data = json.loads(res.data)
        assert "data"  in data
        assert "total" in data
        assert "pages" in data

    def test_invalid_status_returns_400(self, client):
        res = client.get("/api/reports/sales?status=UNKNOWN")
        assert res.status_code == 400

    def test_invalid_category_returns_400(self, client):
        res = client.get("/api/reports/sales?category=BadCategory")
        assert res.status_code == 400

    def test_pagination_params_accepted(self, client):
        with patch("app.routes.queries.get_sales_report", return_value=MOCK_SALES):
            res = client.get("/api/reports/sales?page=2&per_page=50")
        assert res.status_code == 200


# ── API: /api/reports/products ─────────────────────────────────────────────

class TestApiProducts:

    def test_returns_200(self, client):
        with patch("app.routes.queries.get_top_products", return_value=[]), \
             patch("app.routes.queries.get_category_revenue", return_value=[]):
            res = client.get("/api/reports/products")
        assert res.status_code == 200

    def test_has_expected_keys(self, client):
        with patch("app.routes.queries.get_top_products", return_value=[]), \
             patch("app.routes.queries.get_category_revenue", return_value=[]):
            res = client.get("/api/reports/products")
        data = json.loads(res.data)
        assert "top_products"     in data
        assert "category_revenue" in data


# ── CSV Export ─────────────────────────────────────────────────────────────

class TestCsvExport:

    def test_returns_csv_content_type(self, client):
        with patch("app.routes.services.generate_csv", return_value="col1,col2\nv1,v2\n"):
            res = client.get("/reports/export.csv")
        assert res.status_code == 200
        assert "text/csv" in res.content_type

    def test_content_disposition_attachment(self, client):
        with patch("app.routes.services.generate_csv", return_value="a,b\n1,2\n"):
            res = client.get("/reports/export.csv")
        cd = res.headers.get("Content-Disposition", "")
        assert "attachment" in cd
        assert ".csv" in cd

    def test_invalid_filter_in_export_returns_400(self, client):
        res = client.get("/reports/export.csv?region=INVALID")
        assert res.status_code == 400
