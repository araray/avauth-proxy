import os


class Config:
    """
    Centralized configuration class for the application.
    Environment variables can override default settings for flexibility.
    """

    # Flask secret key
    SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-key")

    # Cookie settings for secure sessions
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Base directories
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    NGINX_CONFIG_DIR = "/etc/nginx/conf.d/proxies/"
    NGINX_TEMPLATES_DIR = os.path.join(BASE_DIR, "nginx_templates")
    EVENTS_LOG_FILE = os.path.join(os.path.dirname(BASE_DIR), "logs", "events.log")
    PROXIES_CONFIG_FILE = os.path.join(os.path.dirname(BASE_DIR), "proxies_config.toml")
    CONFIG_TOML_FILE = os.path.join(os.path.dirname(BASE_DIR), "config.toml")

    # OAuth2 Proxy-related settings (optional overrides)
    OAUTH2_PROXY_URL = os.getenv("OAUTH2_PROXY_URL", "http://localhost:4180")
