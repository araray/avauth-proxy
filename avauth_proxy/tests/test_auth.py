import pytest
from avauth_proxy import app

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
