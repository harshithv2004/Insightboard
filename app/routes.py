"""
InsightBoard — Flask Routes
All pages and API endpoints are defined here under the 'main' blueprint.
"""

import logging
from flask import (
    Blueprint, render_template, request,
    jsonify, redirect, url_for, Response, abort,
)
from mysql.connector import Error as DBError

from . import queries, services
from .services import ValidationError

logger = logging.getLogger(__name__)
main   = Blueprint("main", __name__)


# ── Helpers ────────────────────────────────────────────────────────────────

def _db_error_response(exc: DBError, api: bool = False):
    logger.error("Database error in route: %s", exc)
    if api:
        return jsonify({"error": "A database error occurred. Please try again later."}), 500
    return render_template("errors/500.html"), 500


# ── Page routes ────────────────────────────────────────────────────────────

@main.route("/")
def index():
    return redirect(url_for("main.dashboard"))


@main.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@main.route("/reports/sales")
def sales_report():
    regions    = ["North", "South", "East", "West", "Central"]
    categories = ["Electronics", "Office Supplies", "Furniture", "Software", "Accessories"]
    return render_template("sales.html", regions=regions, categories=categories)


@main.route("/reports/products")
def products_report():
    categories = ["Electronics", "Office Supplies", "Furniture", "Software", "Accessories"]
    return render_template("products.html", categories=categories)


@main.route("/reports/customers")
def customers_report():
    regions = ["North", "South", "East", "West", "Central"]
    return render_template("customers.html", regions=regions)


# ── API: Dashboard ─────────────────────────────────────────────────────────

@main.route("/api/dashboard")
def api_dashboard():
    try:
        filters = services.validate_filters(request.args)
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400

    try:
        data = services.get_dashboard_data(filters)
        return jsonify(data)
    except DBError as exc:
        return _db_error_response(exc, api=True)
    except Exception as exc:
        logger.exception("Unexpected error in api_dashboard")
        return jsonify({"error": "Internal server error."}), 500


# ── API: Sales report ──────────────────────────────────────────────────────

@main.route("/api/reports/sales")
def api_sales():
    try:
        filters          = services.validate_filters(request.args)
        page, per_page   = services.validate_pagination(request.args)
        sort_by, sort_dir = services.validate_sort(request.args)
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400

    try:
        result = queries.get_sales_report(
            filters=filters,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )
        return jsonify(result)
    except DBError as exc:
        return _db_error_response(exc, api=True)
    except Exception:
        logger.exception("Unexpected error in api_sales")
        return jsonify({"error": "Internal server error."}), 500


# ── API: Products report ───────────────────────────────────────────────────

@main.route("/api/reports/products")
def api_products():
    try:
        filters = services.validate_filters(request.args)
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400

    try:
        return jsonify({
            "top_products":     queries.get_top_products(filters, limit=20),
            "category_revenue": queries.get_category_revenue(filters),
        })
    except DBError as exc:
        return _db_error_response(exc, api=True)
    except Exception:
        logger.exception("Unexpected error in api_products")
        return jsonify({"error": "Internal server error."}), 500


# ── API: Customers report ──────────────────────────────────────────────────

@main.route("/api/reports/customers")
def api_customers():
    try:
        filters = services.validate_filters(request.args)
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400

    try:
        return jsonify({
            "repeat_customers":     queries.get_repeat_customers(filters),
            "high_value_customers": queries.get_high_value_customers(filters),
            "mom_growth":           queries.get_mom_growth(),
        })
    except DBError as exc:
        return _db_error_response(exc, api=True)
    except Exception:
        logger.exception("Unexpected error in api_customers")
        return jsonify({"error": "Internal server error."}), 500


# ── CSV Export ─────────────────────────────────────────────────────────────

@main.route("/reports/export.csv")
def export_csv():
    try:
        filters = services.validate_filters(request.args)
    except ValidationError as exc:
        abort(400, description=str(exc))

    try:
        csv_data = services.generate_csv(filters)
    except DBError as exc:
        logger.error("DB error during CSV export: %s", exc)
        abort(500)
    except Exception:
        logger.exception("Unexpected error in export_csv")
        abort(500)

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=insightboard_export.csv",
            "Content-Type": "text/csv; charset=utf-8",
        },
    )
