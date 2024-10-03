# avauth-proxy/config.py

import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key')
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    NGINX_CONFIG_DIR = '/etc/nginx/conf.d/proxies/'
    NGINX_TEMPLATES_DIR = os.path.join(BASE_DIR, 'nginx_templates')
    EVENTS_LOG_FILE = os.path.join(os.path.dirname(BASE_DIR), 'logs', 'events.log')
    PROXIES_CONFIG_FILE = os.path.join(os.path.dirname(BASE_DIR), 'proxies_config.toml')
    CONFIG_TOML_FILE = os.path.join(os.path.dirname(BASE_DIR), 'config.toml')
