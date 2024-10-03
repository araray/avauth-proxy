# tests/test_app.py

import pytest
import os
from avauth-proxy import app
from avauth-proxy.utils import load_proxies, save_proxies

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client

def test_index_redirects_to_login(client):
    response = client.get('/')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']

def test_login_page(client):
    response = client.get('/login')
    assert response.status_code == 200
    assert b"Please Choose a Login Provider" in response.data

def test_load_proxies_empty(tmpdir):
    proxies_file = tmpdir.join('proxies_config.toml')
    app.config['PROXIES_CONFIG_FILE'] = str(proxies_file)
    proxies = load_proxies()
    assert proxies == []

def test_add_proxy(client, tmpdir):
    proxies_file = tmpdir.join('proxies_config.toml')
    app.config['PROXIES_CONFIG_FILE'] = str(proxies_file)
    with client.session_transaction() as sess:
        sess['user'] = {'name': 'Test User'}
    data = {
        'service_name': 'test_service',
        'url': '127.0.0.1',
        'port': '8000',
        'template': 'default.conf.j2',
        'custom_directives': ''
    }
    response = client.post('/add_proxy', data=data, follow_redirects=True)
    assert response.status_code == 200
    # Check if the proxy was added
    proxies = load_proxies()
    assert len(proxies) == 1
    assert proxies[0]['service_name'] == 'test_service'
