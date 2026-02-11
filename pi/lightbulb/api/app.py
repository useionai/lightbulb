"""Flask application factory."""

import logging
from pathlib import Path

from flask import Flask, send_from_directory
from flask_cors import CORS

from lightbulb.api.routes import api_bp

logger = logging.getLogger(__name__)

# Static files directory
STATIC_DIR = Path(__file__).parent.parent / "static"


def create_app() -> Flask:
    """Create and configure the Flask application.

    Returns:
        Configured Flask application.
    """
    app = Flask(__name__, static_folder=str(STATIC_DIR))

    # Enable CORS for all routes
    CORS(app)

    # Register blueprints
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.route("/")
    def index():
        """Serve the frontend."""
        return send_from_directory(STATIC_DIR, "index.html")

    @app.route("/<path:filename>")
    def static_files(filename):
        """Serve static files (manifest, sw.js, icons)."""
        return send_from_directory(STATIC_DIR, filename)

    logger.info("Flask application created")

    return app
