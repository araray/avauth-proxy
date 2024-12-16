from flask import Flask
from authlib.integrations.flask_client import OAuth
from avauth_proxy.utils.config_utils import get_app_config
from avauth_proxy.utils.logging_utils import configure_logging

# Initialize Flask app
app = Flask(__name__)

# Load application-specific configurations
app_config = get_app_config()
app.secret_key = app_config.get("secret_key", "fallback-secret-key")
app.config.update({
    "SESSION_COOKIE_SECURE": app_config.get("session_cookie_secure", True),
    "SESSION_COOKIE_HTTPONLY": app_config.get("session_cookie_httponly", True),
    "SESSION_COOKIE_SAMESITE": app_config.get("session_cookie_samesite", "Lax"),
})

# Configure logging
configure_logging()

# Initialize OAuth
oauth = OAuth(app)

# Import and register blueprints
from avauth_proxy.blueprints.auth_routes import auth_bp
from avauth_proxy.blueprints.proxy_routes import proxy_bp
from avauth_proxy.blueprints.metrics_routes import metrics_bp

app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(proxy_bp, url_prefix="/proxy")
app.register_blueprint(metrics_bp, url_prefix="/metrics")
