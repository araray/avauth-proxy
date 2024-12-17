import pytest
from avauth_proxy import app, oauth
from avauth_proxy.utils.oauth_utils import load_oauth_providers

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_login_redirect(client):
    # Just verifying that /auth/login is accessible in internal mode
    response = client.get("/auth/login")
    assert response.status_code == 200
    assert b"Please Choose a Login Provider" in response.data

def test_oauth_providers_loaded():
    # Test that at least one provider is loaded in test config
    providers = load_oauth_providers(oauth)
    assert "mock_provider" in providers
    assert providers["mock_provider"]["name"] == "mock_provider"
