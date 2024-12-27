import os
import requests

from datetime import datetime

from flask import Blueprint, jsonify
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from avauth_proxy.models import Proxy

engine = create_engine('sqlite:///database.db')
DBSession = sessionmaker(bind=engine)
session = DBSession()

metrics_bp = Blueprint("metrics", __name__)

@metrics_bp.route('/metrics/healthcheck', methods=['POST'])
def run_health_checks():
    proxies = session.query(Proxy).all()
    for proxy in proxies:
        try:
            response = requests.get(f"http://{proxy.url}:{proxy.port}/health", timeout=5)
            proxy.health_status = 'ok' if response.status_code == 200 else 'warning'
        except requests.RequestException:
            proxy.health_status = 'error'
        proxy.last_checked = datetime.utcnow()
    session.commit()
    return jsonify({"message": "Health checks updated"}), 200

@metrics_bp.route('/logs/<string:log_type>', methods=['GET'])
def fetch_logs(log_type):
    log_files = {
        "nginx": "/var/log/nginx/access.log",
        "app": "logs/events.log"
    }
    log_path = log_files.get(log_type)
    if not log_path or not os.path.exists(log_path):
        return jsonify({"message": "Log file not found"}), 404
    with open(log_path, "r") as log_file:
        return jsonify({"logs": log_file.readlines()})
