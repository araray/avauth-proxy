from flask import Blueprint
from prometheus_client import generate_latest, Counter, Gauge

metrics_bp = Blueprint("metrics", __name__)

# Prometheus metrics
num_proxies = Gauge("num_proxies", "Number of active proxies")
auth_failures = Counter("auth_failures", "Failed authentication attempts")

@metrics_bp.route("/")
def metrics():
    """
    Prometheus scrape endpoint for metrics.
    """
    return generate_latest()
