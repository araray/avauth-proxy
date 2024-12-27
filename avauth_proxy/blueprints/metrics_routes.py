from flask import Blueprint, render_template, jsonify, request
from sqlalchemy.orm import Session
from avauth_proxy.services.metrics_service import MetricsService
from avauth_proxy.utils.decorator_utils import admin_required, require_proxy_access
from datetime import datetime, timedelta

metrics_bp = Blueprint('metrics', __name__)

def get_metrics_service():
    """
    Creates a MetricsService instance with a new database session.

    This helper ensures proper session management for each request.

    Returns:
        tuple: (MetricsService instance, database session)
    """
    session = Session()
    return MetricsService(session), session

@metrics_bp.route('/metrics/dashboard')
@admin_required
def metrics_dashboard():
    """
    Display the main metrics dashboard showing system-wide statistics
    and overview of all proxies.

    The dashboard provides:
    - System-wide metrics overview
    - Health status summary
    - Recent activity graphs
    - Quick insights and recommendations
    """
    service, session = get_metrics_service()
    try:
        # Get all proxies for the dashboard
        proxies = session.query(Proxy).all()

        # Collect metrics summaries for each proxy
        proxy_metrics = {}
        for proxy in proxies:
            proxy_metrics[proxy.id] = {
                'summary': service.get_proxy_metrics(proxy.id, '24h'),
                'health_score': service.get_health_score(proxy.id),
                'insights': service.get_proxy_insights(proxy.id)
            }

        return render_template(
            'metrics/dashboard.html',
            proxies=proxies,
            proxy_metrics=proxy_metrics
        )
    finally:
        session.close()

@metrics_bp.route('/metrics/proxy/<int:proxy_id>')
@require_proxy_access('read')
def proxy_metrics(proxy_id):
    """
    Display detailed metrics for a specific proxy service.

    Shows:
    - Detailed traffic analysis
    - Response time graphs
    - Error rate tracking
    - Resource usage statistics
    - Historical trends
    """
    service, session = get_metrics_service()
    try:
        proxy = session.query(Proxy).get(proxy_id)
        if not proxy:
            return jsonify({'error': 'Proxy not found'}), 404

        timeframe = request.args.get('timeframe', '24h')
        metrics = service.get_proxy_metrics(proxy_id, timeframe)
        insights = service.get_proxy_insights(proxy_id)

        return render_template(
            'metrics/proxy_detail.html',
            proxy=proxy,
            metrics=metrics,
            insights=insights,
            timeframe=timeframe
        )
    finally:
        session.close()

@metrics_bp.route('/metrics/proxy/<int:proxy_id>/data')
@require_proxy_access('read')
def proxy_metrics_data(proxy_id):
    """
    API endpoint providing metrics data for visualization.

    Query Parameters:
        metric: Type of metric to retrieve
        interval: Time interval for aggregation
        timeframe: Time range to query

    Returns:
        JSON response with time series data
    """
    service, session = get_metrics_service()
    try:
        metric = request.args.get('metric', 'requests')
        interval = request.args.get('interval', '5m')
        timeframe = request.args.get('timeframe', '1h')

        data = service.get_time_series_data(
            proxy_id,
            metric,
            interval,
            timeframe
        )

        return jsonify(data)
    finally:
        session.close()

@metrics_bp.route('/metrics/health')
@admin_required
def health_dashboard():
    """
    Display the health monitoring dashboard showing status
    of all proxy services.

    Provides:
    - Real-time health status
    - Historical uptime
    - Performance indicators
    - Alert history
    """
    service, session = get_metrics_service()
    try:
        proxies = session.query(Proxy).all()
        health_data = {}

        for proxy in proxies:
            health_data[proxy.id] = {
                'health_score': service.get_health_score(proxy.id),
                'metrics': service.get_proxy_metrics(proxy.id, '5m'),
                'insights': service.get_proxy_insights(proxy.id)
            }

        return render_template(
            'metrics/health.html',
            proxies=proxies,
            health_data=health_data
        )
    finally:
        session.close()

@metrics_bp.route('/metrics/export')
@admin_required
def export_metrics():
    """
    Export metrics data in various formats.

    Query Parameters:
        format: Export format (json/csv)
        proxy_id: Optional proxy ID to filter
        timeframe: Time range to export

    Returns:
        File download response with metrics data
    """
    service, session = get_metrics_service()
    try:
        export_format = request.args.get('format', 'json')
        proxy_id = request.args.get('proxy_id', type=int)
        timeframe = request.args.get('timeframe', '24h')

        if proxy_id:
            # Export single proxy metrics
            metrics = service.get_proxy_metrics(proxy_id, timeframe)
            data = {
                'metrics': metrics,
                'insights': service.get_proxy_insights(proxy_id)
            }
        else:
            # Export all proxies
            proxies = session.query(Proxy).all()
            data = {}
            for proxy in proxies:
                data[proxy.service_name] = {
                    'metrics': service.get_proxy_metrics(proxy.id, timeframe),
                    'insights': service.get_proxy_insights(proxy.id)
                }

        if export_format == 'csv':
            # Convert to CSV format
            output = StringIO()
            writer = csv.writer(output)

            # Write headers
            if proxy_id:
                writer.writerow([
                    'Metric',
                    'Value',
                    'Unit',
                    'Timeframe'
                ])
                # Write metrics data
                for key, value in data['metrics'].__dict__.items():
                    if not key.startswith('_'):
                        writer.writerow([key, value, '', timeframe])
            else:
                writer.writerow([
                    'Proxy',
                    'Total Requests',
                    'Bytes In',
                    'Bytes Out',
                    'Avg Response Time',
                    'Error Rate',
                    'Health Score'
                ])
                for proxy_name, proxy_data in data.items():
                    metrics = proxy_data['metrics']
                    writer.writerow([
                        proxy_name,
                        metrics.total_requests,
                        metrics.total_bytes_in,
                        metrics.total_bytes_out,
                        f"{metrics.avg_response_time:.2f}ms",
                        f"{metrics.error_rate:.2f}%",
                        f"{proxy_data['insights']['performance']['health_score']:.1f}"
                    ])

            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={
                    'Content-Disposition': f'attachment; filename=metrics_{timeframe}.csv'
                }
            )
        else:
            return jsonify(data)

    finally:
        session.close()
