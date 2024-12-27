import pytest
from flask import session, current_app
from avauth_proxy.utils.auth_utils import is_admin, admin_required, require_proxy_access

def test_is_admin_with_admin_email(app):
    """Test admin check with configured admin email."""
    with app.test_request_context():
        app.config['ADMIN_EMAILS'] = ['admin@example.com']
        session['user'] = {'email': 'admin@example.com'}
        assert is_admin() is True

def test_is_admin_with_admin_role(app):
    """Test admin check with admin role in session."""
    with app.test_request_context():
        session['user'] = {
            'email': 'user@example.com',
            'role': 'admin'
        }
        assert is_admin() is True

def test_is_admin_with_regular_user(app):
    """Test admin check with non-admin user."""
    with app.test_request_context():
        session['user'] = {
            'email': 'user@example.com',
            'role': 'user'
        }
        assert is_admin() is False

def test_admin_required_decorator(app, client):
    """Test admin_required decorator behavior."""
    @app.route('/test_admin')
    @admin_required
    def test_admin_route():
        return 'Admin access granted'

    # Test without login
    response = client.get('/test_admin')
    assert response.status_code == 302  # Redirect to login

    # Test with non-admin user
    with client.session_transaction() as sess:
        sess['user'] = {
            'email': 'user@example.com',
            'role': 'user'
        }
    response = client.get('/test_admin')
    assert response.status_code == 403

    # Test with admin user
    with client.session_transaction() as sess:
        sess['user'] = {
            'email': 'admin@example.com',
            'role': 'admin'
        }
    app.config['ADMIN_EMAILS'] = ['admin@example.com']
    response = client.get('/test_admin')
    assert response.status_code == 200
    assert b'Admin access granted' in response.data

def test_require_proxy_access_decorator(app, client):
    """Test proxy access control decorator."""
    @app.route('/test_proxy/<int:proxy_id>')
    @require_proxy_access('write')
    def test_proxy_route(proxy_id):
        return f'Access granted to proxy {proxy_id}'

    # Setup test data
    from avauth_proxy.models import User, Proxy, UserProxy
    user = User(email='user@example.com', role='user')
    proxy = Proxy(
        service_name='test_service',
        url='localhost',
        port=8080
    )
    access = UserProxy(
        user=user,
        proxy=proxy,
        access_level='write'
    )

    db_session = app.db.session
    db_session.add(user)
    db_session.add(proxy)
    db_session.add(access)
    db_session.commit()

    # Test without login
    response = client.get(f'/test_proxy/{proxy.id}')
    assert response.status_code == 302  # Redirect to login

    # Test with insufficient access
    with client.session_transaction() as sess:
        sess['user'] = {
            'email': 'other@example.com',
            'role': 'user'
        }
    response = client.get(f'/test_proxy/{proxy.id}')
    assert response.status_code == 403

    # Test with proper access
    with client.session_transaction() as sess:
        sess['user'] = {
            'email': 'user@example.com',
            'role': 'user'
        }
    response = client.get(f'/test_proxy/{proxy.id}')
    assert response.status_code == 200
    assert f'Access granted to proxy {proxy.id}'.encode() in response.data
