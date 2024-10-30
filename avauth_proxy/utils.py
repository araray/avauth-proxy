# avauth_proxy/utils.py

import os
import uuid
import datetime
import tomllib
import tomli_w as tomlw
from jinja2 import Environment, FileSystemLoader
from .config import Config

def load_oauth_providers(oauth):
    with open(Config.CONFIG_TOML_FILE, 'rb') as f:
        config_data = tomllib.load(f)
    providers_config = config_data.get('oauth_providers', [])
    oauth_providers = {}
    for provider in providers_config:
        oauth.register(
            name=provider['name'],
            client_id=provider['client_id'],
            client_secret=provider['client_secret'],
            access_token_url=provider['access_token_url'],
            authorize_url=provider['authorize_url'],
            api_base_url=provider['api_base_url'],
            client_kwargs=provider.get('client_kwargs', {})
        )
        oauth_providers[provider['name']] = provider
    return oauth_providers

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

def load_proxies():
    if os.path.exists(Config.PROXIES_CONFIG_FILE):
        with open(Config.PROXIES_CONFIG_FILE, 'rb') as f:
            data = tomllib.load(f)
            return data.get('proxies', [])
    else:
        with open(Config.PROXIES_CONFIG_FILE, 'wb') as f:
            tomlw.dump({'proxies': []}, f)
        return []

def save_proxies(proxies):
    with open(Config.PROXIES_CONFIG_FILE, 'wb') as f:
        tomlw.dump({'proxies': proxies}, f)

def generate_nginx_configs(proxies):
    nginx_templates_dir = Config.NGINX_TEMPLATES_DIR
    nginx_config_dir = Config.NGINX_CONFIG_DIR

    env = Environment(loader=FileSystemLoader(nginx_templates_dir))

    for proxy in proxies:
        template_name = proxy.get('template', 'default.conf.j2')
        template = env.get_template(template_name)

        config_content = template.render(
            service_name=proxy['service_name'],
            url=proxy['url'],
            port=proxy['port'],
            custom_directives=proxy.get('custom_directives', '')
        )

        os.makedirs(nginx_config_dir, exist_ok=True)
        config_path = os.path.join(nginx_config_dir, f"{proxy['service_name']}.conf")

        with open(config_path, 'w') as f:
            f.write(config_content)

    os.system('nginx -s reload')

def get_available_templates():
    nginx_templates_dir = Config.NGINX_TEMPLATES_DIR
    templates = [
        filename for filename in os.listdir(nginx_templates_dir)
        if filename.endswith('.j2')
    ]
    return templates
