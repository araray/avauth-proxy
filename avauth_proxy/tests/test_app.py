import pytest
from avauth_proxy import app as flask_app  # Import the Flask app

@pytest.fixture
def client():
    # Configure the Flask app for testing
    flask_app.config["TESTING"] = True
    flask_app.config["WTF_CSRF_ENABLED"] = False  # Disable CSRF for tests
    with flask_app.test_client() as client:
        yield client


def test_index_redirects_to_login(client):
    response = client.get("/")
    assert response.status_code == 302  # Redirect to login
    assert "/auth/login" in response.headers["Location"]


def test_login_page(client):
    response = client.get("/auth/login")
    assert response.status_code == 200
    assert b"Please Choose a Login Provider" in response.data


def test_add_proxy(client, tmpdir):
    proxies_file = tmpdir.join("proxies_config.toml")
    flask_app.config["PROXIES_CONFIG_FILE"] = str(proxies_file)

    with client.session_transaction() as sess:
        sess["user"] = {"name": "Test User"}

    data = {
        "service_name": "test_service",
        "url": "127.0.0.1",
        "port": "8000",
        "template": "default.conf.j2",
        "custom_directives": "",
    }
    response = client.post("/proxy/add_proxy", data=data, follow_redirects=True)
    assert response.status_code == 200

    # Verify the proxy was added
    with open(str(proxies_file), "r") as f:
        assert "test_service" in f.read()
