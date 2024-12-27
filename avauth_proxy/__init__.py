from flask import Flask
from avauth_proxy.blueprints.auth_routes import auth_bp, user_bp
from avauth_proxy.blueprints.proxy_routes import proxy_bp
from avauth_proxy.blueprints.metrics_routes import metrics_bp
from avauth_proxy.blueprints.template_routes import template_bp
from avauth_proxy.utils.logging_utils import configure_logging

def create_app(config_object=None):
    """
    Application factory pattern for Flask app creation.

    Args:
        config_object: Configuration object or string with config class name

    Returns:
        Flask application instance
    """
    app = Flask(__name__, static_folder='static', static_url_path='/static')

    # Load configuration
    if config_object is not None:
        app.config.from_object(config_object)

    # Initialize extensions
    configure_logging()

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(user_bp, url_prefix="/users")
    app.register_blueprint(proxy_bp, url_prefix="/proxy")
    app.register_blueprint(metrics_bp, url_prefix="/metrics")
    app.register_blueprint(template_bp, url_prefix="/templates")

    return app

# Create the application instance
app = create_app()
