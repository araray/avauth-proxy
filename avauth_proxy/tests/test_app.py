import pytest
from avauth_proxy import app as flask_app

@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    flask_app.config["WTF_CSRF_ENABLED"] = False
    with flask_app.test_client() as client:
        yield client

def test_index_redirects(client):
    # If use_oauth2_proxy = true, might redirect differently,
    # if false and no user logged in, redirects to login.
    response = client.get("/")
    assert response.status_code in [302, 303]

def test_login_page(client):
    response = client.get("/auth/login")
    # In test config, use_oauth2_proxy = false, so login page should be accessible.
    assert response.status_code == 200
    assert b"Please Choose a Login Provider" in response.data
