# avauth_proxy/services/metrics_collector.py

from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy import func, and_
from avauth_proxy.models import Proxy, ProxyMetrics

class MetricsCollector:
    """
    Service for collecting and analyzing proxy metrics.

    This service provides methods for aggregating metrics data
    and generating statistics for proxies.
    """

    def __init__(self, session):
        """
        Initialize the metrics collector.

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    def get_proxy_metrics(self, proxy_id, time_range='1h'):
        """
        Get metrics for a specific proxy within a time range.

        Args:
            proxy_id (int): ID of the proxy
            time_range (str): Time range to query (e.g., '1h', '24h', '7d')

        Returns:
            dict: Collected metrics
        """
        # Calculate time range
        end_time = datetime.utcnow()
        if time_range.endswith('h'):
            hours = int(time_range[:-1])
            start_time = end_time - timedelta(hours=hours)
        elif time_range.endswith('d'):
            days = int(time_range[:-1])
            start_time = end_time - timedelta(days=days)
        else:
            raise ValueError("Invalid time range format")

        # Query metrics within time range
        metrics = self.session.query(ProxyMetrics).filter(
            and_(
                ProxyMetrics.proxy_id == proxy_id,
                ProxyMetrics.timestamp >= start_time,
                ProxyMetrics.timestamp <= end_time
            )
        ).all()

        # Aggregate metrics
        total_incoming = sum(m.incoming_requests for m in metrics)
        total_outgoing = sum(m.outgoing_requests for m in metrics)
        total_errors = sum(m.error_count for m in metrics)
        avg_response_time = sum(m.response_time_ms for m in metrics if m.response_time_ms) / len(metrics) if metrics else 0

        return {
            'total_incoming_requests': total_incoming,
            'total_outgoing_requests': total_outgoing,
            'total_errors': total_errors,
            'average_response_time_ms': avg_response_time,
            'metrics_count': len(metrics),
            'time_range': time_range
        }

    def get_all_proxies_metrics(self, time_range='1h'):
        """
        Get metrics for all proxies.

        Args:
            time_range (str): Time range to query

        Returns:
            dict: Metrics for all proxies
        """
        proxies = self.session.query(Proxy).all()
        return {
            proxy.service_name: self.get_proxy_metrics(proxy.id, time_range)
            for proxy in proxies
        }

    def get_metrics_summary(self):
        """
        Get a summary of all metrics.

        Returns:
            dict: Summary statistics
        """
        # Get total requests and errors
        totals = self.session.query(
            func.sum(ProxyMetrics.incoming_requests).label('total_incoming'),
            func.sum(ProxyMetrics.outgoing_requests).label('total_outgoing'),
            func.sum(ProxyMetrics.error_count).label('total_errors')
        ).first()

        # Get average response time
        avg_response = self.session.query(
            func.avg(ProxyMetrics.response_time_ms)
        ).scalar()

        return {
            'total_incoming_requests': totals.total_incoming or 0,
            'total_outgoing_requests': totals.total_outgoing or 0,
            'total_errors': totals.total_errors or 0,
            'average_response_time_ms': float(avg_response) if avg_response else 0
        }
