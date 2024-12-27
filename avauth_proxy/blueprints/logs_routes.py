from flask import Blueprint, render_template, request, jsonify, Response
from avauth_proxy.services.log_manager import LogManager
from avauth_proxy.utils.decorator_utils import log_route_error
from datetime import datetime, timedelta

logs_bp = Blueprint('logs', __name__)
log_manager = LogManager(
    nginx_log_path='/var/log/nginx/access.log',
    app_log_path='logs/events.log'
)

@logs_bp.route('/logs')
@log_route_error()
def view_logs():
    """Display the log viewing interface."""
    return render_template('logs/logs.html')

@logs_bp.route('/logs/data')
@log_route_error()
def get_logs():
    """
    API endpoint to retrieve filtered logs.

    Query Parameters:
        log_type: Type of logs to retrieve ('nginx' or 'app')
        start_time: ISO formatted datetime
        end_time: ISO formatted datetime
        service_name: Filter by proxy service
        status_codes: Comma-separated list of status codes
        limit: Maximum number of entries to return

    Returns:
        JSON response containing log entries
    """
    # Parse query parameters
    log_type = request.args.get('log_type', 'nginx')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    service_name = request.args.get('service_name')
    status_codes = request.args.get('status_codes')
    limit = int(request.args.get('limit', 1000))

    # Parse datetime parameters
    if start_time:
        start_time = datetime.fromisoformat(start_time)
    if end_time:
        end_time = datetime.fromisoformat(end_time)

    # Parse status codes
    if status_codes:
        status_codes = [int(code) for code in status_codes.split(',')]

    # Get filtered logs
    entries = log_manager.get_logs(
        log_type=log_type,
        start_time=start_time,
        end_time=end_time,
        service_name=service_name,
        status_codes=status_codes,
        limit=limit
    )

    # Convert to dict for JSON serialization
    logs = [
        {
            'timestamp': entry.timestamp.isoformat(),
            'ip_address': entry.ip_address,
            'method': entry.method,
            'path': entry.path,
            'status_code': entry.status_code,
            'body_bytes': entry.body_bytes,
            'referer': entry.referer,
            'user_agent': entry.user_agent,
            'response_time': entry.response_time,
            'proxy_service': entry.proxy_service
        }
        for entry in entries
    ]

    return jsonify(logs)

@logs_bp.route('/logs/export')
@log_route_error()
def export_logs():
    """
    Export logs in the specified format.

    Query Parameters:
        format: Export format ('json' or 'csv')

    Returns:
        File download response
    """
    format = request.args.get('format', 'json')

    # Get logs using same filtering as get_logs
    entries = log_manager.get_logs(
        log_type=request.args.get('log_type', 'nginx'),
        start_time=request.args.get('start_time'),
        end_time=request.args.get('end_time'),
        service_name=request.args.get('service_name'),
        status_codes=request.args.get('status_codes'),
        limit=int(request.args.get('limit', 1000))
    )

    # Export logs in requested format
    content = log_manager.export_logs(entries, format)

    # Prepare response
    filename = f"logs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
    mimetype = 'application/json' if format == 'json' else 'text/csv'

    return Response(
        content,
        mimetype=mimetype,
        headers={
            'Content-Disposition': f'attachment; filename={filename}'
        }
    )

@logs_bp.route('/logs/statistics')
@log_route_error()
def get_statistics():
    """Get statistics for the current log entries."""
    entries = log_manager.get_logs(
        log_type=request.args.get('log_type', 'nginx'),
        start_time=request.args.get('start_time'),
        end_time=request.args.get('end_time'),
        service_name=request.args.get('service_name'),
        status_codes=request.args.get('status_codes'),
        limit=int(request.args.get('limit', 1000))
    )

    stats = log_manager.get_log_statistics(entries)
    return jsonify(stats)
