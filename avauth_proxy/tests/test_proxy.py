import pytest
from avauth_proxy.utils.file_utils import load_proxies, save_proxies
from avauth_proxy.config import Config

def test_load_proxies(tmpdir):
    old_file = Config.PROXIES_CONFIG_FILE
    proxies_file = tmpdir.join("proxies_config.toml")
    proxies_file.write("")
    Config.PROXIES_CONFIG_FILE = str(proxies_file)
    proxies = load_proxies()
    assert proxies == []
    Config.PROXIES_CONFIG_FILE = old_file
