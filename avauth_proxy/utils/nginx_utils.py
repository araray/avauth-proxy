import os
from jinja2 import Environment, FileSystemLoader
from avauth_proxy.config import Config

def generate_nginx_configs(proxies):
    env = Environment(loader=FileSystemLoader(Config.NGINX_TEMPLATES_DIR))
    for proxy in proxies:
        template = env.get_template(proxy["template"])
        config_content = template.render(**proxy)
        config_path = os.path.join(Config.NGINX_CONFIG_DIR, f"{proxy['service_name']}.conf")
        with open(config_path, "w") as f:
            f.write(config_content)
    os.system("nginx -s reload")
