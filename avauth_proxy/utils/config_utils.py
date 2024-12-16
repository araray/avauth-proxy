import tomllib
import os
from avauth_proxy.config import Config

def load_config_file(filepath):
    """
    Loads a TOML configuration file.
    If the file doesn't exist or is invalid, returns an empty dictionary.

    :param filepath: Path to the configuration file.
    :return: Parsed TOML data as a dictionary.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Configuration file not found: {filepath}")

    try:
        with open(filepath, "rb") as f:
            return tomllib.load(f)
    except Exception as e:
        raise ValueError(f"Failed to parse configuration file '{filepath}': {e}")


def get_oauth_providers():
    """
    Reads the OAuth providers section from the main TOML config file.

    :return: List of dictionaries representing OAuth providers.
    """
    config_data = load_config_file(Config.CONFIG_TOML_FILE)
    return config_data.get("oauth_providers", [])


def get_app_config():
    """
    Reads the application-level configuration from the main TOML config file.

    :return: Dictionary containing application configuration.
    """
    config_data = load_config_file(Config.CONFIG_TOML_FILE)
    return config_data.get("app", {})
