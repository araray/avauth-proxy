import pytest
import requests
from unittest.mock import patch


@pytest.fixture
def mock_oauth_server(mocker):
    # Mock the token endpoint
    mocker.patch(
        "requests.post",
        return_value=type(
            "Response",
            (object,),
            {
                "status_code": 200,
                "json": lambda: {"access_token": "mock_token", "token_type": "Bearer"},
            },
        )(),
    )
    # Mock the userinfo endpoint
    mocker.patch(
        "requests.get",
        return_value=type(
            "Response",
            (object,),
            {
                "status_code": 200,
                "json": lambda: {"email": "testuser@example.com", "name": "Test User"},
            },
        )(),
    )


def test_mock_oauth_token_request(mock_oauth_server):
    # Simulate requesting a token from the mock OAuth server
    response = requests.post(
        "http://localhost:6000/oauth/token",
        data={
            "grant_type": "password",
            "username": "testuser",
            "password": "password123",
            "client_id": "mock_client_id",
            "client_secret": "mock_client_secret",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "Bearer"


def test_mock_userinfo_request(mock_oauth_server):
    # Request user info with a mocked token
    access_token = "mock_token"
    response = requests.get(
        "http://localhost:6000/oauth/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    userinfo = response.json()
    assert userinfo["email"] == "testuser@example.com"
    assert userinfo["name"] == "Test User"
