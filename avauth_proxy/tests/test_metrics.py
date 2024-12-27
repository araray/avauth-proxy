# avauth_proxy/tests/test_metrics.py

import pytest
from datetime import datetime, timedelta
from avauth_proxy.services.metrics_service import MetricsService

def test_proxy_metrics_view(client, auth_admin):
    """Test the proxy metrics detail view."""
    # First create a test proxy
    proxy_data = {
        'service_name': 'test_service',
        'url': 'localhost',
        'port': 8080
    }
    response = client.post('/proxy/add', data=proxy_data)
    assert response.status_code == 302

    # Test metrics view
    response = client.get(f'/metrics/proxy/1/metrics')
    assert response.status_code == 200
    assert b'proxy-metrics-root' in response.data

def test_proxy_metrics_data(client, auth_admin):
    """Test the proxy metrics data API."""
    # Create test proxy
    proxy_data = {
        'service_name': 'test_service',
        'url': 'localhost',
        'port': 8080
    }
    client.post('/proxy/add', data=proxy_data)

    # Test data endpoint
    response = client.get('/metrics/proxy/1/data?timeframe=1h')
    assert response.status_code == 200
    data = response.json

    # Verify response structure
    assert 'health' in data
    assert 'summary' in data
    assert 'insights' in data
    assert 'requests' in data
    assert 'latency' in data
    assert 'errors' in data
    assert 'bandwidth' in data

def test_proxy_metrics_unauthorized(client):
    """Test that unauthorized users cannot access metrics."""
    response = client.get('/metrics/proxy/1/metrics')
    assert response.status_code in (401, 302)  # Either unauthorized or redirect to login

@pytest.mark.parametrize('timeframe', ['1h', '24h', '7d', '30d'])
def test_proxy_metrics_timeframes(client, auth_admin, timeframe):
    """Test different timeframe parameters for metrics data."""
    client.post('/proxy/add', data={
        'service_name': 'test_service',
        'url': 'localhost',
        'port': 8080
    })

    response = client.get(f'/metrics/proxy/1/data?timeframe={timeframe}')
    assert response.status_code == 200
    data = response.json
    assert data['summary'] is not None
