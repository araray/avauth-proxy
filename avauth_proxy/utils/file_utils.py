import tomllib
import tomli_w as tomlw
import os
from avauth_proxy.config import Config

def load_proxies():
    if os.path.exists(Config.PROXIES_CONFIG_FILE):
        with open(Config.PROXIES_CONFIG_FILE, "rb") as f:
            return tomllib.load(f).get("proxies", [])
    else:
        save_proxies([])  # Create an empty file if it doesn't exist
        return []

def save_proxies(proxies):
    with open(Config.PROXIES_CONFIG_FILE, "wb") as f:
        tomlw.dump({"proxies": proxies}, f)
