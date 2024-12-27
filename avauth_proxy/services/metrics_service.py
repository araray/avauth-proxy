from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Optional
from dataclasses import dataclass
import json
from sqlalchemy import func
from avauth_proxy.models import Proxy, ProxyMetrics

@dataclass
class MetricsSummary:
    """Data class representing summarized metrics for a proxy service."""
    total_requests: int
    total_bytes_in: int
    total_bytes_out: int
    avg_response_time: float
    error_rate: float
    success_rate: float
    timeframe: str
    start_time: datetime
    end_time: datetime

class MetricsService:
    """
    Service for collecting, analyzing, and visualizing proxy metrics.

    This service provides:
    - Real-time metrics collection
    - Historical data analysis
    - Trend detection
    - Health status evaluation
    - Data aggregation for visualization
    """

    def __init__(self, session):
        """
        Initialize the metrics service.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session

    def get_proxy_metrics(
        self,
        proxy_id: int,
        timeframe: str = '1h',
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> MetricsSummary:
        """
        Get metrics summary for a specific proxy within a time range.

        Args:
            proxy_id: ID of the proxy service
            timeframe: Time range shorthand ('1h', '24h', '7d', '30d')
            start_time: Custom start time (overrides timeframe)
            end_time: Custom end time (overrides timeframe)

        Returns:
            MetricsSummary object containing aggregated metrics
        """
        # Calculate time range if not explicitly provided
        if not (start_time and end_time):
            end_time = datetime.utcnow()
            if timeframe.endswith('h'):
                hours = int(timeframe[:-1])
                start_time = end_time - timedelta(hours=hours)
            elif timeframe.endswith('d'):
                days = int(timeframe[:-1])
                start_time = end_time - timedelta(days=days)
            else:
                raise ValueError(f"Invalid timeframe format: {timeframe}")

        # Query metrics within time range
        metrics = self.session.query(ProxyMetrics).filter(
            ProxyMetrics.proxy_id == proxy_id,
            ProxyMetrics.timestamp.between(start_time, end_time)
        ).all()

        if not metrics:
            return MetricsSummary(
                total_requests=0,
                total_bytes_in=0,
                total_bytes_out=0,
                avg_response_time=0.0,
                error_rate=0.0,
                success_rate=100.0,
                timeframe=timeframe,
                start_time=start_time,
                end_time=end_time
            )

        # Calculate summary statistics
        total_requests = len(metrics)
        total_bytes_in = sum(m.incoming_bytes for m in metrics)
        total_bytes_out = sum(m.outgoing_bytes for m in metrics)
        avg_response_time = (
            sum(m.response_time_ms for m in metrics) / total_requests
            if total_requests > 0 else 0
        )

        error_count = sum(1 for m in metrics if m.error_count > 0)
        error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0
        success_rate = 100 - error_rate

        return MetricsSummary(
            total_requests=total_requests,
            total_bytes_in=total_bytes_in,
            total_bytes_out=total_bytes_out,
            avg_response_time=avg_response_time,
            error_rate=error_rate,
            success_rate=success_rate,
            timeframe=timeframe,
            start_time=start_time,
            end_time=end_time
        )

    def get_time_series_data(
        self,
        proxy_id: int,
        metric: str,
        interval: str = '5m',
        timeframe: str = '1h'
    ) -> List[Dict]:
        """
        Get time series data for a specific metric.

        Args:
            proxy_id: ID of the proxy service
            metric: Metric to retrieve (requests, bytes, response_time, errors)
            interval: Aggregation interval ('1m', '5m', '1h')
            timeframe: Time range to query

        Returns:
            List of data points for time series visualization
        """
        end_time = datetime.utcnow()
        if timeframe.endswith('h'):
            start_time = end_time - timedelta(hours=int(timeframe[:-1]))
        elif timeframe.endswith('d'):
            start_time = end_time - timedelta(days=int(timeframe[:-1]))
        else:
            raise ValueError(f"Invalid timeframe: {timeframe}")

        # Determine the interval in minutes
        if interval.endswith('m'):
            interval_minutes = int(interval[:-1])
        elif interval.endswith('h'):
            interval_minutes = int(interval[:-1]) * 60
        else:
            raise ValueError(f"Invalid interval: {interval}")

        # Generate time slots
        time_slots = []
        current = start_time
        while current <= end_time:
            time_slots.append({
                'start': current,
                'end': current + timedelta(minutes=interval_minutes)
            })
            current += timedelta(minutes=interval_minutes)

        # Query metrics for each time slot
        series_data = []
        for slot in time_slots:
            metrics = self.session.query(ProxyMetrics).filter(
                ProxyMetrics.proxy_id == proxy_id,
                ProxyMetrics.timestamp.between(slot['start'], slot['end'])
            ).all()

            if metric == 'requests':
                value = len(metrics)
            elif metric == 'bytes_in':
                value = sum(m.incoming_bytes for m in metrics)
            elif metric == 'bytes_out':
                value = sum(m.outgoing_bytes for m in metrics)
            elif metric == 'response_time':
                value = (
                    sum(m.response_time_ms for m in metrics) / len(metrics)
                    if metrics else 0
                )
            elif metric == 'errors':
                value = sum(m.error_count for m in metrics)
            else:
                raise ValueError(f"Invalid metric: {metric}")

            series_data.append({
                'timestamp': slot['start'].isoformat(),
                'value': value
            })

        return series_data

    def get_health_score(
        self,
        proxy_id: int,
        timeframe: str = '5m'
    ) -> float:
        """
        Calculate a health score for a proxy service.

        The health score is based on:
        - Error rate
        - Average response time
        - Request success rate
        - Recent availability

        Args:
            proxy_id: ID of the proxy service
            timeframe: Time window for calculation

        Returns:
            Float between 0 and 100 indicating health
        """
        metrics = self.get_proxy_metrics(proxy_id, timeframe)

        # Weight factors for different components
        weights = {
            'success_rate': 0.4,
            'response_time': 0.3,
            'error_rate': 0.3
        }

        # Calculate response time score (lower is better)
        max_acceptable_time = 1000  # 1 second
        response_time_score = max(
            0,
            100 * (1 - metrics.avg_response_time / max_acceptable_time)
        )

        # Calculate final weighted score
        health_score = (
            weights['success_rate'] * metrics.success_rate +
            weights['response_time'] * response_time_score +
            weights['error_rate'] * (100 - metrics.error_rate)
        )

        return min(100, max(0, health_score))

    def get_proxy_insights(
        self,
        proxy_id: int,
        timeframe: str = '24h'
    ) -> Dict:
        """
        Generate insights about proxy performance and patterns.

        Analyzes:
        - Traffic patterns
        - Error clusters
        - Performance trends
        - Usage patterns

        Args:
            proxy_id: ID of the proxy service
            timeframe: Analysis time window

        Returns:
            Dictionary containing various insights
        """
        # Get metrics for analysis
        metrics = self.get_proxy_metrics(proxy_id, timeframe)
        hourly_data = self.get_time_series_data(
            proxy_id, 'requests', '1h', timeframe
        )

        # Analyze traffic patterns
        hourly_requests = [point['value'] for point in hourly_data]
        avg_requests = sum(hourly_requests) / len(hourly_requests) if hourly_requests else 0
        peak_requests = max(hourly_requests) if hourly_requests else 0

        # Detect trends
        if len(hourly_requests) > 1:
            trend = 'increasing' if hourly_requests[-1] > hourly_requests[0] else 'decreasing'
        else:
            trend = 'stable'

        return {
            'summary': {
                'total_requests': metrics.total_requests,
                'avg_hourly_requests': avg_requests,
                'peak_requests': peak_requests,
                'total_data_transferred': metrics.total_bytes_in + metrics.total_bytes_out,
                'error_rate': metrics.error_rate
            },
            'patterns': {
                'traffic_trend': trend,
                'peak_hours': self._find_peak_hours(hourly_data),
                'quiet_hours': self._find_quiet_hours(hourly_data)
            },
            'performance': {
                'health_score': self.get_health_score(proxy_id),
                'avg_response_time': metrics.avg_response_time,
                'success_rate': metrics.success_rate
            },
            'recommendations': self._generate_recommendations(metrics)
        }

    def _find_peak_hours(self, hourly_data: List[Dict]) -> List[int]:
        """Find hours with highest traffic."""
        if not hourly_data:
            return []

        # Calculate average and standard deviation
        values = [point['value'] for point in hourly_data]
        avg = sum(values) / len(values)
        std_dev = (
            sum((x - avg) ** 2 for x in values) / len(values)
        ) ** 0.5

        # Find hours where traffic is more than 1 std dev above average
        peak_hours = []
        for point in hourly_data:
            hour = datetime.fromisoformat(point['timestamp']).hour
            if point['value'] > (avg + std_dev):
                peak_hours.append(hour)

        return sorted(set(peak_hours))

    def _find_quiet_hours(self, hourly_data: List[Dict]) -> List[int]:
        """Find hours with lowest traffic."""
        if not hourly_data:
            return []

        # Similar to peak hours but looking for low traffic
        values = [point['value'] for point in hourly_data]
        avg = sum(values) / len(values)
        std_dev = (
            sum((x - avg) ** 2 for x in values) / len(values)
        ) ** 0.5

        quiet_hours = []
        for point in hourly_data:
            hour = datetime.fromisoformat(point['timestamp']).hour
            if point['value'] < (avg - std_dev):
                quiet_hours.append(hour)

        return sorted(set(quiet_hours))

    def _generate_recommendations(self, metrics: MetricsSummary) -> List[str]:
        """Generate actionable recommendations based on metrics."""
        recommendations = []

        # Performance recommendations
        if metrics.avg_response_time > 500:  # More than 500ms
            recommendations.append(
                "Consider optimizing proxy configuration for better response times"
            )

        # Error rate recommendations
        if metrics.error_rate > 5:  # More than 5% errors
            recommendations.append(
                "Investigate error patterns and implement error handling improvements"
            )

        # Traffic recommendations
        bytes_per_request = (
            (metrics.total_bytes_in + metrics.total_bytes_out) /
            metrics.total_requests if metrics.total_requests > 0 else 0
        )
        if bytes_per_request > 1000000:  # More than 1MB per request
            recommendations.append(
                "Consider implementing response compression to reduce data transfer"
            )

        return recommendations
