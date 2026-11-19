"""
conftest.py — pytest fixtures for InsightBoard tests.
Creates a test Flask app without requiring a real database connection
by patching get_cursor at the module level.
"""
import os
import pytest

# Set test env vars before importing the app
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_NAME", "insightboard_test")
os.environ.setdefault("DB_USER", "root")
os.environ.setdefault("DB_PASSWORD", "")
os.environ["TESTING"] = "true"

from app import create_app


@pytest.fixture(scope="session")
def app():
    """Create a Flask test app instance."""
    flask_app = create_app()
    flask_app.config.update({
        "TESTING": True,
        "SECRET_KEY": "test-secret",
    })
    return flask_app


@pytest.fixture
def client(app):
    """Provide a test HTTP client."""
    return app.test_client()
