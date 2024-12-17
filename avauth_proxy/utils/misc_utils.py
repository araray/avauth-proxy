import os
import uuid
import datetime
import tomllib
import tomli_w as tomlw
from jinja2 import Environment, FileSystemLoader
from avauth_proxy.config import Config

def log_event(description, code):
    event_id = str(uuid.uuid4())
    timestamp = datetime.datetime.now().isoformat()
    event = {
        'event_id': event_id,
        'timestamp': timestamp,
        'description': description,
        'code': code
    }
    os.makedirs(os.path.dirname(Config.EVENTS_LOG_FILE), exist_ok=True)
    with open(Config.EVENTS_LOG_FILE, 'a') as f:
        f.write(f"{event}\n")

def load_events():
    events = []
    if os.path.exists(Config.EVENTS_LOG_FILE):
        with open(Config.EVENTS_LOG_FILE, 'r') as f:
            for line in f:
                events.append(eval(line.strip()))
    return events

def get_available_templates():
    nginx_templates_dir = Config.NGINX_TEMPLATES_DIR
    templates = [
        filename for filename in os.listdir(nginx_templates_dir)
        if filename.endswith('.j2')
    ]
    return templates
