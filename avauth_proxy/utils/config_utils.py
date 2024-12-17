import os
import tomllib
from avauth_proxy.config import Config

def load_config_file(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Configuration file not found: {filepath}")
    with open(filepath, "rb") as f:
        return tomllib.load(f)

def get_oauth_providers():
    config_data = load_config_file(Config.CONFIG_TOML_FILE)
    return config_data.get("oauth_providers", [])

def get_app_config():
    config_data = load_config_file(Config.CONFIG_TOML_FILE)
    app_config = config_data.get("app", {})
    auth_config = config_data.get("auth", {})
    # Merge auth config into app config for convenience
    app_config.update(auth_config)
    return app_config
