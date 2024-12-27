import os
import re
import json
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class LogEntry:
    """Represents a parsed log entry with structured data."""
    timestamp: datetime
    ip_address: str
    method: str
    path: str
    status_code: int
    body_bytes: int
    referer: Optional[str]
    user_agent: Optional[str]
    response_time: float
    proxy_service: Optional[str]

class LogManager:
    """
    Manages log collection, parsing, and analysis for both Nginx and application logs.

    This service provides capabilities to:
    - Parse Nginx access logs
    - Parse application logs
    - Filter and search logs
    - Export logs in various formats
    - Generate log statistics
    """

    NGINX_LOG_PATTERN = re.compile(
        r'(?P<ip>[\d.]+)\s+-\s+-\s+\[(?P<timestamp>[\w:/]+\s[+\-]\d{4})\]\s+'
        r'"(?P<method>\w+)\s+(?P<path>[^\s]*)\s+\w+/[\d.]+"\s+'
        r'(?P<status>\d{3})\s+(?P<bytes>\d+)\s+'
        r'"(?P<referer>[^"]*)"\s+"(?P<user_agent>[^"]*)"'
    )

    def __init__(self, nginx_log_path: str, app_log_path: str):
        """
        Initialize the log manager with paths to log files.

        Args:
            nginx_log_path: Path to Nginx access log
            app_log_path: Path to application log
        """
        self.nginx_log_path = nginx_log_path
        self.app_log_path = app_log_path

    def parse_nginx_log_line(self, line: str) -> Optional[LogEntry]:
        """
        Parse a single line from Nginx access log into structured data.

        Args:
            line: Raw log line from Nginx access log

        Returns:
            LogEntry if parsing successful, None otherwise
        """
        match = self.NGINX_LOG_PATTERN.match(line)
        if not match:
            return None

        data = match.groupdict()
        try:
            timestamp = datetime.strptime(
                data['timestamp'],
                '%d/%b/%Y:%H:%M:%S %z'
            )

            # Extract proxy service from path if available
            proxy_service = None
            path_parts = data['path'].split('/')
            if len(path_parts) > 1 and path_parts[1] in ['proxy', 'auth', 'metrics']:
                proxy_service = path_parts[1]

            return LogEntry(
                timestamp=timestamp,
                ip_address=data['ip'],
                method=data['method'],
                path=data['path'],
                status_code=int(data['status']),
                body_bytes=int(data['bytes']),
                referer=data['referer'] if data['referer'] != '-' else None,
                user_agent=data['user_agent'],
                response_time=0.0,  # Not available in basic Nginx format
                proxy_service=proxy_service
            )
        except (ValueError, KeyError):
            return None

    def get_logs(self,
                 log_type: str = 'nginx',
                 start_time: Optional[datetime] = None,
                 end_time: Optional[datetime] = None,
                 service_name: Optional[str] = None,
                 status_codes: Optional[List[int]] = None,
                 limit: int = 1000) -> List[LogEntry]:
        """
        Retrieve and filter logs based on criteria.

        Args:
            log_type: Type of logs to retrieve ('nginx' or 'app')
            start_time: Filter logs after this time
            end_time: Filter logs before this time
            service_name: Filter logs for specific proxy service
            status_codes: Filter logs for specific status codes
            limit: Maximum number of log entries to return

        Returns:
            List of filtered LogEntry objects
        """
        log_path = self.nginx_log_path if log_type == 'nginx' else self.app_log_path
        entries = []

        if not os.path.exists(log_path):
            return entries

        with open(log_path, 'r') as f:
            for line in f:
                if log_type == 'nginx':
                    entry = self.parse_nginx_log_line(line)
                else:
                    try:
                        data = json.loads(line)
                        entry = self.parse_app_log_line(data)
                    except json.JSONDecodeError:
                        continue

                if not entry:
                    continue

                # Apply filters
                if start_time and entry.timestamp < start_time:
                    continue
                if end_time and entry.timestamp > end_time:
                    continue
                if service_name and entry.proxy_service != service_name:
                    continue
                if status_codes and entry.status_code not in status_codes:
                    continue

                entries.append(entry)
                if len(entries) >= limit:
                    break

        return entries

    def export_logs(self, entries: List[LogEntry], format: str = 'json') -> str:
        """
        Export log entries in the specified format.

        Args:
            entries: List of LogEntry objects to export
            format: Export format ('json' or 'csv')

        Returns:
            String containing formatted log data
        """
        if format == 'json':
            return json.dumps([
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
            ], indent=2)
        elif format == 'csv':
            import csv
            from io import StringIO

            output = StringIO()
            writer = csv.writer(output)

            # Write header
            writer.writerow([
                'Timestamp', 'IP Address', 'Method', 'Path',
                'Status Code', 'Body Bytes', 'Referer',
                'User Agent', 'Response Time', 'Proxy Service'
            ])

            # Write data rows
            for entry in entries:
                writer.writerow([
                    entry.timestamp.isoformat(),
                    entry.ip_address,
                    entry.method,
                    entry.path,
                    entry.status_code,
                    entry.body_bytes,
                    entry.referer or '',
                    entry.user_agent or '',
                    entry.response_time,
                    entry.proxy_service or ''
                ])

            return output.getvalue()
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def get_log_statistics(self, entries: List[LogEntry]) -> Dict:
        """
        Generate statistics from log entries.

        Args:
            entries: List of LogEntry objects to analyze

        Returns:
            Dictionary containing log statistics
        """
        stats = {
            'total_requests': len(entries),
            'status_codes': {},
            'methods': {},
            'proxy_services': {},
            'total_bytes': 0,
            'avg_response_time': 0.0
        }

        if not entries:
            return stats

        # Calculate statistics
        for entry in entries:
            # Count status codes
            stats['status_codes'][entry.status_code] = \
                stats['status_codes'].get(entry.status_code, 0) + 1

            # Count HTTP methods
            stats['methods'][entry.method] = \
                stats['methods'].get(entry.method, 0) + 1

            # Count proxy services
            if entry.proxy_service:
                stats['proxy_services'][entry.proxy_service] = \
                    stats['proxy_services'].get(entry.proxy_service, 0) + 1

            # Sum bytes
            stats['total_bytes'] += entry.body_bytes

            # Sum response times
            stats['avg_response_time'] += entry.response_time

        # Calculate average response time
        stats['avg_response_time'] /= len(entries)

        return stats
