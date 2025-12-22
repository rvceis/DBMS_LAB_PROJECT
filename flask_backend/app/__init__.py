import os
from flask import Flask, jsonify
from flask_cors import CORS
from .config import get_config
from .extensions import db, migrate, jwt, ma
def create_app():
    env = os.getenv("FLASK_ENV", "development")
    config = get_config(env)

    app = Flask(__name__)
    app.config.from_object(config)
    
    # Disable strict slashes to prevent redirects
    app.url_map.strict_slashes = False
    
    # Enable CORS for all routes with proper preflight handling
    CORS(app, resources={r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": False
    }})

    # init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    ma.init_app(app)

    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_data):
        return jsonify({"error": "token expired"}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        print(f"Invalid token: {error}")
        return jsonify({"error": f"invalid token: {error}"}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        print(f"Missing token: {error}")
        return jsonify({"error": "missing authorization header"}), 401

    # Import models to ensure they're registered
    from . import models

    # register blueprints
    from .routes.auth import auth_bp
    from .routes.users import users_bp
    from .routes.asset_types import asset_types_bp
    # Use dynamic schemas routes
    from .routes.schemas_dynamic import schemas_bp
    from .routes.metadata import metadata_bp
    from .routes.analytics import analytics_bp
    from .routes.reports import reports_bp
    
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(users_bp, url_prefix="/users")
    app.register_blueprint(asset_types_bp, url_prefix="/asset-types")
    app.register_blueprint(schemas_bp, url_prefix="/schemas")
    app.register_blueprint(metadata_bp, url_prefix="/metadata")
    app.register_blueprint(analytics_bp, url_prefix="/analytics")
    app.register_blueprint(reports_bp, url_prefix="/reports")

    @app.route("/")
    def index():
        return {"status": "ok", "service": "MMS Flask Backend"}

    return app
