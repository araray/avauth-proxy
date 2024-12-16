import logging
from pythonjsonlogger.json import JsonFormatter
from avauth_proxy.config import Config

def configure_logging():
    logger = logging.getLogger()
    log_handler = logging.FileHandler(Config.EVENTS_LOG_FILE)
    formatter = JsonFormatter()
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)
    logger.setLevel(logging.INFO)

def log_event(description, code):
    logging.info({"event": description, "code": code})
