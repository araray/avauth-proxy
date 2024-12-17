import logging
from pythonjsonlogger.json import JsonFormatter
from avauth_proxy.config import Config
import os
import uuid
import datetime

def configure_logging():
    os.makedirs(os.path.dirname(Config.EVENTS_LOG_FILE), exist_ok=True)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    log_handler = logging.FileHandler(Config.EVENTS_LOG_FILE)
    formatter = JsonFormatter()
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)

def log_event(description, code):
    event_id = str(uuid.uuid4())
    timestamp = datetime.datetime.now().isoformat()
    logging.info({"event_id": event_id, "timestamp": timestamp, "description": description, "code": code})
