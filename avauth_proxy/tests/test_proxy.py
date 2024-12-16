import pytest
from avauth_proxy.utils.file_utils import load_proxies, save_proxies

def test_load_proxies(tmpdir):
    proxies_file = tmpdir.join("proxies_config.toml")
    proxies_file.write("")
    proxies = load_proxies()
    assert proxies == []
