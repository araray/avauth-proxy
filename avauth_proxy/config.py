import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-key")
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    ADMIN_EMAILS = []

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # Read CONFIG_TOML_FILE from environment or default
    CONFIG_TOML_FILE = os.getenv("CONFIG_TOML_FILE", os.path.join(os.path.dirname(BASE_DIR), "config.toml"))

    NGINX_CONFIG_DIR = "/etc/nginx/conf.d/proxies/"
    NGINX_TEMPLATES_DIR = os.path.join(BASE_DIR, "nginx_templates")
    EVENTS_LOG_FILE = os.path.join(os.path.dirname(BASE_DIR), "logs", "events.log")
    PROXIES_CONFIG_FILE = os.path.join(os.path.dirname(BASE_DIR), "proxies_config.toml")

    USE_OAUTH2_PROXY = True
    OAUTH2_PROXY_URL = os.getenv("OAUTH2_PROXY_URL", "http://localhost:4180")
