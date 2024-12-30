import pytest
from avauth_proxy import app
from avauth_proxy.models import init_db, get_db, User
from avauth_proxy.utils.security_utils import hash_password
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

@pytest.fixture(scope="module")
def test_app():
    # Use an in-memory SQLite DB for testing
    test_db_url = "sqlite:///:memory:"
    init_db(test_db_url)
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def create_test_user(email, password):
    db_generator = get_db()
    db = next(db_generator)
    user = User(
        email=email,
        password_hash=hash_password(password)
    )
    db.add(user)
    db.commit()

def test_local_signup(test_app):
    # Attempt to sign up with local auth
    response = test_app.post("/auth/signup/local", data={
        "email": "newuser@example.com",
        "password": "Password123"
    })
    # Expect redirect if successful
    assert response.status_code in (302, 303)

def test_local_login_success(test_app):
    create_test_user("test@example.com", "Password123")
    response = test_app.post("/auth/login/local", data={
        "email": "test@example.com",
        "password": "Password123"
    })
    # Expect redirect if successful
    assert response.status_code in (302, 303)

def test_local_login_failure(test_app):
    # Attempt login with invalid credentials
    response = test_app.post("/auth/login/local", data={
        "email": "bogus@example.com",
        "password": "WrongPassword"
    })
    assert response.status_code == 401
