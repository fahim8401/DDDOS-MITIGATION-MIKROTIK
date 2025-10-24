"""
Flask API factory for mt-ddos-manager
"""

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from .routes import api_bp


def create_app(config=None):
    """Create Flask application"""
    app = Flask(__name__)

    # Configuration
    if config:
        app.config.update(config)
    else:
        app.config['SECRET_KEY'] = 'dev-secret-key'  # Change in production
        app.config['JWT_SECRET_KEY'] = 'jwt-secret-key'  # Change in production

    # Extensions
    CORS(app)
    jwt = JWTManager(app)

    # Register blueprints
    app.register_blueprint(api_bp, url_prefix='/api')

    return app