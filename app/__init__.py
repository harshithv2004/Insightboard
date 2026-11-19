"""
InsightBoard — Flask Application Factory
"""

from flask import Flask, render_template
from dotenv import load_dotenv
import os
import logging


def create_app():
    """Create and configure the Flask application."""
    load_dotenv()

    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "insightboard-dev-key-change-me")
    app.config["TESTING"] = os.getenv("TESTING", "false").lower() == "true"

    # Logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )

    # Register blueprint
    from .routes import main
    app.register_blueprint(main)

    # ── Error handlers ─────────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    @app.errorhandler(400)
    def bad_request(e):
        from flask import request, jsonify
        if request.path.startswith("/api/"):
            return jsonify({"error": str(e.description)}), 400
        return render_template("errors/404.html", message=str(e.description)), 400

    return app
