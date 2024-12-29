from flask import Flask, session, redirect, url_for
from avauth_proxy.config import Config
from avauth_proxy.utils.config_utils import get_app_config
from avauth_proxy.utils.logging_utils import configure_logging
from authlib.integrations.flask_client import OAuth
from avauth_proxy.models import init_db

app = Flask(__name__)

# Now load dynamic config
app_config = get_app_config()

# Initialize the database
db_url = app_config["database"].get("url", "sqlite:///./data/avauth.db")
init_db(db_url)

# Load app config
Config.USE_OAUTH2_PROXY = app_config.get("use_oauth2_proxy", True)
Config.ADMIN_EMAILS = app_config.get("admin_emails", [])

# Load Flask app config
app.secret_key = app_config.get("secret_key", Config.SECRET_KEY)
app.config.update({
    "SESSION_COOKIE_SECURE": app_config.get("session_cookie_secure", Config.SESSION_COOKIE_SECURE),
    "SESSION_COOKIE_HTTPONLY": app_config.get("session_cookie_httponly", Config.SESSION_COOKIE_HTTPONLY),
    "SESSION_COOKIE_SAMESITE": app_config.get("session_cookie_samesite", Config.SESSION_COOKIE_SAMESITE),
})

configure_logging()

oauth = OAuth(app)  # OAuth instance for internal OAuth mode

# Import and register blueprints
from avauth_proxy.blueprints.auth_routes import auth_bp
from avauth_proxy.blueprints.proxy_routes import proxy_bp
from avauth_proxy.blueprints.metrics_routes import metrics_bp

app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(proxy_bp, url_prefix="/proxy")
app.register_blueprint(metrics_bp, url_prefix="/metrics")

print(app.url_map)

# If internal OAuth is used, login endpoints are under /auth
# If oauth2-proxy is used, authentication is handled externally.

@app.route('/')
def index():
    # Redirect to dashboard if logged in internally, else login
    if not Config.USE_OAUTH2_PROXY:
        if 'user' in session:
            return redirect(url_for('proxy.dashboard'))
        else:
            return redirect(url_for('auth.login'))
    return redirect(url_for('proxy.dashboard'))
