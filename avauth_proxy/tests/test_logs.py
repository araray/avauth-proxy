import pytest
from datetime import datetime, timedelta
from avauth_proxy.services.log_manager import LogManager, LogEntry

@pytest.fixture
def log_manager(tmp_path):
    """Create a LogManager instance with temporary log files."""
    nginx_log = tmp_path / "nginx_access.log"
    app_log = tmp_path / "app.log"

    # Create sample nginx log entries
    nginx_log.write_text(
        '192.168.1.1 - - [27/Dec/2024:10:00:00 +0000] "GET /proxy/status HTTP/1.1" '
        '200 1234 "https://example.com" "Mozilla/5.0"\n'
        '192.168.1.2 - - [27/Dec/2024:10:01:00 +0000] "POST /proxy/add HTTP/1.1" '
        '201 567 "https://example.com" "Mozilla/5.0"\n'
    )

    # Create sample app log entries
    app_log.write_text(
        '{"timestamp": "2024-12-27T10:00:00Z", "level": "INFO", '
        '"message": "Proxy status checked"}\n'
        '{"timestamp": "2024-12-27T10:01:00Z", "level": "INFO", '
        '"message": "New proxy added"}\n'
    )

    return LogManager(str(nginx_log), str(app_log))

def test_parse_nginx_log_line(log_manager):
    """Test parsing of Nginx log lines."""
    log_line = (
        '192.168.1.1 - - [27/Dec/2024:10:00:00 +0000] "GET /proxy/status '
        'HTTP/1.1" 200 1234 "https://example.com" "Mozilla/5.0"'
    )

    entry = log_manager.parse_nginx_log_line(log_line)

    assert entry is not None
    assert entry.ip_address == '192.168.1.1'
    assert entry.method == 'GET'
    assert entry.path == '/proxy/status'
    assert entry.status_code == 200
    assert entry.body_bytes == 1234
    assert entry.proxy_service == 'proxy'

def test_get_logs_with_filters(log_manager):
    """Test log retrieval with various filters."""
    # Test time range filter
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=1)

    logs = log_manager.get_logs(
        log_type='nginx',
        start_time=start_time,
        end_time=end_time,
        service_name='proxy',
        status_codes=[200, 201]
    )

    assert len(logs) == 2
    assert all(log.proxy_service == 'proxy' for log in logs)
    assert all(log.status_code in [200, 201] for log in logs)

def test_export_logs(log_manager):
    """Test log export functionality."""
    logs = log_manager.get_logs()

    # Test JSON export
    json_export = log_manager.export_logs(logs, 'json')
    assert '"ip_address": "192.168.1.1"' in json_export
    assert '"method": "GET"' in json_export

    # Test CSV export
    csv_export = log_manager.export_logs(logs, 'csv')
    assert 'IP Address,Method,Path' in csv_export
    assert '192.168.1.1,GET,/proxy/status' in csv_export

def test_get_log_statistics(log_manager):
    """Test log statistics generation."""
    logs = log_manager.get_logs()
    stats = log_manager.get_log_statistics(logs)

    assert stats['total_requests'] == 2
    assert stats['status_codes'] == {200: 1, 201: 1}
    assert stats['methods'] == {'GET': 1, 'POST': 1}
    assert stats['proxy_services'] == {'proxy': 2}
    assert stats['total_bytes'] == 1801  # 1234 + 567
