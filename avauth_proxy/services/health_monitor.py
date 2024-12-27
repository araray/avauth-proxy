# avauth_proxy/services/health_monitor.py

import asyncio
import aiohttp
import json
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from avauth_proxy.models import Proxy, ProxyMetrics
from avauth_proxy.utils.logging_utils import log_event

class HealthMonitor:
    """
    Service for monitoring proxy health status and collecting metrics.

    This service performs periodic health checks on all registered proxies,
    updates their status, and collects performance metrics. It uses
    asynchronous I/O to efficiently handle multiple proxies simultaneously.
    """

    def __init__(self, db_url='sqlite:///database.db', check_interval=60):
        """
        Initialize the health monitor service.

        Args:
            db_url (str): Database connection URL
            check_interval (int): Time between health checks in seconds
        """
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        self.check_interval = check_interval
        self.running = False

    async def check_proxy_health(self, proxy):
        """
        Check the health of a single proxy by making a request to its
        health check endpoint and validating the response.

        Args:
            proxy (Proxy): Proxy instance to check

        Returns:
            tuple: (status, response_time_ms)
        """
        start_time = datetime.utcnow()

        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://{proxy.url}:{proxy.port}{proxy.health_check_endpoint}"

                async with session.get(url, timeout=5) as response:
                    end_time = datetime.utcnow()
                    response_time = (end_time - start_time).total_seconds() * 1000

                    # Check status code
                    if response.status != proxy.expected_status:
                        return 'error', response_time

                    # If expecting specific JSON response
                    if proxy.expected_response:
                        try:
                            data = await response.json()
                            expected = json.loads(proxy.expected_response)

                            # Compare response with expected structure
                            if not self._validate_response(data, expected):
                                return 'warning', response_time

                        except (json.JSONDecodeError, ValueError):
                            return 'error', response_time

                    return 'ok', response_time

        except asyncio.TimeoutError:
            return 'warning', None
        except Exception as e:
            log_event(f"Health check error for {proxy.service_name}: {str(e)}", 'health_check_error')
            return 'error', None

    def _validate_response(self, actual, expected):
        """
        Recursively validate that the actual response matches the expected structure.

        Args:
            actual (dict): Actual response from the health check
            expected (dict): Expected response structure

        Returns:
            bool: True if response matches expected structure
        """
        if isinstance(expected, dict):
            if not isinstance(actual, dict):
                return False
            return all(
                k in actual and self._validate_response(actual[k], v)
                for k, v in expected.items()
            )
        elif isinstance(expected, list):
            if not isinstance(actual, list):
                return False
            return len(actual) > 0  # Just verify it's not empty
        else:
            return isinstance(actual, type(expected))

    async def collect_metrics(self, proxy):
        """
        Collect performance metrics for a proxy.

        Args:
            proxy (Proxy): Proxy to collect metrics for
        """
        session = self.Session()
        try:
            # Create new metrics record
            metrics = ProxyMetrics(
                proxy_id=proxy.id,
                timestamp=datetime.utcnow()
            )
            session.add(metrics)
            session.commit()

        except Exception as e:
            session.rollback()
            log_event(f"Error collecting metrics for {proxy.service_name}: {str(e)}", 'metrics_error')
        finally:
            session.close()

    async def monitor_loop(self):
        """
        Main monitoring loop that periodically checks all proxies.
        """
        while self.running:
            session = self.Session()
            try:
                proxies = session.query(Proxy).all()

                # Check each proxy concurrently
                tasks = []
                for proxy in proxies:
                    if proxy.health_check_endpoint:  # Only check if endpoint is configured
                        tasks.append(self.check_proxy_health(proxy))

                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Update proxy statuses and collect metrics
                for proxy, (status, response_time) in zip(proxies, results):
                    proxy.health_status = status
                    proxy.last_checked = datetime.utcnow()

                    if response_time is not None:
                        await self.collect_metrics(proxy)

                session.commit()

            except Exception as e:
                session.rollback()
                log_event(f"Error in monitor loop: {str(e)}", 'monitor_error')
            finally:
                session.close()

            await asyncio.sleep(self.check_interval)

    async def start(self):
        """Start the health monitoring service."""
        self.running = True
        await self.monitor_loop()

    async def stop(self):
        """Stop the health monitoring service."""
        self.running = False
