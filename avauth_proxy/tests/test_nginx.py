import os
import pytest
from unittest.mock import patch
from avauth_proxy.utils.nginx_utils import generate_nginx_configs, reload_nginx
from avauth_proxy.config import Config

@pytest.fixture
def temp_nginx_dir(tmpdir):
    temp_dir = tmpdir.mkdir("nginx")
    old_dir = Config.NGINX_CONFIG_DIR
    Config.NGINX_CONFIG_DIR = str(temp_dir)
    yield temp_dir
    Config.NGINX_CONFIG_DIR = old_dir

@patch("avauth_proxy.utils.nginx_utils.reload_nginx")
def test_generate_nginx_configs(mock_reload, temp_nginx_dir):
    proxies = [{
        "service_name": "test_service",
        "url": "127.0.0.1",
        "port": 8000,
        "template": "default.conf.j2",
        "custom_directives": "proxy_set_header X-Custom-Header my-value;"
    }]

    generate_nginx_configs(proxies)
    config_file = temp_nginx_dir.join("test_service.conf")
    assert config_file.check()
    with open(str(config_file), "r") as f:
        content = f.read()
        assert "test_service" in content
        assert "X-Custom-Header" in content

@patch("subprocess.run")
def test_reload_nginx(mock_run):
    mock_run.return_value.returncode = 0
    reload_nginx()
    mock_run.assert_called_once_with(["nginx", "-s", "reload"], capture_output=True)
