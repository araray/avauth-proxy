import os
import pytest
from unittest.mock import patch
from avauth_proxy.utils.nginx_utils import generate_nginx_configs, reload_nginx
from avauth_proxy.config import Config


@pytest.fixture
def temp_nginx_dir(tmpdir):
    """
    Creates a temporary directory for Nginx configuration files during tests.
    """
    temp_dir = tmpdir.mkdir("nginx")
    Config.NGINX_CONFIG_DIR = str(temp_dir)
    yield temp_dir


def test_generate_nginx_configs(temp_nginx_dir, mocker):
    """
    Test that Nginx configurations are generated correctly for given proxies.
    """
    # Mock the Nginx reload command
    mocker.patch("subprocess.run")

    proxies = [
        {
            "service_name": "test_service",
            "url": "127.0.0.1",
            "port": 8000,
            "template": "default.conf.j2",
            "custom_directives": "proxy_set_header X-Custom-Header my-value;",
        }
    ]

    # Call the configuration generator
    generate_nginx_configs(proxies)

    # Verify the configuration file exists
    config_file = temp_nginx_dir.join("test_service.conf")
    assert config_file.check(), "Nginx configuration file was not created"

    # Verify file content
    with open(config_file, "r") as f:
        content = f.read()
        assert "test_service" in content
        assert "127.0.0.1" in content
        assert "proxy_set_header X-Custom-Header my-value;" in content


def test_reload_nginx(mocker):
    """
    Test that the Nginx reload command is executed correctly.
    """
    mock_subprocess = mocker.patch("subprocess.run", return_value=type("Result", (object,), {"returncode": 0})())
    reload_nginx()
    mock_subprocess.assert_called_once_with(["nginx", "-s", "reload"], capture_output=True)
